# RAG PDF 问答（Vue + FastAPI）

上传文本型 PDF 后，后端使用 LangChain、Hugging Face 嵌入模型和 FAISS 建立内存索引。前端通过 Vue 3 和 Element Plus 提问，DeepSeek 根据检索片段流式回答。

## 本地运行

需要 Python、Node.js 与 npm。首次运行会下载 `all-MiniLM-L6-v2` 嵌入模型；问答需要自己的 DeepSeek API Key。分别在两个终端运行：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm ci
npm run dev
```

打开 Vite 输出的本地地址（通常是 <http://localhost:5173>），在左侧输入 DeepSeek API Key，然后上传 PDF 并提问。前端开发服务器会将 `/api` 请求代理到本机 8000 端口。

macOS/Linux 使用 `python3 -m venv .venv` 和 `.venv/bin/python`，其余步骤相同。

## 项目结构

```text
backend/main.py          FastAPI 上传与流式问答接口
backend/rag.py           PDF 解析、向量检索和 DeepSeek 调用
backend/requirements.txt Python 依赖
frontend/src/App.vue     问答界面
frontend/vite.config.js  开发服务器代理
```

`POST /api/upload` 接受 PDF 文件并返回 `document_id`；`POST /api/chat` 接受 `api_key`、`document_id`、`question` 和可选 `history`，以 SSE 返回回答片段。交互式接口文档见 <http://127.0.0.1:8000/docs>。

上传文件只在索引构建期间存于系统临时目录，随后删除。索引保存在后端进程内存中，重启后需要重新上传。DeepSeek API Key 由浏览器随问答请求发给本地后端，当前版本仅适合个人本地开发使用。扫描版 PDF 需要先做 OCR。
