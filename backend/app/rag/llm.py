"""百炼 LLM 模型封装"""

from langchain_openai import ChatOpenAI
from app.config import get_settings

_main_llm = None
_simple_llm = None
_complex_llm = None


def get_llm(model_type: str = "main") -> ChatOpenAI:
    """获取 LLM 实例

    Args:
        model_type: "main" (qwen-plus), "simple" (qwen-turbo), "complex" (qwen-max)
    """
    global _main_llm, _simple_llm, _complex_llm
    settings = get_settings()

    cache_map = {
        "main": ("_main_llm", settings.llm_model),
        "simple": ("_simple_llm", settings.llm_model_simple),
        "complex": ("_complex_llm", settings.llm_model_complex),
    }

    attr_name, model = cache_map.get(model_type, cache_map["main"])

    cached = globals().get(attr_name)
    if cached is None:
        cached = ChatOpenAI(
            model=model,
            openai_api_key=settings.dashscope_api_key,
            openai_api_base=settings.dashscope_base_url,
            temperature=0.1,
            streaming=True,
            max_tokens=2048,
        )
        globals()[attr_name] = cached
    return cached
