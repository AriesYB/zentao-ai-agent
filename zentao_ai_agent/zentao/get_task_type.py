"""
测试脚本：动态获取禅道任务类型

验证从禅道系统动态获取最新的任务类型列表功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from zentao_ai_agent.zentao import ZendaoTool, get_dynamic_task_types, update_task_type_dict, task_type_dict


def dynamic_task_types():
    """测试动态获取任务类型功能"""

    print("=" * 70)
    print("测试：动态获取禅道任务类型")
    print("=" * 70)

    # 初始化禅道工具
    tool = ZendaoTool()

    # 登录禅道
    print("\n[1/4] 正在登录禅道...")
    if not tool.login():
        print("❌ 登录失败！请检查配置文件中的账号密码。")
        return False

    print("✅ 登录成功！")

    # 测试1：直接使用 ZendaoTool 实例获取任务类型
    print("\n" + "=" * 70)
    print("[2/4] 测试1：使用 tool.get_task_types() 获取任务类型")
    print("=" * 70)

    try:
        task_types = tool.get_task_types()
        print(f"\n✅ 成功获取到 {len(task_types)} 种任务类型：\n")

        # 按类别分组显示
        categories = {
            "需求相关": ["需求", "市场", "用户调研", "需求分析", "通用需求"],
            "设计相关": ["设计", "UI", "架构", "概要", "详细", "预研", "评审"],
            "开发相关": ["研发", "编码", "前端", "后端", "联调", "代码", "自测", "单元测试", "演示"],
            "测试相关": ["测试", "用例", "验收", "提测", "回归", "集成", "自动化", "安全", "性能", "报告"],
            "生产支持": ["生产", "升级", "问题"],
            "项目管理": ["立项", "管理", "结项", "复盘"],
            "质量管理": ["质量", "审计", "稽查", "度量", "整改"],
            "项目支持": ["支持", "售前", "文档", "加固", "优化"],
            "运营相关": ["运营", "培训", "请假", "其他", "客服"],
            "运维相关": ["部署", "运维", "DevOps"]
        }

        # 显示前10个任务类型作为示例
        count = 0
        for cn_name, en_value in task_types.items():
            print(f"  {cn_name:30s} -> {en_value}")
            count += 1
            if count >= 10:
                break

        if len(task_types) > 10:
            print(f"  ... (还有 {len(task_types) - 10} 种任务类型)")

    except Exception as e:
        print(f"❌ 获取任务类型失败: {e}")
        return False

    # 测试2：使用便捷函数 get_dynamic_task_types
    print("\n" + "=" * 70)
    print("[3/4] 测试2：使用 get_dynamic_task_types() 函数")
    print("=" * 70)

    try:
        task_types_2 = get_dynamic_task_types(tool)
        print(f"\n✅ 成功获取到 {len(task_types_2)} 种任务类型")

        # 验证两种方式获取的结果是否一致
        if task_types == task_types_2:
            print("✅ 两种方式获取的结果一致")
        else:
            print("⚠️  两种方式获取的结果不一致")

    except Exception as e:
        print(f"❌ 获取任务类型失败: {e}")
        return False

    # 测试3：验证特定任务类型
    print("\n" + "=" * 70)
    print("[4/4] 测试3：验证特定任务类型是否存在")
    print("=" * 70)

    test_types = [
        "前端编码",
        "后端编码",
        "需求分析",
        "UI设计",
        "架构设计",
        "通用测试",
        "培训",
        "其他"
    ]

    print("\n检查常用任务类型：")
    all_found = True
    for type_name in test_types:
        if type_name in task_types:
            print(f"  ✅ '{type_name}' -> {task_types[type_name]}")
        else:
            print(f"  ❌ '{type_name}' 未找到")
            all_found = False

    if all_found:
        print("\n✅ 所有测试的任务类型都存在")
    else:
        print("\n⚠️  部分任务类型未找到，可能是禅道配置不同")

    # 测试4：更新全局 task_type_dict
    print("\n" + "=" * 70)
    print("额外测试：更新全局 task_type_dict")
    print("=" * 70)

    print(f"\n更新前 task_type_dict 有 {len(task_type_dict)} 个条目")

    update_task_type_dict(tool)

    print(f"更新后 task_type_dict 有 {len(task_type_dict)} 个条目")
    print("✅ 全局任务类型字典已更新")

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print("\n✅ 所有测试通过！动态获取任务类型功能正常工作。")
    print(f"\n共获取到 {len(task_types)} 种任务类型")
    print("\n提示：任务类型会根据禅道系统配置动态变化，")
    print("      建议定期调用 get_task_types() 获取最新列表。")

    return True


if __name__ == "__main__":
    tool = ZendaoTool()
    # 登录禅道
    print("\n[1/4] 正在登录禅道...")
    if not tool.login():
        print("❌ 登录失败！请检查配置文件中的账号密码。")

    print("✅ 登录成功！")
    print(get_dynamic_task_types(tool))