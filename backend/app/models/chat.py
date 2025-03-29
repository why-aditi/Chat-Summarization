from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _):
        if not isinstance(v, (ObjectId, str)):
            raise ValueError('Invalid ObjectId')
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {'type': 'string'}

class ChatMessage(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias='_id')
    conversation_id: str
    user_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        allow_population_by_field_name = True

class ChatSummary(BaseModel):
    id: Optional[PyObjectId] = Field(alias='_id')
    conversation_id: str
    summary: str
    sentiment: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[ChatMessage]

class ChatSummarizeRequest(BaseModel):
    conversation_id: str
    include_sentiment: bool = False
    include_keywords: bool = False