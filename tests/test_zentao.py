"""
禅道工具测试
"""

import importlib.util
import pathlib
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_SCRIPTS_DIR = ROOT / "skills" / "zentao-task-planner" / "scripts"
if str(SKILL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

ZENTAO_COMMON_SPEC = importlib.util.spec_from_file_location(
    "zentao_common",
    SKILL_SCRIPTS_DIR / "zentao_common.py",
)
zentao_common = importlib.util.module_from_spec(ZENTAO_COMMON_SPEC)
assert ZENTAO_COMMON_SPEC.loader is not None
sys.modules[ZENTAO_COMMON_SPEC.name] = zentao_common
ZENTAO_COMMON_SPEC.loader.exec_module(zentao_common)

LIST_TASKS_SPEC = importlib.util.spec_from_file_location(
    "skill_list_tasks",
    SKILL_SCRIPTS_DIR / "list_tasks.py",
)
skill_list_tasks = importlib.util.module_from_spec(LIST_TASKS_SPEC)
assert LIST_TASKS_SPEC.loader is not None
sys.modules[LIST_TASKS_SPEC.name] = skill_list_tasks
LIST_TASKS_SPEC.loader.exec_module(skill_list_tasks)

REPAIR_TASK_FINISH_DATE_SPEC = importlib.util.spec_from_file_location(
    "skill_repair_task_finish_date",
    SKILL_SCRIPTS_DIR / "repair_task_finish_date.py",
)
skill_repair_task_finish_date = importlib.util.module_from_spec(REPAIR_TASK_FINISH_DATE_SPEC)
assert REPAIR_TASK_FINISH_DATE_SPEC.loader is not None
sys.modules[REPAIR_TASK_FINISH_DATE_SPEC.name] = skill_repair_task_finish_date
REPAIR_TASK_FINISH_DATE_SPEC.loader.exec_module(skill_repair_task_finish_date)

ZentaoClient = zentao_common.ZentaoClient
ZentaoConfig = zentao_common.ZentaoConfig
TASK_TYPE_DICT = zentao_common.TASK_TYPE_DICT
strip_html_tags = zentao_common.strip_html_tags


def make_client(base_url: str = "https://example.com/zentao/") -> ZentaoClient:
    return ZentaoClient(
        ZentaoConfig(
            base_url=base_url,
            account="tester",
            password="secret",
        )
    )


def test_task_type_dict():
    """测试任务类型字典"""
    assert "后端编码" in TASK_TYPE_DICT
    assert "前端编码" in TASK_TYPE_DICT
    assert TASK_TYPE_DICT["后端编码"] == "backendCoding"


def test_zentao_tool_init():
    """测试禅道工具初始化"""
    zendao = make_client()
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

    data = ZentaoClient._extract_form_data(html)
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

    field_names = ZentaoClient._extract_form_field_names(html)
    assert field_names == ["uid", "hoursConsumed", "comment"]


def test_build_finish_consumed_updates_uses_dynamic_consumed_keys():
    form_data = {
        "uid": "abc123",
        "hoursConsumed": "",
        "workConsumed": "",
    }

    updates = ZentaoClient._build_finish_consumed_updates(form_data, 4)
    assert updates["hoursConsumed"] == "4"
    assert updates["workConsumed"] == "4"


def test_build_finish_date_updates_uses_finish_form_date_keys():
    form_data = {
        "uid": "abc123",
        "finishedDate": "2026-04-15",
        "realDate": "2026-04-15",
        "noticeDate": "2026-04-15",
    }

    updates = ZentaoClient._build_finish_date_updates(form_data, "2026-04-13")
    assert updates == {
        "finishedDate": "2026-04-13",
        "realDate": "2026-04-13",
    }


def test_build_effort_date_updates_falls_back_to_date_field():
    updates = ZentaoClient._build_effort_date_updates({"uid": "abc123"}, "2026-04-13")
    assert updates == {"date": "2026-04-13"}


def test_normalize_task_efforts_accepts_dict_and_filters_missing_id():
    efforts = ZentaoClient._normalize_task_efforts(
        {
            "efforts": {
                "1": {"id": "1", "date": "2026-04-12"},
                "missing": {"date": "2026-04-13"},
            }
        }
    )
    assert efforts == [{"id": "1", "date": "2026-04-12"}]


def test_extract_record_estimates_from_record_estimate_table():
    html = """
    <table>
        <tbody>
            <tr>
                <td>1</td>
                <td><input name="dates[1]" value="2026-04-13"></td>
                <td><input name="consumed[1]" value=""></td>
                <td><input name="left[1]" value=""></td>
            </tr>
            <tr>
                <td>452548</td>
                <td>2026-04-13</td>
                <td>4</td>
                <td>0</td>
                <td title="">完成</td>
                <td></td>
            </tr>
        </tbody>
    </table>
    """

    estimates = ZentaoClient._extract_record_estimates(html)
    assert estimates == [
        {
            "id": "452548",
            "date": "2026-04-13",
            "consumed": "4",
            "left": "0",
            "work": "完成",
        }
    ]


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

    matched = ZentaoClient.filter_tasks_by_date(
        tasks,
        start_date="2026-04-07",
        end_date="2026-04-13",
        date_field="range",
        statuses=("wait", "doing"),
    )

    assert [task["id"] for task in matched] == [1]


def test_calculate_finish_consumed_uses_estimate_gap():
    task = {"estimate": "8", "consumed": "3.5"}
    assert ZentaoClient.calculate_finish_consumed(task) == 4.5


def test_is_task_closed_accepts_closed_status_without_closed_date():
    task = {"status": "closed", "closedDate": "0000-00-00 00:00:00"}
    assert ZentaoClient.is_task_closed(task) is True


def test_list_tasks_parser_supports_view_only():
    parser = skill_list_tasks.build_parser()
    args = parser.parse_args(["--view", "finishedBy", "--summary-only"])
    assert args.view == "finishedBy"
    assert args.summary_only is True


def test_repair_task_finish_date_parser_defaults_to_preview():
    parser = skill_repair_task_finish_date.build_parser()
    args = parser.parse_args(["--task-id", "220603", "--assigned-to", "yangbiao"])
    assert args.task_id == 220603
    assert args.assigned_to == "yangbiao"
    assert args.left == 1
    assert args.execute is False


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
    zendao = make_client("https://example.com/zentao/")
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
    zendao = make_client("https://example.com/zentao/")
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
    zendao = make_client("https://example.com/zentao/")
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


def test_finish_task_posts_finish_date_when_form_has_supported_date_field():
    zendao = make_client("https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    class FakeResponse:
        def __init__(self, status_code=200, text=""):
            self.status_code = status_code
            self.text = text

    captured = {}

    def fake_get(url):
        return FakeResponse(text="""
        <form>
            <input id='uid' name='uid' value='uid-123'>
            <input name='finishedDate' value='2026-04-15'>
        </form>
        """)

    def fake_post(url, headers=None, data=None):
        captured["data"] = data
        return FakeResponse(status_code=200)

    zendao.session.get = fake_get
    zendao.session.post = fake_post
    details = iter([
        {"id": 101, "status": "doing", "consumed": "4", "left": "1"},
        {"id": 101, "status": "done", "consumed": "8", "left": "0"},
    ])
    zendao.get_task_detail = lambda task_id: next(details)

    assert zendao.finish_task(
        task_id=101,
        consumed=4,
        left=0,
        comment="完成",
        finish_date="2026-04-13",
    ) is True
    assert captured["data"]["finishedDate"] == "2026-04-13"


def test_auto_finish_tasks_by_date_omits_consumed_when_gap_is_zero():
    zendao = make_client("https://example.com/zentao/")
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

    def fake_finish_task(task_id, consumed=None, left=0, comment="", finish_date=None):
        captured["task_id"] = task_id
        captured["consumed"] = consumed
        captured["left"] = left
        captured["comment"] = comment
        captured["finish_date"] = finish_date
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
    assert captured["finish_date"] == "2026-04-13"


def test_finish_task_raises_error_when_post_200_but_task_not_updated():
    zendao = make_client("https://example.com/zentao/")
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


def test_activate_task_posts_assigned_to_left_and_uid():
    zendao = make_client("https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    class FakeResponse:
        def __init__(self, status_code=200, text=""):
            self.status_code = status_code
            self.text = text

    captured = {}

    def fake_get(url):
        captured["get_url"] = url
        return FakeResponse(text="<input id='uid' name='uid' value='uid-123'>")

    def fake_post(url, headers=None, data=None):
        captured["post_url"] = url
        captured["data"] = data
        return FakeResponse(status_code=200)

    details = iter([
        {"id": 401, "status": "done", "assignedTo": "yangbiao", "left": "0"},
        {"id": 401, "status": "doing", "assignedTo": "yangbiao", "left": "1"},
    ])

    zendao.session.get = fake_get
    zendao.session.post = fake_post
    zendao.get_task_detail = lambda task_id: next(details)

    assert zendao.activate_task(task_id=401, comment="修复") is True
    assert captured["get_url"] == "https://example.com/zentao/task-activate-401.html?onlybody=yes"
    assert captured["post_url"] == "https://example.com/zentao/task-activate-401.html?onlybody=yes"
    assert captured["data"]["assignedTo"] == "yangbiao"
    assert captured["data"]["left"] == "1"
    assert captured["data"]["comment"] == "修复"
    assert captured["data"]["uid"] == "uid-123"


def test_edit_effort_date_posts_date_fields_from_form():
    zendao = make_client("https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    class FakeResponse:
        def __init__(self, status_code=200, text=""):
            self.status_code = status_code
            self.text = text

    captured = {}

    def fake_get(url):
        captured["get_url"] = url
        return FakeResponse(text="""
        <form>
            <input id='uid' name='uid' value='uid-123'>
            <input name='date' value='2026-04-15'>
            <input name='consumed' value='8'>
            <input name='left' value='0'>
            <textarea name='work'>完成</textarea>
        </form>
        """)

    def fake_post(url, headers=None, data=None):
        captured["post_url"] = url
        captured["data"] = data
        return FakeResponse(status_code=200)

    zendao.session.get = fake_get
    zendao.session.post = fake_post

    assert zendao.edit_effort_date(effort_id=9001, effort_date="2026-04-13") is True
    assert captured["get_url"] == "https://example.com/zentao/task-editEstimate-9001.html?onlybody=yes"
    assert captured["post_url"] == "https://example.com/zentao/task-editEstimate-9001.html?onlybody=yes"
    assert captured["data"]["date"] == "2026-04-13"
    assert captured["data"]["consumed"] == "8"
    assert captured["data"]["left"] == "0"
    assert captured["data"]["work"] == "完成"
    assert captured["data"]["uid"] == "uid-123"


def test_repair_task_wrong_finish_date_uses_existing_efforts_before_activate():
    zendao = make_client("https://example.com/zentao/")
    zendao.is_logged_in = True
    zendao.session_id = "fake-session"

    calls = []
    zendao.get_task_detail = lambda task_id: {
        "id": 501,
        "name": "完成日期错误的任务",
        "deadline": "2026-04-13",
    }
    zendao.get_task_efforts = lambda task_id: [
        {"id": "11", "date": "2026-04-15"},
        {"id": "12", "date": "2026-04-15"},
    ]

    def fake_activate_task(task_id, assigned_to=None, left=1, comment=""):
        calls.append(("activate", task_id, assigned_to, left, comment))
        return True

    def fake_edit_effort_date(effort_id, effort_date):
        calls.append(("edit", effort_id, effort_date))
        return True

    zendao.activate_task = fake_activate_task
    zendao.edit_effort_date = fake_edit_effort_date

    result = zendao.repair_task_wrong_finish_date(
        task_id=501,
        assigned_to="yangbiao",
        dry_run=False,
    )

    assert result["status"] == "success"
    assert result["deadline"] == "2026-04-13"
    assert result["effort_ids"] == [11, 12]
    assert calls == [
        ("activate", 501, "yangbiao", 1, "修复任务完成日期"),
        ("edit", 11, "2026-04-13"),
        ("edit", 12, "2026-04-13"),
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
