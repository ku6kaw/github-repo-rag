```bash
jupyter lab
```

```bash
docker run -p 6333:6333 -p 6334:6334 \
       -v $(pwd)/qdrant_storage:/qdrant/storage \
       qdrant/qdrant
```

```bash
# (永続化を気にしない、最もシンプルな起動コマンド)
docker run --rm -p 6333:6333 -p 6334:6334 qdrant/qdrant
```