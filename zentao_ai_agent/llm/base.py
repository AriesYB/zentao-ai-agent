"""
LLM基类模块
提供大语言模型的初始化和配置
"""

from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler

from ..utils.config import config


def init_llm() -> ChatOpenAI:
    """
    初始化大语言模型

    Returns:
        ChatOpenAI: 配置好的大语言模型实例
    """
    api_key = config.llm_api_key
    api_base = config.llm_api_base
    model = config.llm_model
    temperature = config.llm_temperature

    chat_open_ai = ChatOpenAI(
        temperature=temperature,
        model=model,
        openai_api_key=api_key,
        openai_api_base=api_base,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
    )

    return chat_open_ai
