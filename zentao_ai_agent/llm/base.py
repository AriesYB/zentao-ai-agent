"""
LLM基类模块
提供大语言模型的初始化和配置
"""

from typing import Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler, StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI

from ..utils.config import config


def init_llm(
    *,
    streaming: bool = False,
    callbacks: Optional[Sequence[BaseCallbackHandler]] = None,
) -> ChatOpenAI:
    """
    初始化大语言模型。

    Args:
        streaming: 是否启用流式输出。
        callbacks: 自定义回调列表；当 streaming=True 且未显式提供时，会默认输出到标准输出。

    Returns:
        ChatOpenAI: 配置好的大语言模型实例
    """
    api_key = config.llm_api_key
    api_base = config.llm_api_base
    model = config.llm_model
    temperature = config.llm_temperature

    resolved_callbacks = list(callbacks or [])
    if streaming and not resolved_callbacks:
        resolved_callbacks = [StreamingStdOutCallbackHandler()]

    chat_open_ai = ChatOpenAI(
        temperature=temperature,
        model=model,
        openai_api_key=api_key,
        openai_api_base=api_base,
        streaming=streaming,
        callbacks=resolved_callbacks or None,
    )

    return chat_open_ai
