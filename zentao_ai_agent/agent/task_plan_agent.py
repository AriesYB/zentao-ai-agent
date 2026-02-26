import re
from datetime import datetime
from typing import Literal, Dict, Any

from chinese_calendar import is_workday
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from zentao_ai_agent.llm import llm_tool, init_llm, LLMToolIntegration, AgentState
from zentao_ai_agent.zentao import zendao_tool


@llm_tool
def get_current_date() -> Dict[str, Any]:
    """
    获取当前日期和星期几

    Returns:
        Dict[str, Any]: 包含当前日期和星期信息的字典
    """
    now = datetime.now()
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday = weekday_names[now.weekday()]

    return {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "today_is_workday": is_workday(now),
    }


@llm_tool
def get_next_workdays(week_type: Literal["current", "next"] = "next") -> Dict[str, Any]:
    """
    获取工作日的日期和星期几

    Args:
        week_type (Literal["current", "next"]): 工作日类型
            - "current": 本周工作日。如果今天是工作日，从今天开始收集；如果今天是节假日，从下一个工作日开始收集
            - "next": 下周工作日。如果今天是工作日，找到下一个节假日后的第一个工作日；如果今天是节假日，找到下一个工作日

    Returns:
        Dict[str, Any]: 包含工作日日期和星期信息的字典，包括：
        - today: 当前日期信息
        - today_is_workday: 今天是否是工作日
        - workdays: 工作日列表
        - week_type: 返回的工作日类型
    """
    from datetime import datetime, timedelta

    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    workdays = []

    # 从今天开始计算
    current_date = datetime.now()
    today_is_workday = is_workday(current_date)

    if week_type == "current":
        # 本周工作日
        if today_is_workday:
            # 如果今天是工作日，从今天开始收集
            date_to_check = current_date
        else:
            # 如果今天是节假日，从下一个工作日开始收集
            date_to_check = current_date + timedelta(days=1)
            while not is_workday(date_to_check):
                date_to_check += timedelta(days=1)

        # 收集工作日直到遇到节假日
        while is_workday(date_to_check):
            weekday_index = date_to_check.weekday()
            workdays.append({
                "date": date_to_check.strftime("%Y-%m-%d"),
                "weekday": weekday_names[weekday_index],
                "is_workday": True
            })
            date_to_check += timedelta(days=1)
    else:
        # 下周工作日（原有逻辑）
        date_to_check = current_date + timedelta(days=1)  # 从明天开始检查

        if today_is_workday:
            # 如果今天是工作日，需要找到下一个节假日后的第一个工作日
            # 先找到下一个节假日
            found_holiday = False
            while not found_holiday:
                if not is_workday(date_to_check):
                    found_holiday = True
                    # 找到节假日后，继续找到节假日后的第一个工作日
                    date_to_check += timedelta(days=1)
                    while not is_workday(date_to_check):
                        date_to_check += timedelta(days=1)
                    break
                date_to_check += timedelta(days=1)
        else:
            # 如果今天是节假日，找到下一个工作日
            while not is_workday(date_to_check):
                date_to_check += timedelta(days=1)

        # 现在date_to_check指向了起始工作日，收集工作日直到遇到下一个节假日
        while is_workday(date_to_check):
            weekday_index = date_to_check.weekday()
            workdays.append({
                "date": date_to_check.strftime("%Y-%m-%d"),
                "weekday": weekday_names[weekday_index],
                "is_workday": True
            })
            date_to_check += timedelta(days=1)

    return {
        "today": get_current_date(),
        "today_is_workday": today_is_workday,
        "workdays": workdays,
        "week_type": week_type
    }


@llm_tool
def calculate(expression: str) -> Dict[str, Any]:
    """
    执行基本的数学计算

    Args:
        expression (str): 数学表达式，支持 +, -, *, / 运算符

    Returns:
        Dict[str, Any]: 包含计算结果的字典
    """
    try:
        # 安全地计算表达式，只允许数字和基本运算符
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("表达式包含非法字符")

        result = eval(expression)
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e)
        }


