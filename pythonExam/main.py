"""FastAPI 流式接口演示：同一段文本，两种传输方式。

- GET /api/stream/{text_id}  SSE 逐块推送
- GET /api/plain/{text_id}   攒完一次性返回（用于对比）
"""

import asyncio
import json
import random
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from texts import TEXTS

app = FastAPI(title="FastAPI Streaming Demo")
STATIC_DIR = Path(__file__).parent / "static"


def tokenize(text: str) -> list[str]:
    """切成 1~2 个字符的小块，模拟模型逐 token 输出。"""
    tokens: list[str] = []
    buf = ""
    for piece in re.findall(r"[A-Za-z0-9_.+#/-]+|\s+|[^\s]", text):
        if len(piece) == 1 and ord(piece) > 127:  # 中日韩字符按两个一组
            buf += piece
            if len(buf) == 2:
                tokens.append(buf)
                buf = ""
        else:
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(piece)
    if buf:
        tokens.append(buf)
    return tokens


def get_text(text_id: str) -> str:
    if text_id not in TEXTS:
        raise HTTPException(status_code=404, detail=f"未知文本：{text_id}")
    return TEXTS[text_id]["content"]


@app.get("/api/texts")
def list_texts():
    return [
        {"id": key, "title": item["title"], "chars": len(item["content"])}
        for key, item in TEXTS.items()
    ]


@app.get("/api/stream/{text_id}")
async def stream(text_id: str, request: Request, delay: float = Query(0.03, ge=0, le=1)):
    """SSE：每算出一块就发一块。"""
    tokens = tokenize(get_text(text_id))

    async def event_source():
        for token in tokens:
            if await request.is_disconnected():  # 前端点了「停止」就收手
                return
            payload = json.dumps({"delta": token}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(delay * random.uniform(0.5, 1.5))
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/plain/{text_id}")
async def plain(text_id: str, delay: float = Query(0.03, ge=0, le=1)):
    """对照组：干同样的活，但攒到最后一次返回。"""
    tokens = tokenize(get_text(text_id))
    await asyncio.sleep(len(tokens) * delay)  # 与流式总耗时大致相当
    return {"text": "".join(tokens)}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
