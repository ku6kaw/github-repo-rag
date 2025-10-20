import os
import shutil
from dotenv import load_dotenv
from git import Repo
from urllib.parse import urlparse

# LlamaIndex / Qdrant
import qdrant_client
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import CodeSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv(dotenv_path=".env")

# --- 定数 ---
# QDRANT_HOST = "localhost"
# QDRANT_PORT = 6333
REPO_BASE_PATH = "./temp_repos" # クローンしたリポジトリを保存するベース

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# --- LlamaIndexのグローバル設定 ---
print("LlamaIndexのグローバル設定を初期化中...")
Settings.llm = OpenAI(model="gpt-4o")
Settings.embedding = OpenAIEmbedding(
    model="text-embedding-3-small",
    embed_batch_size=10
)
print("LlamaIndexのグローバル設定完了。")

def _get_qdrant_client():
    """Qdrantクライアントを初期化するヘルパー関数"""
    if QDRANT_URL and QDRANT_API_KEY:
        # ★ クラウド接続
        print(f"Qdrant Cloudに接続中: {QDRANT_URL}")
        return qdrant_client.QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            port=6333 # gRPCポート
        )
    else:
        # ★ ローカル接続 (フォールバック)
        print("Qdrant (ローカル) に接続中: localhost:6333")
        return qdrant_client.QdrantClient(host="localhost", port=6333)

def _get_repo_id_from_url(repo_url: str) -> str:
    """
    GitHub URLから "ユーザー名-リポジトリ名" 形式のIDを生成する
    例: "https://github.com/tiangolo/fastapi" -> "tiangolo-fastapi"
    """
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) >= 2:
        # ".git" 拡張子を削除
        repo_name = path_parts[1].removesuffix('.git')
        return f"{path_parts[0]}-{repo_name}"
    else:
        raise ValueError("無効なリポジトリURLです")

def ingest_repo(repo_url: str) -> str:
    """
    指定されたURLのリポジトリを取り込み、インデックスを構築する。
    成功した場合、repo_id を返す。
    """
    try:
        repo_id = _get_repo_id_from_url(repo_url)
        repo_path = os.path.join(REPO_BASE_PATH, repo_id)
        
        # 1. リポジトリのクローン (Notebook セル4相当)
        if os.path.exists(repo_path):
            print(f"既存のリポジトリを削除: {repo_path}")
            shutil.rmtree(repo_path, ignore_errors=True)
            
        print(f"リポジトリをクローン中: {repo_url} -> {repo_path}")
        Repo.clone_from(repo_url, repo_path)
        print("クローン完了。")

        # 2. データの読み込み (Notebook セル5相当)
        # 読み込む拡張子を増やす
        reader = SimpleDirectoryReader(
            input_dir=repo_path,
            required_exts=[".py", ".md", ".js", ".ts", ".tsx", ".jsx", ".toml", ".yaml"],
            recursive=True,
        )
        documents = reader.load_data()
        print(f"{len(documents)} 個のドキュメントを読み込み完了。")

        # 3. チャンキング (Notebook セル6相当)
        # 今回は言語を特定せず、汎用的なスプリッターを使う (必要に応じて CodeSplitter に変更可)
        # splitter = CodeSplitter(language="python") # <- ファイルタイプごとに行うのがベストだが、一旦シンプルに
        
        # シンプルなスプリッターで代替
        from llama_index.core.node_parser import SentenceSplitter
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=20)
        
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"{len(nodes)} 個のノードに分割完了。")

        # 4. Qdrantへの保存 (Notebook セル7相当)
        client = _get_qdrant_client()
        
        # 既存のコレクションがあれば削除 (本番では注意)
        try:
            client.delete_collection(collection_name=repo_id)
            print(f"既存のコレクションを削除: {repo_id}")
        except Exception as e:
            print(f"コレクション削除失敗 (存在しない可能性): {e}")
            
        vector_store = QdrantVectorStore(client=client, collection_name=repo_id)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        print("インデックス構築中...")
        VectorStoreIndex(
            nodes,
            storage_context=storage_context,
        )
        print("インデックス構築完了！")
        
        return repo_id

    except Exception as e:
        print(f"取り込み処理中にエラーが発生: {e}")
        # エラーを呼び出し元に伝播させる
        raise e

def query_repo(repo_id: str, query: str) -> str:
    """
    指定されたリポジトリID(コレクション)に対してクエリを実行する
    """
    try:
        # 1. Qdrantからインデックスをロード (Notebook セル8相当)
        client = _get_qdrant_client() # ★ ヘルパー関数でクライアント取得
        vector_store = QdrantVectorStore(client=client, collection_name=repo_id)
        
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
        )

        # 2. クエリエンジンの作成
        query_engine = index.as_query_engine(
            similarity_top_k=5 
        )
        print(f"クエリ実行 (Repo: {repo_id}): {query}")
        
        # 3. クエリ実行 (Notebook セル9相当)
        response = query_engine.query(query)
        
        return str(response)

    except Exception as e:
        print(f"クエリ処理中にエラーが発生: {e}")
        raise e