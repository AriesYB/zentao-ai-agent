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
杨彪	106082	【#106082-中间件认知】了解消息队列在系统中的基础作用	技术预研	4	2026/02/02	2026/02/02  
杨彪	106082	【#106082-数据库认知】查看核心业务表名称及基础字段	技术预研	4	2026/02/02	2026/02/02  
杨彪	106082	【#106082-业务流程体验】在测试环境走通标准业务路径	产品功能测试	4	2026/02/03	2026/02/03  
杨彪	106082	【#106082-系统日志认知】了解日志存储位置和查看方式	技术预研	4	2026/02/03	2026/02/03  
杨彪	106082	【#106082-文档查阅】浏览现有架构文档目录结构	项目文档编写	4	2026/02/04	2026/02/04  
杨彪	106082	【#106082-代码结构认知】查看核心模块代码文件分布	技术预研	4	2026/02/04	2026/02/04  
杨彪	106082	【#106082-团队初识】与同事交流业务线基础分工	通用支持	4	2026/02/05	2026/02/05  
杨彪	106082	【#106082-环境初建】配置本地基础开发环境	通用研发	4	2026/02/05	2026/02/05  
杨彪	106082	【#106082-功能初验】执行基础业务流程冒烟测试	产品功能测试	4	2026/02/06	2026/02/06  
杨彪	106082	【#106082-信息初整】汇总基础业务线认知要点	项目文档编写	4	2026/02/06	2026/02/06  
"""

        # 用户名映射（中文名 -> 系统用户名）
        username_mapping = {
            "杨彪": "yangbiao"
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
