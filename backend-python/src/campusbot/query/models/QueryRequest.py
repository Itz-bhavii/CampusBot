from pydantic import BaseModel,Field
from typing import List
class QueryRequest(BaseModel):
    question : str
    chatHistory : List[str] = Field(default_factory=list)