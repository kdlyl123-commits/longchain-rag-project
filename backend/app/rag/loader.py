"""文档加载器：支持 PDF、Word、TXT、Markdown、CSV"""

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
)
from langchain.schema import Document
from app.services.document_service import download_file
import os
import tempfile


def load_document(file_path: str, file_type: str) -> list[Document]:
    """根据文件类型加载文档内容"""
    # 统一使用 download_file（本地文件系统或 MinIO）
    content = download_file(file_path)

    suffix_map = {
        "pdf": ".pdf",
        "docx": ".docx",
        "doc": ".docx",
        "txt": ".txt",
        "md": ".md",
        "markdown": ".md",
        "csv": ".csv",
    }
    suffix = suffix_map.get(file_type.lower(), ".txt")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        loader_map = {
            "pdf": PyPDFLoader,
            "docx": Docx2txtLoader,
            "doc": Docx2txtLoader,
            "txt": TextLoader,
            "md": UnstructuredMarkdownLoader,
            "markdown": UnstructuredMarkdownLoader,
            "csv": CSVLoader,
        }

        loader_cls = loader_map.get(file_type.lower(), TextLoader)

        if file_type.lower() == "csv":
            loader = loader_cls(tmp_path, encoding="utf-8")
        else:
            loader = loader_cls(tmp_path)

        docs = loader.load()
        return docs
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
