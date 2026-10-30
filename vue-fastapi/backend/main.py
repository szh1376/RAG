from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
from typing import List, Optional
import json
import uuid
import os

from rag import build_index, stream_answer  # 你自己的 RAG 函数

app = FastAPI(title="AI PDF 问答后端")

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用内存字典存储已上传文档的索引用内存字典
document_store = {}

class ChatRequest(BaseModel):
    api_key: str
    document_id: str
    question: str
    history: List[dict] = []   # 格式: [{"role": "user", "content": "..."}, ...]

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are allowed")

    file_id = str(uuid.uuid4())

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{file_id}.pdf")

    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        index = build_index(temp_path)
        document_store[file_id] = index
        return {"document_id": file_id, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process PDF: {e}") from e
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """流式对话接口，使用 SSE 推送生成的 token"""
    if request.document_id not in document_store:
        return {"error": "Document not found, please upload again"}

    index = document_store[request.document_id]

    def generate():
        try:
            # 调用流式生成函数，要求该函数是一个生成器，逐个产出文本片段
            for chunk in stream_answer(
                api_key=request.api_key,
                vector_store=index,
                question=request.question,
                history=request.history
            ):
                # 包装成 SSE 格式，前端可解析
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            # 发送结束信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
