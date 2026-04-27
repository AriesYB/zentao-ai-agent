"""
状态定义模块
定义智能体的状态类型
"""

import operator
from typing import TypedDict, Dict, Any, List, Annotated

from langchain_core.messages import BaseMessage


def _replace_messages(_old: List[BaseMessage], new: List[BaseMessage]) -> List[BaseMessage]:
    """Reducer: 总是用新值覆盖旧值，用于在发生压缩或节点写回时直接覆盖消息列表。"""
    return new


# 定义简化的智能体状态
class AgentState(TypedDict, total=False):
    # =========message级变量==========
    # 当前用户输入
    cur_user_input: str
    # 当前响应
    cur_response: str
    # 当前工具执行结果
    cur_tools_results: List[Dict[str, Any]]
    # =========session级变量==========
    # 完整对话历史
    history: List[BaseMessage]
    # 退出标志
    should_exit: bool
    # 是否确认当前结果
    confirmed: bool
    # 任务规划结果
    task_plan: str
    # 任务参数
    task_params: Dict[str, Any]
