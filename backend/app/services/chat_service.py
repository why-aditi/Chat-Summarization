from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from ..database import db
from ..models.chat import ChatMessage, ChatSummary, PaginatedResponse
from .gemini_service import gemini_service

class ChatService:
    # Cache for storing recent messages
    _message_cache = {}
    _cache_size = 100

    @staticmethod
    async def create_message(message: ChatMessage) -> ChatMessage:
        db_instance = await db.get_db()
        message_dict = message.model_dump(by_alias=True, exclude_none=True)
        if '_id' in message_dict:
            del message_dict['_id']
        
        # Add to cache before DB operation
        cache_key = f"{message.conversation_id}_{datetime.now().timestamp()}"
        ChatService._message_cache[cache_key] = message_dict
        
        # Maintain cache size
        if len(ChatService._message_cache) > ChatService._cache_size:
            oldest_key = min(ChatService._message_cache.keys())
            del ChatService._message_cache[oldest_key]
        
        # Batch insert to improve performance
        result = await db_instance.messages.insert_one(message_dict)
        message.id = str(result.inserted_id)

        # Generate bot response if the message is from a user
        if message.user_id != 'bot':
            # Get conversation history
            conversation = await ChatService.get_message(message.conversation_id)
            conversation_text = '\n'.join([f"{msg.user_id}: {msg.message}" for msg in conversation])
            
            # Generate response using Gemini
            prompt = f"Please respond to this conversation as a helpful AI assistant:\n\n{conversation_text}"
            response = await gemini_service.model.generate_content_async(prompt)
            
            # Create and save bot response
            bot_message = ChatMessage(
                conversation_id=message.conversation_id,
                user_id='bot',
                message=response.text,
                timestamp=datetime.now().isoformat(),
                metadata={}
            )
            bot_dict = bot_message.model_dump(by_alias=True, exclude_none=True)
            bot_result = await db_instance.messages.insert_one(bot_dict)
            bot_message.id = str(bot_result.inserted_id)
            return bot_message
        
        return message

    @staticmethod
    async def get_message(
        conversation_id: str,
        search_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ChatMessage]:
        db_instance = await db.get_db()
        query = {'conversation_id': conversation_id}
        
        # Add text search if provided
        if search_query:
            query['message'] = {'$regex': search_query, '$options': 'i'}
        
        # Add date range filters if provided
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = start_date.isoformat()
            if end_date:
                date_query['$lte'] = end_date.isoformat()
            if date_query:
                query['timestamp'] = date_query
        
        cursor = db_instance.messages.find(query).sort('timestamp', 1)
        messages = [ChatMessage(**msg) async for msg in cursor]
        return messages

    @staticmethod
    async def get_user_messages(user_id: str, page: int = 1, limit: int = 10) -> PaginatedResponse:
        db_instance = await db.get_db()
        skip = (page - 1) * limit
        
        # Use aggregation for efficient pagination
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$sort': {'timestamp': -1}},
            {
                '$facet': {
                    'total': [{'$count': 'count'}],
                    'data': [{'$skip': skip}, {'$limit': limit}]
                }
            }
        ]
        
        result = await db_instance.messages.aggregate(pipeline).to_list(1)
        result = result[0]
        
        total = result['total'][0]['count'] if result['total'] else 0
        messages = [ChatMessage(**msg) for msg in result['data']]
        
        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            data=messages
        )

    @staticmethod
    async def delete_message(conversation_id: str) -> bool:
        db_instance = await db.get_db()
        result = await db_instance.messages.delete_many({'conversation_id': conversation_id})
        await db_instance.summaries.delete_many({'conversation_id': conversation_id})
        return result.deleted_count > 0

    @staticmethod
    async def summarize_conversation(
        conversation_id: str,
        include_sentiment: bool = False,
        include_keywords: bool = False
    ) -> ChatSummary:
        db_instance = await db.get_db()
        
        # Get messages for the conversation
        messages = await ChatService.get_message(conversation_id)
        if not messages:
            raise ValueError(f"No messages found for conversation {conversation_id}")
        
        # Generate summary
        summary = await gemini_service.generate_summary(messages)
        
        # Create summary object
        chat_summary = ChatSummary(
            _id=str(ObjectId()),
            conversation_id=conversation_id,
            summary=summary
        )
        
        # Add sentiment and keywords if requested
        if include_sentiment or include_keywords:
            sentiment, keywords = await gemini_service.analyze_sentiment_and_keywords(messages)
            if include_sentiment:
                chat_summary.sentiment = sentiment
            if include_keywords:
                chat_summary.keywords = keywords
        
        # Store summary in database
        summary_dict = chat_summary.model_dump(by_alias=True, exclude_none=True)
        result = await db_instance.summaries.insert_one(summary_dict)
        chat_summary.id = str(result.inserted_id)
        
        return chat_summary

chat_service = ChatService()