"""文档分割策略"""

from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain.schema import Document


def split_documents(docs: list[Document], chunk_size: int = 512, chunk_overlap: int = 50) -> list[Document]:
    """
    智能文档分割：
    - 对 Markdown 类型文档先按标题分割，再按大小切分
    - 对普通文档直接用 RecursiveCharacterTextSplitter
    """
    # 尝试按 Markdown 标题分割
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
        ("####", "h4"),
    ]

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=True,
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "，", " ", ""],
        length_function=len,
    )

    final_chunks = []

    for doc in docs:
        # 先尝试 Markdown 标题分割
        if any(header in doc.page_content for header in ["#", "##", "###"]):
            try:
                md_splits = md_splitter.split_text(doc.page_content)
                # 对每个标题段再用大小分割器切分
                for split in md_splits:
                    sub_chunks = text_splitter.split_documents([split])
                    # 保留元数据中的标题信息
                    for chunk in sub_chunks:
                        if hasattr(split, "metadata"):
                            chunk.metadata.update(split.metadata)
                        chunk.metadata.update(doc.metadata)
                    final_chunks.extend(sub_chunks)
                continue
            except Exception:
                pass

        # 普通文本分割
        chunks = text_splitter.split_documents([doc])
        final_chunks.extend(chunks)

    return final_chunks
