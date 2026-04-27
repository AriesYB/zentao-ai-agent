"""
禅道工具测试
"""

import importlib.util
import pathlib
import sys

import pytest
from zentao_ai_agent import ZendaoTool
from zentao_ai_agent.zentao import task_type_dict
from zentao_ai_agent.zentao.zendao_tool import strip_html_tags


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_SCRIPTS_DIR = ROOT / "skills" / "zentao-task-planner" / "scripts"
if str(SKILL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

LIST_TASKS_SPEC = importlib.util.spec_from_file_location(
    "skill_list_tasks",
    SKILL_SCRIPTS_DIR / "list_tasks.py",
)
skill_list_tasks = importlib.util.module_from_spec(LIST_TASKS_SPEC)
assert LIST_TASKS_SPEC.loader is not None
LIST_TASKS_SPEC.loader.exec_module(skill_list_tasks)


def test_task_type_dict():
    """测试任务类型字典"""
    assert "后端编码" in task_type_dict
    assert "前端编码" in task_type_dict
    assert task_type_dict["后端编码"] == "backendCoding"


def test_zentao_tool_init():
    """测试禅道工具初始化"""
    zendao = ZendaoTool()
    assert zendao.base_url is not None
    assert zendao.session is not None
    assert not zendao.is_logged_in


def test_strip_html_tags():
    """测试HTML标签移除"""

    html = "<p>这是一段<strong>HTML</strong>文本</p>"
    text = strip_html_tags(html)
    assert "<p>" not in text
    assert "<strong>" not in text
    assert "这是一段HTML文本" in text


def test_extract_form_data():
    html = """
    <form>
        <input type="hidden" name="uid" value="abc123">
        <input type="text" name="consumed" value="1">
        <textarea name="comment">默认备注</textarea>
        <select name="left">
            <option value="2">2</option>
            <option value="0" selected>0</option>
        </select>
    </form>
    """

    data = ZendaoTool._extract_form_data(html)
    assert data["uid"] == "abc123"
    assert data["consumed"] == "1"
    assert data["comment"] == "默认备注"
    assert data["left"] == "0"


def test_extract_form_field_names():
    html = """
    <form>
        <input type="hidden" name="uid" value="abc123">
        <input type="text" name="hoursConsumed" value="">
        <textarea name="comment"></textarea>
    </form>
    """

    field_names = ZendaoTool._extract_form_field_names(html)
    assert field_names == ["uid", "hoursConsumed", "comment"]


def test_build_finish_consumed_updates_uses_dynamic_consumed_keys():
    form_data = {
        "uid": "abc123",
        "hoursConsumed": "",
        "workConsumed": "",
    }

    updates = ZendaoTool._build_finish_consumed_updates(form_data, 4)
    assert updates["hoursConsumed"] == "4"
    assert updates["workConsumed"] == "4"


def test_filter_tasks_by_date_range():
    tasks = [
        {
            "id": 1,
            "name": "任务1",
            "status": "wait",
            "estStarted": "2026-04-08",
            "deadline": "2026-04-10",
            "closedDate": "0000-00-00 00:00:00",
        },
        {
            "id": 2,
            "name": "任务2",
            "status": "done",
            "estStarted": "2026-04-09",
            "deadline": "2026-04-09",
            "closedDate": "0000-00-00 00:00:00",
        },
        {
            "id": 3,
            "name": "任务3",
            "status": "doing",
            "estStarted": "2026-04-15",
            "deadline": "2026-04-16",
            "closedDate": "0000-00-00 00:00:00",
        },
    ]

    matched = ZendaoTool.filter_tasks_by_date(
        tasks,
        start_date="2026-04-07",
        end_date="2026-04-13",
        date_field="range",
        statuses=("wait", "doing"),
    )

    assert [task["id"] for task in matched] == [1]


def test_calculate_finish_consumed_uses_estimate_gap():
    task = {"estimate": "8", "consumed": "3.5"}
    assert ZendaoTool.calculate_finish_consumed(task) == 4.5


def test_is_task_closed_accepts_closed_status_without_closed_date():
    task = {"status": "closed", "closedDate": "0000-00-00 00:00:00"}
    assert ZendaoTool.is_task_closed(task) is True


def test_list_tasks_parser_supports_view_only():
    parser = skill_list_tasks.build_parser()
    args = parser.parse_args(["--view", "finishedBy", "--summary-only"])
    assert args.view == "finishedBy"
    assert args.summary_only is True


def test_select_tasks_returns_all_tasks_in_selected_view():
    tasks = [
        {
            "id": 1,
            "name": "待处理任务",
            "status": "wait",
            "closedDate": "0000-00-00 00:00:00",
        },
        {
            "id": 2,
            "name": "已关闭任务",
            "status": "closed",
            "closedDate": "0000-00-00 00:00:00",
        },
        {
            "id": 3,
            "name": "进行中任务",
            "status": "doing",
            "closedDate": "",
        },
    ]

    filtered = skill_list_tasks.select_tasks(
        tasks,
        summary_only=True,
    )
    assert [task["id"] for task in filtered] == [1, 2, 3]
    assert filtered[1]["closed"] is True


def test_get_my_tasks_supports_view_endpoints():
    zendao = ZendaoTool(base_url="https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"status": "success", "data": "{\"tasks\": []}"}

    def fake_post(url):
        captured["url"] = url
        return FakeResponse()

    zendao.session.post = fake_post
    result = zendao.get_my_tasks(view="assignedTo")

    assert result == {"tasks": []}
    assert captured["url"] == "https://example.com/zentao/my-task-assignedTo.json"


def test_auto_finish_tasks_by_date_dry_run():
    zendao = ZendaoTool(base_url="https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    zendao.get_my_tasks = lambda: {
        "tasks": [
            {
                "id": 101,
                "name": "今天的任务",
                "status": "doing",
                "estimate": "8",
                "consumed": "2",
                "estStarted": "2026-04-13",
                "deadline": "2026-04-13",
                "closedDate": "0000-00-00 00:00:00",
            },
            {
                "id": 102,
                "name": "没有预估工时",
                "status": "doing",
                "estimate": "0",
                "consumed": "0",
                "estStarted": "2026-04-13",
                "deadline": "2026-04-13",
                "closedDate": "0000-00-00 00:00:00",
            },
        ]
    }

    result = zendao.auto_finish_tasks_by_date(
        start_date="2026-04-13",
        dry_run=True
    )

    assert result["matched_count"] == 2
    assert result["success_count"] == 0
    assert result["skipped_count"] == 1
    assert result["results"][0]["status"] == "planned"
    assert result["results"][0]["finish_consumed"] == 6.0
    assert result["results"][1]["status"] == "skipped"


def test_finish_task_omits_consumed_when_none():
    zendao = ZendaoTool(base_url="https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    class FakeResponse:
        def __init__(self, status_code=200, text=""):
            self.status_code = status_code
            self.text = text

    captured = {}

    def fake_get(url):
        return FakeResponse(text="<input id='uid' name='uid' value='uid-123'>")

    def fake_post(url, headers=None, data=None):
        captured["data"] = data
        return FakeResponse(status_code=200)

    zendao.session.get = fake_get
    zendao.session.post = fake_post
    details = iter([
        {"id": 101, "status": "doing", "consumed": "4", "left": "1"},
        {"id": 101, "status": "done", "consumed": "4", "left": "0"},
    ])
    zendao.get_task_detail = lambda task_id: next(details)

    assert zendao.finish_task(task_id=101, consumed=None, left=0, comment="完成") is True
    assert "consumed" not in captured["data"]
    assert captured["data"]["left"] == "0"
    assert captured["data"]["comment"] == "完成"


def test_auto_finish_tasks_by_date_omits_consumed_when_gap_is_zero():
    zendao = ZendaoTool(base_url="https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    zendao.get_my_tasks = lambda: {
        "tasks": [
            {
                "id": 201,
                "name": "工时已补齐的任务",
                "status": "doing",
                "estimate": "8",
                "consumed": "8",
                "estStarted": "2026-04-13",
                "deadline": "2026-04-13",
                "closedDate": "0000-00-00 00:00:00",
            },
        ]
    }

    captured = {}

    def fake_finish_task(task_id, consumed=None, left=0, comment=""):
        captured["task_id"] = task_id
        captured["consumed"] = consumed
        captured["left"] = left
        captured["comment"] = comment
        return True

    zendao.finish_task = fake_finish_task

    result = zendao.auto_finish_tasks_by_date(
        start_date="2026-04-13",
        dry_run=False
    )

    assert result["success_count"] == 1
    assert result["results"][0]["finish_consumed"] == 0.0
    assert captured["task_id"] == 201
    assert captured["consumed"] is None
    assert captured["left"] == 0


def test_finish_task_raises_error_when_post_200_but_task_not_updated():
    zendao = ZendaoTool(base_url="https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    class FakeResponse:
        def __init__(self, status_code=200, text=""):
            self.status_code = status_code
            self.text = text

    zendao.session.get = lambda url: FakeResponse(text="<input id='uid' name='uid' value='uid-123'>")
    zendao.session.post = lambda url, headers=None, data=None: FakeResponse(status_code=200, text="validation error")
    details = iter([
        {"id": 301, "status": "doing", "consumed": "0", "left": "4"},
        {"id": 301, "status": "doing", "consumed": "0", "left": "4"},
    ])
    zendao.get_task_detail = lambda task_id: next(details)

    with pytest.raises(RuntimeError, match="validation error"):
        zendao.finish_task(task_id=301, consumed=4, left=0, comment="完成")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
