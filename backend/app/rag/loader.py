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


def _try_load_text(path: str, file_type: str) -> list[Document]:
    """尝试加载文本文件（编码自动检测：UTF-8 → GBK → GB2312 → 替换模式）"""
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

    # 文本类文件逐个尝试编码
    if file_type.lower() in ("txt", "csv", "md", "markdown"):
        for encoding in ["utf-8", "gbk", "gb2312", "gb18030"]:
            try:
                loader = loader_cls(path, encoding=encoding)
                docs = loader.load()
                if docs:
                    return docs
            except (UnicodeDecodeError, RuntimeError):
                continue
        # 全部失败，用替换模式兜底
        loader = loader_cls(path, encoding="utf-8", errors="replace")
        return loader.load()

    # PDF/DOCX 不需要指定编码
    if file_type.lower() == "csv":
        loader = loader_cls(path, encoding="utf-8")
    else:
        loader = loader_cls(path)
    return loader.load()


def load_document(file_path: str, file_type: str) -> list[Document]:
    """根据文件类型加载文档内容"""
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
        return _try_load_text(tmp_path, file_type)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