class ZentaoTaskPlanAgent:
    """
    禅道任务规划智能体
    """

    def __init__(self):
        self.llm = init_llm()
        self.llm.callbacks=[StreamingStdOutCallbackHandler()]
        self.tool_integration = LLMToolIntegration(
            [
                # get_current_date,
                get_next_workdays,
                # calculate
            ]
        )
        self.zendao_tool = zendao_tool.ZendaoTool()
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:

        builder = StateGraph(AgentState)

        builder.add_node("user_input_node", self.user_input_node)
        builder.add_node("plan_node", self.plan_node)
        builder.add_node("tool_node", self.tool_node)
        builder.add_node("update_task_type_node", self.update_task_type_node)

        builder.add_edge(START, "user_input_node")

        # 合并两个条件边为一个，避免冲突
        builder.add_conditional_edges("user_input_node", self._handle_user_input_routing,
                                      ["plan_node", "update_task_type_node", END])
        builder.add_conditional_edges("plan_node", self._need_invoke_tool, ["tool_node", "user_input_node", "update_task_type_node"])
        builder.add_edge("tool_node", "plan_node")
        builder.add_edge("update_task_type_node", "user_input_node")

        # 创建图实例
        graph = builder.compile(name="zentao_task_plan_agent")
        print(graph.get_graph().draw_mermaid())
        return graph

    def invoke(self, state: AgentState) -> AgentState:
        return self.graph.invoke(state)

    def user_input_node(self, state: AgentState) -> AgentState:
        """
        用户输入节点：支持多行输入，以END结尾表示输入完毕
        """
        print("\n" + "=" * 50)

        # 正常的用户输入流程
        while True:
            print("请输入内容 (输入 'exit' 退出程序；输入 'confirm' 确认结果，换行后输入 'end' 结束多行输入):")

            # 收集多行输入
            lines = []
            while True:
                line = input()
                if line.strip().lower() == "end":
                    break
                if line.strip().lower() in ['exit', '退出']:
                    print("感谢使用禅道任务规划助手！")
                    return {"should_exit": True}
                if line.strip().lower() in ['confirm']:
                    return {"confirmed": True}
                lines.append(line)

            # 合并所有行作为用户输入
            user_input = "\n".join(lines).strip()

            # 检查空输入
            if not user_input or user_input.strip() == "":
                print("输入不能为空，请重新输入。")
                continue

            # 有效输入，退出循环
            break

        return {"cur_user_input": user_input, "should_exit": False}

    def _handle_user_input_routing(self, state: AgentState) -> Literal[str]:
        # 检查是否需要退出
        if state.get("should_exit", False):
            return END
        if state.get("confirmed", False):
            return "update_task_type_node"
        # 否则转发给大模型
        return "plan_node"

    def _need_invoke_tool(self, state: AgentState) -> Literal[str]:
        response = state.get("cur_response", "")
        if response and "<tools>" in response:
            return "tool_node"

        task_plan = state.get("task_plan", "")
        if task_plan and "人员姓名" in task_plan and "需求编号" in task_plan and "任务名称" in task_plan:
            return "update_task_type_node"
        if "最终结果" in task_plan:
            return "update_task_type_node"

        return "user_input_node"

    def plan_node(self, state: AgentState) -> AgentState:
        """
        规划任务节点
        """
        tool_prompt = self.tool_integration.get_tool_prompt()

        sys_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                template="""
# 任务
你是一个禅道任务工时规划助手。
                
## 核心原则
1. 根据用户要求，生成若干工作任务，若信息不足则先要求用户补充，必须获取用户姓名、岗位(前端开发、后端开发、产品、测试、运维等)、需求编号，随后获取下次工作日的日期，禁止假设和推断日期。等信息完整后再规划任务。
2. 任务命名规范：
- 需求任务为 #需求（来源：业务需求，大部分任务）
- bug任务为 @BUG类（来源：生产事件/BUG，改bug）
- 事项任务为 *事项（来源：非业务需求，请假、出差等）
3. 每个任务不超过8小时，如果超过了就让用户协助拆分任务，每个任务最少2小时，确保写满工作日的工时（一般是5天40小时，具体得看工作日情况），除非遇到节假日调休；当天完成的结束日期写当天
4. 任务数量不足时让用户补充；任务数量太多时提示用户去除部分任务，工作量需要适当评估，不要排得太紧急忙不过来，而且可能存在对接联调、沟通协调等事情
5. 任务类型暂时使用简短描述（如：研究、后端开发、前端编码、测试、会议及培训等），后续会自动转换为标准类型
6. 任务尽量拆分为8个及以上
7. 表头为 人员姓名、需求编号、任务名称（功能点）、任务类型、预计工时（小时）、预计开始、预计结束
8. 输出可直接复制粘贴进excel的文本，且需要保留表头。输出示例：

张三	103615	【#103615-PageIndex解析文件-研究】研究测试PageIndex官网版api	研究	4	2025/11/24	2025/11/24
张三	103615	【#103615-PageIndex解析文件-编码】编写调用代码解析采购需求文件	后端开发	4	2025/11/24	2025/11/24
张三	103615	【#103615-PageIndex解析文件-验证】验证大模型对相关性内容召回情况	测试	4	2025/11/25	2025/11/25
张三	103615	【#103615-PageIndex解析文件-编码】调整检索内容提示词	后端开发	8	2025/11/25	2025/11/26
张三	103615	【#103615-PageIndex解析文件-讨论】汇报讨论效果	会议及培训	4	2025/11/26	2025/11/26
张三	103615	【#103615-表单搜索项研究-研究】研究表单依据什么进行检索	研究	8	2025/11/27	2025/11/27
张三	103615	【#103615-其他文件解析工具-研究】研究其他文件解析工具	研究	4	2025/11/28	2025/11/28
张三	103615	【#103615-其他文件解析工具-会议】进度汇报和讨论	会议及培训	4	2025/11/28	2025/11/28
                
## 今天的日期
{today_date}

## 工具
{tool_prompt}     
                """
            )
        ])

        history_messages = state.get("history", [])

        # 首次对话
        if not history_messages or len(history_messages) == 0:
            # 系统提示词
            system_messages = sys_prompt.format_messages(
                tool_prompt=tool_prompt,
                today_date=get_current_date()
            )

            # 用户输入
            cur_user_input = state.get("cur_user_input", "")
            user_messages = [HumanMessage(content=f"## 用户输入\n{cur_user_input}")]

            # 合并消息为新数组
            history_messages = system_messages + user_messages
        else:
            # TODO 判断是否需要压缩上下文

            # 上一次调用工具的结果作为新的消息传递
            cur_tools_results = state.get("cur_tools_results", [])
            if cur_tools_results and len(cur_tools_results) > 0:
                history_messages.append(ToolMessage(content=f"工具调用结果:{cur_tools_results}", tool_call_id="fake"))

            # 有新的用户输入
            cur_user_input = state.get("cur_user_input", "")
            if cur_user_input:
                history_messages.append(HumanMessage(content=f"用户输入\n{cur_user_input}"))

        # debug
        # for m in history_messages:
        #     m.pretty_print()

        response = self.llm.invoke(history_messages)

        # 添加对话记录时，清理think标签
        content = re.sub(r'<think>.*?</think>', '', response.content, flags=re.DOTALL)
        history_messages.append(AIMessage(content=content))

        # 检查响应是否包含任务规划结果
        if "人员姓名" in content and "需求编号" in content and "任务名称" in content:
            # 保存任务规划结果
            return {"cur_response": response.content, "history": history_messages, "cur_user_input": None,
                    "cur_tools_results": None, "task_plan": content}

        return {"cur_response": response.content, "history": history_messages, "cur_user_input": None,
                "cur_tools_results": None}

    def tool_node(self, state: AgentState) -> AgentState:
        """
        工具节点：调用工具处理用户输入
        """
        cur_response = state.get('cur_response', "")
        tools_results = self.tool_integration.process_response(cur_response)
        if tools_results and len(tools_results) > 0:
            return {"cur_tools_results": tools_results, "cur_response": None}
        return state

    def update_task_type_node(self, state: AgentState) -> AgentState:
        """
        更新任务类型节点：将任务规划中的简短任务类型转换为标准任务类型
        动态从禅道系统获取最新的任务类型列表
        """
        task_plan = state.get("task_plan", "")
        if not task_plan:
            return state

        # 动态获取任务类型映射
        try:
            dynamic_task_types = zendao_tool.get_task_types()
            task_type_mapping = "\n".join([f"{k}: {v}" for k, v in dynamic_task_types.items()])
        except Exception as e:
            # 如果动态获取失败，使用静态的任务类型字典作为后备
            print(f"动态获取任务类型失败，使用静态字典: {e}")
            task_type_mapping = "\n".join([f"{k}: {v}" for k, v in zendao_tool.task_type_dict.items()])

        sys_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                template="""
# 任务
你是一个任务类型标准化助手。

## 任务
将任务规划中的简短任务类型转换为禅道标准任务类型，如果任务名称中用词不对也需要同步转换。

## 任务类型映射
{task_type_mapping}

## 转换规则
1. 根据任务名称和简短任务类型，选择最匹配的标准任务类型
2. 保持任务规划的其他内容不变（人员姓名、需求编号、任务名称（带有任务类型名时需要更改）、预计工时、预计开始、预计结束）
3. 输出格式与输入格式一致，使用制表符分隔
4. 输出可直接复制粘贴进excel的文本

## 输入示例
张三	103615	【#103615-PageIndex解析文件-研究】研究测试PageIndex官网版api	研究	4	2025/11/24	2025/11/24

## 输出示例
张三	103615	【#103615-PageIndex解析文件-研究】研究测试PageIndex官网版api	市场/用户调研	4	2025/11/24	2025/11/24
                """
            )
        ])

        # 构建消息
        messages = sys_prompt.format_messages(task_type_mapping=task_type_mapping)
        messages.append(HumanMessage(content=f"## 任务规划\n{task_plan}"))

        # 调用大模型
        response = self.llm.invoke(messages)

        # 清理think标签
        content = re.sub(r'</think>', '', response.content, flags=re.DOTALL)

        # 更新任务规划
        return {"task_plan": content, "cur_response": content}


if __name__ == "__main__":
    # 初始化智能体
    guide_agent = ZentaoTaskPlanAgent()

    # 初始化状态
    current_state = AgentState()

    print("=== 禅道任务规划助手 ===")
    print("程序将引导您完成禅道任务规划")
    print("=" * 50)

    # 调用智能体，让它自己处理用户输入循环
    result_state = guide_agent.invoke(current_state)

    # 检查是否正常退出
    if result_state.get("should_exit", False):
        print("\n程序已正常退出")
