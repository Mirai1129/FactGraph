from pydantic import BaseModel, Field

# —— 請依需求擴充 —— #
class NewsIn(BaseModel):
    text: str = Field(..., min_length=20, description="新聞全文")

class NewsOut(BaseModel):
    task_id: str
    status: str = Field(..., description="'processing' | 'done' | 'error'")
