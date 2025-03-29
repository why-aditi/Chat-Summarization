import google.generativeai as genai
from typing import List, Tuple
from ..config import settings
from ..models.chat import ChatMessage

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def generate_summary(self, messages: List[ChatMessage]) -> str:
        conversation = '\n'.join([f"{msg.user_id}: {msg.message}" for msg in messages])
        prompt = f"Please provide a concise summary of the following conversation:\n\n{conversation}"
        
        response = await self.model.generate_content_async(prompt)
        return response.text

    async def analyze_sentiment_and_keywords(self, messages: List[ChatMessage]) -> Tuple[str, List[str]]:
        conversation = '\n'.join([f"{msg.user_id}: {msg.message}" for msg in messages])
        prompt = (
            "Analyze the following conversation and provide:\n"
            "1. Overall sentiment (positive, negative, or neutral)\n"
            "2. Key topics or keywords (comma-separated)\n\n"
            f"{conversation}"
        )
        
        response = await self.model.generate_content_async(prompt)
        result = response.text.split('\n')
        
        sentiment = 'neutral'
        keywords = []
        
        for line in result:
            if 'sentiment' in line.lower():
                if 'positive' in line.lower():
                    sentiment = 'positive'
                elif 'negative' in line.lower():
                    sentiment = 'negative'
            elif 'key' in line.lower() and ':' in line:
                keywords = [k.strip() for k in line.split(':', 1)[1].split(',')]
        
        return sentiment, keywords

gemini_service = GeminiService()