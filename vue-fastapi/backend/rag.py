import tempfile
import os
from typing import List, Dict, Generator

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

# HuggingFace 镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


def build_index(pdf_path: str):
    """
    解析 PDF，切分文本，建立向量索引。
    返回 FAISS 向量库对象，后续提问直接使用。
    """
    # 1. 加载 PDF
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # 2. 文本切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n", "。", ",", "!", "?", "、"]
    )
    texts = text_splitter.split_documents(docs)

    # 3. 初始化 Embedding 模型
    embedding_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # 4. 建立向量索引
    vector_store = FAISS.from_documents(texts, embedding_model)

    return vector_store

def stream_answer(
    api_key: str,
    vector_store: FAISS,
    question: str,
    history: List[Dict[str, str]] = None
) -> Generator[str, None, None]:
    """
    使用现有索引回答问题，并以流式方式产出 token。
    history: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    if history is None:
        history = []

    # 1. 检索相关文档（取 top 4 个片段）
    docs = vector_store.similarity_search(question, k=4)
    context = "\n\n".join([doc.page_content for doc in docs])

    # 2. 拼接历史对话（只保留最近 3 轮，防止 prompt 过长）
    history_text = ""
    for msg in history[-6:]:   # 每轮一问一答，所以取 6 条
        role = "用户" if msg["role"] == "user" else "AI"
        history_text += f"{role}: {msg['content']}\n"

    # 3. 构建 Prompt
    system_prompt = "你是一个基于文档的问答助手。请严格根据以下上下文回答用户的问题。如果上下文中没有相关信息，请直接回答“文档中未找到相关内容”，不要编造。"
    user_prompt = f"""上下文信息：{context}

                    对话历史：{history_text}

                    用户当前问题：{question}

                    请给出准确、简洁的回答："""

    # 4. 调用 DeepSeek 流式 API（使用 OpenAI 兼容接口）
    model = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        streaming=True              # 开启流式
    )

    # ChatOpenAI 的 stream 方法返回生成器
    for chunk in model.stream([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]):
        # chunk.content 是当前 token 的文本
        if chunk.content:
            yield chunk.content
