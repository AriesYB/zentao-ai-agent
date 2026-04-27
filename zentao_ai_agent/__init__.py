"""
Zentao AI Agent - 禅道任务规划与录入智能体
"""

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = ["AgenticTaskPlanner", "ZentaoTaskPlanAgent", "ZendaoTool"]


def __getattr__(name):
    if name == "ZendaoTool":
        from .zentao import ZendaoTool

        return ZendaoTool

    if name in {"AgenticTaskPlanner", "ZentaoTaskPlanAgent"}:
        from .agent import AgenticTaskPlanner, ZentaoTaskPlanAgent

        exported = {
            "AgenticTaskPlanner": AgenticTaskPlanner,
            "ZentaoTaskPlanAgent": ZentaoTaskPlanAgent,
        }
        return exported[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
