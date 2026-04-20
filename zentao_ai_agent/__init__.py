"""
Zentao AI Agent - 禅道任务规划与录入智能体
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .zentao import ZendaoTool

try:
    from .agent import ZentaoTaskPlanAgent
except ModuleNotFoundError:
    ZentaoTaskPlanAgent = None

__all__ = ["ZentaoTaskPlanAgent", "ZendaoTool"]
