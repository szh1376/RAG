# AI智能PDF问答工具

这是一个基于 Streamlit 的本地 PDF 问答应用。用户可以上传 PDF 文件，输入问题后，程序会读取 PDF 内容、切分文本、构建向量索引，并通过 DeepSeek API 生成面向文档内容的回答。

项目适合用于学习 RAG（检索增强生成）的基础流程，也可以作为一个简单的本地文档问答工具使用。

## 功能特点

- 上传 PDF 文件并解析文本内容
- 将 PDF 内容切分为适合检索的小段文本
- 使用 HuggingFace Embeddings 生成文本向量
- 使用 FAISS 构建本地向量检索库
- 调用 DeepSeek API 进行对话式问答
- 在页面中展示答案和历史对话记录

## 技术栈

- Python
- Streamlit：构建网页交互界面
- LangChain：组织 RAG 问答流程
- DeepSeek API：提供大语言模型能力
- PyPDFLoader：读取 PDF 文件内容
- HuggingFace Embeddings：生成文本向量
- FAISS：本地向量检索

## 项目结构

```text
AI智能PDF问答工具/
├── main.py              # Streamlit 前端入口，负责页面展示、文件上传和问题输入
├── RAG.py               # PDF 问答核心逻辑，负责加载 PDF、切分文本、向量检索和调用模型
├── requirements.txt     # 项目依赖列表
├── temp.pdf             # 程序运行时保存上传 PDF 的临时文件
└── README.md            # 项目说明文档
```

## 安装依赖

建议先进入项目目录：

```bash
cd AI智能PDF问答工具
```

创建并激活虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell：

```bash
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 启动项目

在 `AI智能PDF问答工具` 目录下运行：

```bash
streamlit run main.py
```

启动后，浏览器会打开 Streamlit 页面。如果没有自动打开，可以根据终端提示访问本地地址，通常是：

```text
http://localhost:8501
```

## 使用方法

1. 在侧边栏输入 DeepSeek API Key。
2. 点击页面中的上传区域，选择一个 PDF 文件。
3. 在问题输入框中输入你想问的问题。
4. 等待 AI 生成回答。
5. 在“历史消息”区域查看之前的提问和回答。

## 核心流程

项目的主要问答流程在 `RAG.py` 的 `qa_agent(api_key, memory, uploaded_file, question)` 函数中：

1. 使用 `ChatOpenAI` 连接 DeepSeek API。
2. 将上传的 PDF 保存为 `temp.pdf`。
3. 使用 `PyPDFLoader` 加载 PDF 内容。
4. 使用 `RecursiveCharacterTextSplitter` 切分文本。
5. 使用 `HuggingFaceEmbeddings` 生成文本向量。
6. 使用 `FAISS` 创建向量数据库。
7. 使用 `ConversationalRetrievalChain` 结合历史对话和检索结果生成回答。

## 注意事项

- 运行前需要准备 DeepSeek API Key。
- 代码中模型接口地址为 `https://api.deepseek.com`。
- 当前模型名称配置为 `deepseek-v4-pro`，如果接口返回模型不存在或不可用，请根据 DeepSeek 平台实际支持的模型名称调整。
- 首次运行时可能会下载 `all-MiniLM-L6-v2` embedding 模型，耗时取决于网络环境。
- 代码设置了 `HF_ENDPOINT=https://hf-mirror.com`，用于加速 HuggingFace 模型下载。
- 程序会把上传的 PDF 临时写入 `temp.pdf`，再次上传时会覆盖该文件。
- 页面中“请输入APPI密钥”是界面文案拼写问题，不影响功能。

## 常见问题

### 1. 安装依赖失败怎么办？

可以先升级 pip：

```bash
python -m pip install --upgrade pip
```

然后重新安装：

```bash
pip install -r requirements.txt
```

如果是 `faiss-cpu` 或 `torch` 安装失败，通常和 Python 版本、系统环境或网络有关，可以尝试更换 Python 版本或使用国内镜像源。

### 2. 首次运行很慢怎么办？

首次运行可能需要下载 embedding 模型。请保持网络连接稳定，等待模型下载完成。下载完成后，后续运行通常会更快。

### 3. 提示 API Key 错误怎么办？

请确认：

- API Key 是否填写完整
- API Key 是否来自 DeepSeek 平台
- DeepSeek 账户是否有可用额度
- 模型名称是否仍然可用

### 4. PDF 无法正常回答怎么办？

可能原因包括：

- PDF 是扫描件图片，无法直接提取文字
- PDF 内容为空或加密
- 文档内容太少，检索不到有效上下文
- 问题和 PDF 内容无关

可以优先尝试使用文字型 PDF，并提出和文档内容直接相关的问题。

## 当前限制

- 当前只支持单个 PDF 文件上传。
- 当前没有做用户登录、权限管理或在线部署配置。
- 当前 API Key 需要在页面侧边栏手动输入。
- 当前临时 PDF 文件固定保存为 `temp.pdf`，不适合多人同时使用。
