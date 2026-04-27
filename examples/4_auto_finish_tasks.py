"""
按日期自动完成任务示例

用途：
1. 当天没时间手动去禅道点“完成任务”
2. 按某一天或某一周筛选我的任务
3. 按每个任务的预估工时补齐消耗工时，然后执行“完成任务”

注意：这里是完成任务，不是关闭任务。
"""

from zentao_ai_agent import ZendaoTool


def print_result(result: dict) -> None:
    print("=" * 80)
    print(f"筛选范围: {result['start_date']} ~ {result['end_date']}")
    print(f"筛选字段: {result['date_field']}")
    print(f"执行模式: {'演练预览' if result['dry_run'] else '实际执行'}")
    print(f"匹配任务数: {result['matched_count']}")
    print(f"成功: {result['success_count']}  跳过: {result['skipped_count']}  失败: {result['failed_count']}")
    print("=" * 80)

    for item in result["results"]:
        print(f"任务 #{item['task_id']} - {item['task_name']}")
        print(f"   状态: {item['status']}")
        print(f"   预估工时: {item.get('estimate', 'N/A')}")
        print(f"   已消耗: {item.get('current_consumed', 'N/A')}")
        print(f"   本次补录: {item.get('finish_consumed', 'N/A')}")
        if item.get("reason"):
            print(f"   原因: {item['reason']}")
        print()


def preview_and_confirm_finish(
    zendao: ZendaoTool,
    start_date: str,
    end_date: str,
    date_field: str = "range",
    comment: str = "按预估工时自动完成任务"
) -> None:
    preview_result = zendao.auto_finish_tasks_by_date(
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        comment=comment,
        dry_run=True
    )

    print("以下是将要补录并完成的任务：")
    print_result(preview_result)

    if preview_result["matched_count"] == 0:
        print("没有匹配到可处理的任务，无需执行。")
        return

    print("=" * 80)
    print("⚠️  即将按上面的补录方案填写工时并完成任务")
    print("请确认任务范围、预估工时和本次补录工时都正确")
    confirm = input(f"确认执行这 {preview_result['matched_count']} 个任务？(输入 'yes' 确认): ")

    if confirm.lower() != "yes":
        print("已取消执行")
        return

    execute_result = zendao.auto_finish_tasks_by_date(
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        comment=comment,
        dry_run=False
    )
    print("实际执行结果：")
    print_result(execute_result)


def main():
    zendao = ZendaoTool()

    if not zendao.login():
        print("登录失败")
        return

    print("登录成功")

    # 示例1：预览今天的任务，并在确认后执行
    preview_and_confirm_finish(
        zendao=zendao,
        start_date="2026-04-13",
        end_date="2026-04-27",
        date_field="range"
    )


if __name__ == "__main__":
    main()
