from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# .env ファイルをロード (OpenAI APIキーのため)
load_dotenv(dotenv_path=".env")

# 内部モジュール（PydanticモデルとRAGロジック）をインポート
from app.models import IngestRequest, IngestResponse, ChatRequest, ChatResponse
import app.rag_service as rag_service

app = FastAPI()

# --- CORS (Cross-Origin Resource Sharing) の設定 ---
# Next.js (ローカルの 3000番ポート) からのアクセスを許可する
origins = [
    "http://localhost:3000",
    # (デプロイ後、VercelのURLなどもここに追加する)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # すべてのメソッド (GET, POSTなど) を許可
    allow_headers=["*"], # すべてのヘッダーを許可
)

# --- API エンドポイント ---

@app.get("/")
def read_root():
    return {"message": "RAG API is running"}

@app.post("/ingest", response_model=IngestResponse)
async def api_ingest(request: IngestRequest):
    """
    GitHubリポジトリを取り込むエンドポイント
    """
    try:
        repo_id = rag_service.ingest_repo(str(request.repo_url))
        return IngestResponse(
            repo_id=repo_id,
            status="success",
            message=f"Repository {repo_id} ingested successfully."
        )
    except ValueError as e:
        # URLが不正などの場合
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # クローン失敗やインデックス構築失敗など
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )

@app.post("/chat", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    """
    リポジトリに対してチャット（クエリ）を実行するエンドポイント
    """
    try:
        answer = rag_service.query_repo(request.repo_id, request.query)
        return ChatResponse(answer=answer)
    except Exception as e:
        # コレクションが見つからない、LLMエラーなど
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during query: {e}"
        )

if __name__ == "__main__":
    # このファイルが直接実行された場合 (デバッグ用)
    uvicorn.run(app, host="0.0.0.0", port=8000)