import tempfile
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from langchain_classic.tools import retriever
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sqlalchemy.testing import db
from langchain_classic.chains import ConversationalRetrievalChain

def qa_agent(api_key,memory,uploaded_file,question):
    model = ChatOpenAI(
        api_key=api_key,  # 推荐用环境变量
        base_url="https://api.deepseek.com",  # 指向DeepSeek的API地址
        model="deepseek-v4-pro",  # 指定模型名称
    )
    file_content = uploaded_file.read()
    temp_file_path = "temp.pdf"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file_content)
    loader = PyPDFLoader(temp_file_path)
    docs=loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=50,
        chunk_overlap=50,
        separators=["\n","。",",","!","?","、"]
    )
    texts = text_splitter.split_documents(docs)

    embedding_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"  # 轻量、免费、中文兼容性良好
    )

    db = FAISS.from_documents(texts,embedding_model)
    retriever =db.as_retriever()
    qa = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory
    )
    response = qa.invoke({"chat_history":memory,"question":question})
    return response