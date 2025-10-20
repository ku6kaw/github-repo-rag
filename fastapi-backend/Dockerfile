# 1. ベースイメージ
FROM python:3.10-slim

# 2. 作業ディレクトリ
WORKDIR /app

# 3. git コマンドをインストール
# apt-get (Debianのパッケージマネージャ) を使ってgitをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4. 必要なPythonライブラリをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. アプリケーションコードをコピー
COPY ./app /app/app

# 6. 実行コマンド (Cloud Run が $PORT を渡す)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT