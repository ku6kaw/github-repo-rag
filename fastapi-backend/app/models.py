from pydantic import BaseModel, HttpUrl

class IngestRequest(BaseModel):
    """
    リポジトリ取り込みAPIのリクエストボディ
    """
    repo_url: HttpUrl # pydantic が URL として妥当か検証してくれる

class IngestResponse(BaseModel):
    """
    リポジトリ取り込みAPIのレスポンス
    """
    repo_id: str
    status: str
    message: str

class ChatRequest(BaseModel):
    """
    チャットAPIのリクエストボディ
    """
    repo_id: str
    query: str

class ChatResponse(BaseModel):
    """
    チャットAPIのレスポンス
    """
    answer: str