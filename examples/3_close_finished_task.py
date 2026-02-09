"""
关闭已完成任务示例
演示如何安全地关闭已完成的任务
任务列表默认分页size为20
"""

from zentao_ai_agent import ZendaoTool


def main():
    """
    关闭已完成任务示例
    """
    # 创建禅道工具实例
    zendao = ZendaoTool()

    # 登录（使用环境变量中的账号密码）
    if zendao.login():
        print("登录成功")

        # 获取我的任务列表
        tasks = zendao.get_my_tasks()
        task_list = tasks.get('tasks', [])

        print(f"总任务数: {len(task_list)}")

        # 筛选已完成的任务（status='done'但未closed）
        finished_tasks = []
        for task in task_list:
            # 只处理已完成的任务
            if task.get('status') == 'done':
                # 检查是否已经关闭
                if task.get('closedDate') == '0000-00-00 00:00:00':  # 没有关闭日期说明未关闭
                    finished_tasks.append(task)

        if not finished_tasks:
            print("没有找到已完成的待关闭任务")
            return

        print(f"找到 {len(finished_tasks)} 个已完成的待关闭任务：")
        print("=" * 80)

        # 显示待关闭的任务详情
        for i, task in enumerate(finished_tasks, 1):
            print(f"{i}. 任务ID: {task.get('id')}")
            print(f"   任务名称: {task.get('name')}")
            print(f"   状态: {task.get('status')}")
            print(f"   完成人: {task.get('finishedBy', '未知')}")
            print(f"   完成日期: {task.get('finishedDate', '未知')}")
            print(f"   指派给: {task.get('assignedTo', '未知')}")
            print(f"   预估工时: {task.get('estimate', 0)} 小时")
            print(f"   消耗工时: {task.get('consumed', 0)} 小时")
            print()

        # 二次确认
        print("=" * 80)
        print("⚠️  警告：即将关闭以上已完成任务")
        print("请确认这些任务确实已经完成，并且可以关闭")
        confirm = input(f"确认关闭这 {len(finished_tasks)} 个任务？(输入 'yes' 确认): ")

        if confirm.lower() != 'yes':
            print("已取消关闭操作")
            return

        # 执行关闭操作
        print("\n开始关闭任务...")
        success_count = 0
        failed_count = 0

        for task in finished_tasks:
            task_id = task.get('id')
            task_name = task.get('name')

            try:
                # 关闭任务，可以添加关闭备注
                success = zendao.close_task(
                    task_id=task_id,
                    comment="任务已完成，自动关闭"
                )

                if success:
                    print(f"✓ 任务 #{task_id} - {task_name} 关闭成功")
                    success_count += 1
                else:
                    print(f"✗ 任务 #{task_id} - {task_name} 关闭失败")
                    failed_count += 1

            except Exception as e:
                print(f"✗ 任务 #{task_id} - {task_name} 关闭异常: {e}")
                failed_count += 1

        print("\n" + "=" * 80)
        print(f"关闭操作完成！")
        print(f"成功: {success_count} 个")
        print(f"失败: {failed_count} 个")

    else:
        print("登录失败")


if __name__ == "__main__":
    main()
