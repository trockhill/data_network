import threading
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import engine, SessionLocal
from models import Base
from routers import nodes, edges, columns, scripts, lock, imports, export
from routers.lock import init_lock, release_lock_on_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: テーブル作成 + ロック初期化
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        init_lock(db)
    yield
    # 終了時: ロック解放
    with SessionLocal() as db:
        release_lock_on_shutdown(db)


app = FastAPI(
    title="データネットワーク可視化ツール",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(nodes.router)
app.include_router(edges.router)
app.include_router(columns.router)
app.include_router(scripts.router)
app.include_router(lock.router)
app.include_router(imports.router)
app.include_router(export.router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    port = 8000
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    print("=" * 50)
    print("データネットワーク可視化ツール 起動中...")
    print(f"URL: http://localhost:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print("終了するには Ctrl+C を押してください")
    print("=" * 50)
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
