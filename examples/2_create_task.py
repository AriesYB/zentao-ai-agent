"""
批量创建任务示例
演示如何使用禅道工具批量创建任务
"""

from zentao_ai_agent import ZendaoTool


def main():
    """
    批量创建任务示例
    """
    # 创建禅道工具实例
    zendao = ZendaoTool()

    # 登录（使用环境变量中的账号密码）
    if zendao.login():
        print("登录成功")

        # 获取进行中的项目列表
        doing_projects = zendao.get_doing_projects()
        print(f"进行中的项目数量: {len(doing_projects)}")

        # 获取用户列表
        users = zendao.get_user_list()
        print(f"用户数量: {len(users)}")

        # 需求列表
        assigned_stories = zendao.get_assigned_stories()
        print(f"指派给我的需求数量: {assigned_stories.get('stories', [])}")

        # 根据需求id获取需求详情
        print(f"需求详情: {zendao.get_story_detail(104096)}")

        # 获取任务列表
        tasks = zendao.get_my_tasks()
        for e in tasks.get('tasks', []):
            print(f"任务: {e}")

        # 批量创建任务示例
        batch_data = """
张三	108611	【#108611-禅道智能体设计-概要设计】设计禅道智能体的主要流程	概要设计	4	2026/01/05	2026/01/05
张三	108611	【#108611-禅道智能体设计-概要设计2】设计禅道智能体的主要流程2	概要设计	4	2026/01/05	2026/01/05
张三	108611	【#108611-禅道智能体设计-概要设计3】设计禅道智能体的主要流程3	概要设计	8	2026/01/06	2026/01/06
"""

        # 用户名映射（中文名 -> 系统用户名）
        username_mapping = {
            "张三": "zhangsan"
            # "你的名字": "禅道姓名拼音"
        }

        # 第一步：验证数据（不执行创建）
        batch_result = zendao.batch_create_tasks_from_text(batch_data, username_mapping, execute_create=False)

        if batch_result['validation_passed']:
            print(f"验证通过，准备创建 {len(batch_result['tasks_to_create'])} 个任务")
            print("=" * 50)
            for i, task in enumerate(batch_result['tasks_to_create'], 1):
                print(f"{i}. {task['task_name']}")
                print(f"   需求ID: {task['story_id']}")
                print(f"   任务类型: {task['task_type_cn']}")
                print(f"   指派给: {task['assigned_to']}")
                print(f"   工时: {task['estimate']}小时")
                print(f"   时间: {task['est_started']} ~ {task['deadline']}")
                print()

            # 确认后执行创建
            confirm = input("确认创建以上任务？(yes/no): ")
            if confirm.lower() == 'yes':
                print("开始创建任务...")
                # 第二步：执行批量创建
                create_result = zendao.batch_create_tasks_from_text(batch_data, username_mapping, execute_create=True)
                for result in create_result['create_results']:
                    print(f"✓ {result['task_name']} - 创建成功")
                    print(result)
                print(f"共创建 {len(create_result['create_results'])} 个任务")
            else:
                print("已取消创建")
        else:
            print("验证失败，请检查以下错误：")
            for error in batch_result['validation_errors']:
                print(f"✗ {error}")

    else:
        print("登录失败")


if __name__ == "__main__":
    main()
