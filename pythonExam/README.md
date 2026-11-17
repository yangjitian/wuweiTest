# FastAPI 流式接口演示

后端把内置文本切块，用 SSE 逐块推给浏览器；前端把「流式」和「一次性返回」并排跑同一段文本，让首字到达的差异可见。不接 LLM。

## 实测

| | 流式 SSE | 一次性 JSON |
|---|---|---|
| 首字延迟 | 4 ~ 5 ms | 3078 ms |
| 总耗时 | 3721 ms | 3078 ms |

medium 文本 234 字、30 ms/块；延时带 0.5 ~ 1.5 随机抖动，每次数值略有不同。

## 运行

```bash
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
# 打开 http://127.0.0.1:8000/ ，加 ?auto=1 打开即自动跑
```

验证真的分块到达（`-N` 关掉 curl 自己的缓冲）：

```bash
curl -N "http://127.0.0.1:8000/api/stream/medium?delay=0.03"
```

## 结构

| 文件 | 说明 |
|---|---|
| `main.py` | 路由 + SSE 生成器 + 切块，约 80 行 |
| `texts.py` | 三段内置中文文本（short / medium / long） |
| `static/index.html` | 单文件前端，无构建依赖 |
| `test_main.http` | IDE 里可直接点的请求 |

## 接口

| 路径 | 说明 |
|---|---|
| `GET /` | 对比演示页 |
| `GET /api/texts` | 文本列表 |
| `GET /api/stream/{id}?delay=0.03` | SSE 逐块推送 |
| `GET /api/plain/{id}?delay=0.03` | 对照组，攒完一次性返回 |

`delay` 是每块的基准延时（秒，0 ~ 1）。未知 `id` 返回 404。

## 关键实现

后端用生成器逐块产出，交给 `StreamingResponse`；每轮先查断开，避免用户关页面后白算：

```python
async def event_source():
    for token in tokens:
        if await request.is_disconnected():
            return
        yield f"data: {json.dumps({'delta': token}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(delay)
    yield "data: [DONE]\n\n"

return StreamingResponse(event_source(), media_type="text/event-stream")
```

前端用 `fetch` + `ReadableStream` 手动解帧，`\n\n` 分帧，残帧留在 buffer：

```js
buffer += decoder.decode(value, { stream: true });
const frames = buffer.split("\n\n");
buffer = frames.pop();          // 最后一段可能不完整
for (const f of frames) { /* 取 data: 后的 JSON 追加到页面 */ }
```

没用 `EventSource`：不能自定义请求头，也不好取消。`fetch` 能接 `AbortController`，点「停止」后后端 `is_disconnected()` 立即感知。

## 上线注意

Nginx 的 `proxy_buffering` 默认开启，会把流攒成一次性返回——典型症状是「本地正常、线上失灵」。响应头已带 `X-Accel-Buffering: no`，Nginx 侧仍需：

```nginx
location /api/ {
    proxy_buffering off;
    proxy_cache off;
    proxy_http_version 1.1;
}
```

## 换成真实 LLM

前端不用改，只要 SSE 的 `data: {"delta": ...}` 格式不变：

```python
async for chunk in client.chat.completions.create(model="...", stream=True):
    if delta := chunk.choices[0].delta.content:
        yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
```

`tokenize()` 和 `asyncio.sleep()` 可以直接删掉。
