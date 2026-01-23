"""
使用禅道任务规划智能体
"""

from zentao_ai_agent import ZentaoTaskPlanAgent


def main():
    """
    基本使用示例
    """
    # 初始化智能体
    agent = ZentaoTaskPlanAgent()

    # 运行智能体
    agent.invoke({})


if __name__ == "__main__":
    main()
