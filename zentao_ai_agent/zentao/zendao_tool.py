"""
禅道API客户端模块
提供与禅道系统交互的完整功能
"""

import json
import uuid
import re
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Iterable
import requests
from bs4 import BeautifulSoup

from ..utils.config import config
from .task_types import task_type_dict


def strip_html_tags(html_text: str) -> str:
    """
    移除HTML标签，只保留纯文本

    Args:
        html_text: 包含HTML标签的文本

    Returns:
        str: 纯文本
    """
    if not html_text:
        return ""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', html_text)
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class ZendaoTool:
    """禅道工具类，用于登录禅道并获取相关信息"""

    def __init__(self, base_url: Optional[str] = None):
        """
        初始化禅道工具

        Args:
            base_url: 禅道基础地址，默认从环境变量读取
        """
        if base_url is None:
            self.base_url = config.zentao_base_url.rstrip('/') + '/'
        else:
            self.base_url = base_url.rstrip('/') + '/'
        self.session = requests.Session()
        self.session_id = None
        self.is_logged_in = False

    def login(self, account: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        登录禅道

        Args:
            account: 用户名，默认从环境变量读取
            password: 密码，默认从环境变量读取

        Returns:
            bool: 登录是否成功
        """
        # 如果没有提供账号密码，则从环境变量读取
        if account is None:
            account = config.zentao_account
        if password is None:
            password = config.zentao_password
        url = f"{self.base_url}user-login.json"
        params = {
            'account': account,
            'password': password
        }

        try:
            response = self.session.post(url, params=params)

            # 检查HTTP状态码
            if response.status_code != 200:
                return False

            # 解析响应JSON
            response_data = response.json()

            # 检查登录状态
            if response_data.get('status') != 'success':
                return False

            # 获取会话ID
            self.session_id = response.cookies.get('zentaosid')
            if not self.session_id:
                return False

            self.is_logged_in = True
            return True

        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def _ensure_logged_in(self) -> bool:
        """确保已登录"""
        if not self.is_logged_in or not self.session_id:
            raise ValueError("请先登录禅道")
        return True

    def _parse_response_data(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析禅道API响应数据

        Args:
            response: HTTP响应对象

        Returns:
            Dict: 解析后的数据
        """
        if response.status_code != 200:
            raise ValueError(f"请求失败，状态码: {response.status_code}")

        outer_data = response.json()

        if outer_data.get('status') != 'success':
            raise ValueError(f"API返回失败: {outer_data.get('reason', '未知错误')}")

        # 二次解析data字段
        data_str = outer_data.get('data', '{}')
        try:
            inner_data = json.loads(data_str)
            return inner_data
        except json.JSONDecodeError as e:
            raise ValueError(f"解析响应数据失败: {e}")

    def get_assigned_stories(self) -> Dict[str, Any]:
        """
        获取指派给我的需求列表

        Returns:
            Dict: 需求列表数据
        """
        self._ensure_logged_in()

        url = f"{self.base_url}my-story-assignedTo.json"

        response = self.session.post(url)
        return self._parse_response_data(response)

    def get_story_detail(self, story_id: int) -> Dict[str, Any]:
        """
        获取需求详情

        Args:
            story_id: 需求ID

        Returns:
            Dict: 需求详情数据
        """
        self._ensure_logged_in()

        url = f"{self.base_url}story-view-{story_id}.json"

        response = self.session.post(url)
        data = self._parse_response_data(response)
        return data.get('story', {})

    def get_doing_projects(self) -> List[Dict[str, Any]]:
        """
        获取进行中的项目列表

        Returns:
            List[Dict]: 项目列表
        """
        self._ensure_logged_in()

        url = f"{self.base_url}project-all-doing-order_desc-0.json"

        response = self.session.post(url)
        data = self._parse_response_data(response)
        return data.get('projectStats', [])

    def get_project_stories(self, project_id: int, page_size: int = 200) -> List[Dict[str, Any]]:
        """
        按项目获取需求列表

        Args:
            project_id: 项目ID
            page_size: 分页大小，默认200

        Returns:
            List[Dict]: 需求列表
        """
        self._ensure_logged_in()

        url = f"{self.base_url}project-story-{project_id}.json"

        # 设置分页大小
        cookies = self.session.cookies
        cookies.set('pagerProjectStory', str(page_size))

        response = self.session.post(url, cookies=cookies)
        data = self._parse_response_data(response)

        # stories可能是字典结构，需要转换为列表
        stories = data.get('stories', {})
        if isinstance(stories, dict):
            return list(stories.values())
        return stories if isinstance(stories, list) else []

    def assign_story(self, story_id: int, assigned_to: str, comment: str = "") -> bool:
        """
        指派需求到用户

        Args:
            story_id: 需求ID
            assigned_to: 被指派用户（系统用户名）
            comment: 备注说明

        Returns:
            bool: 是否成功
        """
        self._ensure_logged_in()

        url = f"{self.base_url}story-assignTo-{story_id}.json?onlybody=yes"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': url,
            'Origin': self.base_url.rstrip('/'),
            'Connection': 'keep-alive'
        }

        data = {
            'assignedTo': assigned_to,
            'comment': comment,
            'uid': str(uuid.uuid4())
        }

        response = self.session.post(url, headers=headers, data=data)
        return response.status_code == 200

    def add_story_comment(self, story_id: int, comment: str) -> bool:
        """
        为需求添加备注

        Args:
            story_id: 需求ID
            comment: 备注内容

        Returns:
            bool: 是否成功
        """
        self._ensure_logged_in()

        url = f"{self.base_url}action-comment-story-{story_id}.html"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': url,
            'Origin': self.base_url.rstrip('/'),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        data = {
            'comment': comment,
            'uid': str(uuid.uuid4())
        }

        response = self.session.post(url, headers=headers, data=data)
        return response.status_code == 200

    def get_user_list(self) -> Dict[str, str]:
        """
        获取用户列表

        Returns:
            Dict: 用户字典，键为用户名拼音，值为中文名
        """
        self._ensure_logged_in()

        url = f"{self.base_url}my-managecontacts.json"

        response = self.session.post(url)
        data = self._parse_response_data(response)
        return data.get('users', {})

    def get_my_tasks(self) -> Dict[str, Any]:
        """
        获取我的任务列表

        Returns:
            Dict: 任务列表数据
        """
        self._ensure_logged_in()

        url = f"{self.base_url}my-task.json"

        response = self.session.post(url)
        return self._parse_response_data(response)

    @staticmethod
    def _normalize_task_list(tasks: Any) -> List[Dict[str, Any]]:
        """
        将禅道返回的任务列表标准化为列表结构
        """
        if isinstance(tasks, list):
            return tasks
        if isinstance(tasks, dict):
            return list(tasks.values())
        return []

    @staticmethod
    def _parse_date_value(value: Any) -> Optional[date]:
        """
        解析禅道日期字段
        """
        if value is None:
            return None

        text = str(value).strip()
        if not text or text.startswith("0000-00-00"):
            return None

        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_float_value(value: Any, default: float = 0.0) -> float:
        """
        解析工时字段
        """
        if value is None:
            return default
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return default

    @classmethod
    def filter_tasks_by_date(cls, tasks: Any, start_date: str, end_date: Optional[str] = None,
                             date_field: str = "range", statuses: Optional[Iterable[str]] = None,
                             exclude_closed: bool = True) -> List[Dict[str, Any]]:
        """
        按日期范围筛选任务

        Args:
            tasks: 禅道任务列表，支持 list 或 dict
            start_date: 开始日期，格式 YYYY-MM-DD / YYYY/MM/DD
            end_date: 结束日期，默认等于 start_date
            date_field: 筛选字段，可选 estStarted / deadline / range
            statuses: 限定状态列表，默认不过滤
            exclude_closed: 是否排除已关闭任务
        """
        start = cls._parse_date_value(start_date)
        end = cls._parse_date_value(end_date or start_date)
        if not start or not end:
            raise ValueError("start_date 和 end_date 必须是有效日期")
        if start > end:
            start, end = end, start

        allowed_statuses = set(statuses) if statuses else None
        matched_tasks = []

        for task in cls._normalize_task_list(tasks):
            status = task.get("status")
            if allowed_statuses and status not in allowed_statuses:
                continue

            if exclude_closed and cls._parse_date_value(task.get("closedDate")) is not None:
                continue

            est_started = cls._parse_date_value(task.get("estStarted"))
            deadline = cls._parse_date_value(task.get("deadline"))

            if date_field == "estStarted":
                matched = est_started is not None and start <= est_started <= end
            elif date_field == "deadline":
                matched = deadline is not None and start <= deadline <= end
            elif date_field == "range":
                if est_started is None and deadline is None:
                    matched = False
                else:
                    task_start = est_started or deadline
                    task_end = deadline or est_started
                    matched = task_start <= end and task_end >= start
            else:
                raise ValueError("date_field 仅支持 estStarted、deadline、range")

            if matched:
                matched_tasks.append(task)

        return matched_tasks

    @classmethod
    def calculate_finish_consumed(cls, task: Dict[str, Any]) -> float:
        """
        计算完成任务时需要补录的工时

        规则：将累计消耗补齐到预估工时；若已经超过预估工时，则不再补录。
        """
        estimate = cls._parse_float_value(task.get("estimate"))
        consumed = cls._parse_float_value(task.get("consumed"))
        return max(0.0, estimate - consumed)

    @staticmethod
    def _format_hour_value(value: float) -> str:
        """
        将工时格式化为禅道表单需要的字符串
        """
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _is_finished_task_detail(task_detail: Dict[str, Any]) -> bool:
        """
        根据任务详情判断任务是否已进入完成态
        """
        status = str(task_detail.get("status", "")).strip().lower()
        if status in {"done", "closed"}:
            return True

        finished_by = str(task_detail.get("finishedBy", "")).strip()
        finished_date = str(task_detail.get("finishedDate", "")).strip()
        return bool(finished_by) and finished_by != "0" and not finished_date.startswith("0000-00-00")

    @staticmethod
    def _extract_submit_error(response_text: str) -> str:
        """
        从禅道表单提交响应中尽量提取错误信息
        """
        if not response_text:
            return "提交后任务状态和工时都没有变化"

        patterns = [
            r"alert\(['\"](.+?)['\"]\)",
            r'"message"\s*:\s*"(.+?)"',
            r'"reason"\s*:\s*"(.+?)"',
            r"<div[^>]*class=['\"][^'\"]*alert[^'\"]*['\"][^>]*>(.*?)</div>",
            r"<td[^>]*class=['\"][^'\"]*message[^'\"]*['\"][^>]*>(.*?)</td>",
        ]
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                message = strip_html_tags(match.group(1)).strip()
                if message:
                    return message

        plain_text = strip_html_tags(response_text).strip()
        if plain_text:
            return plain_text[:200]
        return "提交后任务状态和工时都没有变化"

    @staticmethod
    def _extract_form_data(response_text: str) -> Dict[str, str]:
        """
        从HTML表单中提取默认字段值
        """
        soup = BeautifulSoup(response_text, 'html.parser')
        form = soup.find('form')
        if not form:
            return {}

        form_data: Dict[str, str] = {}

        for field in form.find_all(['input', 'textarea', 'select']):
            name = field.get('name')
            if not name:
                continue

            tag_name = field.name.lower()
            field_type = str(field.get('type', '')).lower()

            if tag_name == 'input':
                if field_type in {'checkbox', 'radio'} and not field.has_attr('checked'):
                    continue
                form_data[name] = field.get('value', '')
            elif tag_name == 'textarea':
                form_data[name] = field.get_text()
            elif tag_name == 'select':
                selected_option = field.find('option', selected=True)
                if selected_option is None:
                    selected_option = field.find('option')
                form_data[name] = selected_option.get('value', '') if selected_option else ''

        return form_data

    @staticmethod
    def _extract_form_field_names(response_text: str) -> List[str]:
        """
        提取页面表单中的字段名，便于排查动态字段
        """
        soup = BeautifulSoup(response_text, 'html.parser')
        field_names: List[str] = []
        for field in soup.find_all(['input', 'textarea', 'select']):
            name = field.get('name')
            if name:
                field_names.append(name)
        return field_names

    @classmethod
    def _build_finish_consumed_updates(cls, form_data: Dict[str, str], consumed: Optional[float]) -> Dict[str, str]:
        """
        根据完成任务页面的实际字段名，生成“本次消耗”更新字段
        """
        if consumed is None:
            return {}

        consumed_value = cls._format_hour_value(consumed)
        updates: Dict[str, str] = {}
        candidate_keys = [key for key in form_data.keys() if 'consumed' in key.lower()]

        if 'consumed' in form_data:
            updates['consumed'] = consumed_value

        for key in candidate_keys:
            updates[key] = consumed_value

        if not updates:
            updates['consumed'] = consumed_value

        return updates

    def create_task_from_story(self, story_id: int, task_type: str, task_name: str,
                           assigned_to: str, estimate: int = 1, priority: int = 3,
                           est_started: str = None, deadline: str = None,
                           test_stories: List[int] = None, project_id: int = None) -> Dict[str, Any]:
        """
        从需求详情创建任务

        Args:
            story_id: 需求ID
            task_type: 任务类型 (如: training, devel等)
            task_name: 任务名称
            assigned_to: 指派给谁 (用户名)
            estimate: 预估工时，默认为1
            priority: 优先级，默认为3
            est_started: 开始日期，格式: YYYY-MM-DD
            deadline: 截止日期，格式: YYYY-MM-DD
            test_stories: 测试需求ID列表
            project_id: 项目ID，如果不提供则从需求详情中获取

        Returns:
            str: 创建任务的响应内容

        Raises:
            ValueError: 当无法获取需求详情、模块ID或项目ID时抛出
        """
        self._ensure_logged_in()

        # 获取需求详情
        story_detail = self.get_story_detail(story_id)
        if not story_detail:
            raise ValueError(f'无法获取需求 {story_id} 的详情')

        # 从需求详情中获取必要信息
        module_id = story_detail.get('module')
        if not module_id:
            raise ValueError(f'无法从需求 {story_id} 的详情中获取模块ID')

        # 确保 module_id 是整数
        try:
            module_id = int(module_id)
        except (ValueError, TypeError):
            raise ValueError(f'模块ID格式错误: {module_id}')

        if not project_id:
            # 从需求详情的projects字段中获取项目ID
            projects = story_detail.get('projects', {})
            if projects:
                project_id = list(projects.keys())[0]  # 取第一个项目ID
                # 确保 project_id 是整数
                try:
                    project_id = int(project_id)
                except (ValueError, TypeError):
                    raise ValueError(f'项目ID格式错误: {project_id}')
            else:
                raise ValueError('无法从需求详情中获取项目ID')

        # 获取需求描述作为任务描述，并移除HTML标签
        description = strip_html_tags(story_detail.get('spec', ''))

        # 调用内部创建任务方法
        return self._create_task(
            project_id=int(project_id),
            story_id=story_id,
            module_id=int(module_id),
            task_type=task_type,
            name=task_name,
            description=description,
            assigned_to=assigned_to,
            estimate=estimate,
            priority=priority,
            est_started=est_started,
            deadline=deadline,
            test_stories=test_stories
        )

    def create_task(self, project_id: int, story_id: int, module_id: int, task_type: str,
                  name: str, description: str, assigned_to: str, estimate: int = 1,
                  priority: int = 3, est_started: str = None, deadline: str = None,
                  test_stories: List[int] = None) -> Dict[str, Any]:
        """
        创建任务

        Args:
            project_id: 项目ID
            story_id: 需求ID
            module_id: 模块ID
            task_type: 任务类型 (如: training, devel等)
            name: 任务名称
            description: 任务描述
            assigned_to: 指派给谁 (用户名)
            estimate: 预估工时，默认为1
            priority: 优先级，默认为3
            est_started: 开始日期，格式: YYYY-MM-DD
            deadline: 截止日期，格式: YYYY-MM-DD
            test_stories: 测试需求ID列表

        Returns:
            Dict: 创建结果
        """
        return self._create_task(
            project_id=project_id,
            story_id=story_id,
            module_id=module_id,
            task_type=task_type,
            name=name,
            description=description,
            assigned_to=assigned_to,
            estimate=estimate,
            priority=priority,
            est_started=est_started,
            deadline=deadline,
            test_stories=test_stories
        )

    def _create_task(self, project_id: int, story_id: int, module_id: int, task_type: str,
                   name: str, description: str, assigned_to: str, estimate: int = 1,
                   priority: int = 3, est_started: str = None, deadline: str = None,
                   test_stories: List[int] = None) -> Dict[str, Any]:
        """
        内部创建任务方法

        Args:
            project_id: 项目ID
            story_id: 需求ID
            module_id: 模块ID
            task_type: 任务类型 (如: training, devel等)
            name: 任务名称
            description: 任务描述
            assigned_to: 指派给谁 (用户名)
            estimate: 预估工时，默认为1
            priority: 优先级，默认为3
            est_started: 开始日期，格式: YYYY-MM-DD
            deadline: 截止日期，格式: YYYY-MM-DD
            test_stories: 测试需求ID列表

        Returns:
            Dict: 创建结果
        """
        # 构建URL
        url = f"{self.base_url}task-create-{project_id}-{story_id}-{module_id}.html"

        # 设置默认日期
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        if not est_started:
            est_started = today
        if not deadline:
            deadline = today

        # 构建表单数据 - 清理HTML标签以避免WAF拦截
        data = {
            'functionEstimates': '{}',
            'project': str(project_id),
            'story': str(story_id),
            'module[]': str(module_id),
            'type': task_type,
            'estimate': str(estimate),
            'estStarted': est_started,
            'deadline': deadline,
            'assignedTo[]': assigned_to,
            'name': strip_html_tags(name),
            'desc': strip_html_tags(description),
            'pri': str(priority),
            'storyEstimate': '0',
            'storyPri': '1',
            'color': '',
            'labels[]': '',
            'files[]': '',
            'mailto[]': '',
            'after': 'continueAdding',
            'uid': str(uuid.uuid4()),
            'team[]': '',
            'teamEstimate[]': '',
            'functionMapping': '{}'
        }

        # 添加测试需求
        if test_stories:
            for i, test_story_id in enumerate(test_stories):
                data[f'testStory[]'] = str(test_story_id)
                data[f'testPri[]'] = '3'
                data[f'testEstStarted[]'] = ''
                data[f'testDeadline[]'] = ''
                data[f'testAssignedTo[]'] = assigned_to
                data[f'testEstimate[]'] = ''

        # 设置请求头 - 添加完整的浏览器特征以避免WAF拦截
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': self.base_url.rstrip('/'),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        response = self.session.post(url, headers=headers, data=data)

        if response.status_code != 200:
            print(response.text)
            raise RuntimeError(f'请求失败，状态码: {response.status_code}')

        return response.text

    def get_task_detail(self, task_id: int) -> Dict[str, Any]:
        """
        获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            Dict: 任务详情数据
        """
        self._ensure_logged_in()

        url = f"{self.base_url}task-view-{task_id}.json"

        response = self.session.post(url)
        data = self._parse_response_data(response)
        return data.get('task', {})

    def update_task(self, task_id: int, name: str = None, description: str = None,
                  assigned_to: str = None, task_type: str = None, status: str = None,
                  priority: int = None, est_started: str = None, deadline: str = None,
                  estimate: int = None, left: int = None, comment: str = None) -> Dict[str, Any]:
        """
        修改任务

        Args:
            task_id: 任务ID
            name: 任务名称
            description: 任务描述
            assigned_to: 指派给谁 (用户名)
            task_type: 任务类型 (如: training, devel等)
            status: 任务状态 (如: wait, doing, done等)
            priority: 优先级
            est_started: 开始日期，格式: YYYY-MM-DD
            deadline: 截止日期，格式: YYYY-MM-DD
            estimate: 预估工时
            left: 剩余工时
            comment: 修改备注

        Returns:
            Dict: 修改结果
        """
        self._ensure_logged_in()

        # 获取任务详情，用于填充未提供的字段
        task_detail = self.get_task_detail(task_id)
        if not task_detail:
            return {'success': False, 'message': f'无法获取任务 {task_id} 的详情'}

        # 构建URL
        url = f"{self.base_url}task-edit-{task_id}.html"

        # 构建表单数据 - 清理HTML标签以避免WAF拦截
        data = {
            'color': task_detail.get('color', ''),
            'name': strip_html_tags(name if name is not None else task_detail.get('name', '')),
            'desc': strip_html_tags(description if description is not None else task_detail.get('desc', '')),
            'comment': strip_html_tags(comment if comment is not None else ''),
            'labels[]': '',
            'files[]': '',
            'lastEditedDate': task_detail.get('lastEditedDate', ''),
            'consumed': task_detail.get('consumed', '0'),
            'uid': str(uuid.uuid4()),
            'project': task_detail.get('project', ''),
            'module': task_detail.get('module', '0'),
            'story': task_detail.get('story', ''),
            'parent': task_detail.get('parent', ''),
            'assignedTo': assigned_to if assigned_to is not None else task_detail.get('assignedTo', ''),
            'type': task_type if task_type is not None else task_detail.get('type', ''),
            'status': status if status is not None else task_detail.get('status', ''),
            'pri': str(priority if priority is not None else task_detail.get('pri', '3')),
            'mailto[]': '',
            'estStarted': est_started if est_started is not None else task_detail.get('estStarted', ''),
            'deadline': deadline if deadline is not None else task_detail.get('deadline', ''),
            'estimate': str(estimate if estimate is not None else task_detail.get('estimate', '0')),
            'left': str(left if left is not None else task_detail.get('left', '0')),
            'realStarted': task_detail.get('realStarted', '0000-00-00'),
            'finishedBy': task_detail.get('finishedBy', ''),
            'finishedDate': task_detail.get('finishedDate', ''),
            'canceledBy': task_detail.get('canceledBy', ''),
            'canceledDate': task_detail.get('canceledDate', ''),
            'closedBy': task_detail.get('closedBy', ''),
            'closedReason': task_detail.get('closedReason', ''),
            'closedDate': task_detail.get('closedDate', ''),
            'funcIds[]': 'new',
            'functionModule[new]': '0',
            'functionPoints[new]': '',
            'functionType[new]': '新增',
            'functionDesc[new]': '',
            'timeConsumed[new][规划]': '',
            'timeOwner[new][规划]': '',
            'timeStartDate[new][规划]': '',
            'timeEndDate[new][规划]': '',
            'timeConsumed[new][需求]': '',
            'timeOwner[new][需求]': '',
            'timeStartDate[new][需求]': '',
            'timeEndDate[new][需求]': '',
            'timeConsumed[new][UI]': '',
            'timeOwner[new][UI]': '',
            'timeStartDate[new][UI]': '',
            'timeEndDate[new][UI]': '',
            'timeConsumed[new][后端]': '',
            'timeOwner[new][后端]': '',
            'timeStartDate[new][后端]': '',
            'timeEndDate[new][后端]': '',
            'timeConsumed[new][前端]': '',
            'timeOwner[new][前端]': '',
            'timeStartDate[new][前端]': '',
            'timeEndDate[new][前端]': '',
            'timeConsumed[new][测试]': '',
            'timeOwner[new][测试]': '',
            'timeStartDate[new][测试]': '',
            'timeEndDate[new][测试]': '',
            'docs': '[]',
            'team[]': '',
            'teamEstimate[]': '',
            'teamConsumed[]': '',
            'teamLeft[]': ''
        }

        # 设置请求头 - 添加完整的浏览器特征以避免WAF拦截
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': self.base_url.rstrip('/'),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        response = self.session.post(url, headers=headers, data=data)

        if response.status_code != 200:
            return {'success': False, 'message': f'请求失败，状态码: {response.status_code}'}

        # 尝试解析响应
        return response.text

    def batch_create_tasks_from_text(self, text_data: str, username_mapping: Dict[str, str] = None, execute_create: bool = False) -> Dict[str, Any]:
        """
        从文本数据批量创建任务（带验证）

        Args:
            text_data: 文本数据，每行格式：人员姓名\t需求编号\t任务名称（功能点）\t任务类型\t预计工时（小时）\t预计开始\t预计结束
            username_mapping: 用户名映射字典，键为中文名，值为系统用户名
            execute_create: 是否立即执行创建，默认为False（仅验证，不创建）

        Returns:
            Dict: 包含验证结果和创建结果
                {
                    'validation_passed': bool,  # 是否通过验证
                    'validation_errors': List[str],  # 验证错误列表
                    'tasks_to_create': List[Dict],  # 待创建任务列表
                    'create_results': List[Dict]  # 创建结果列表（仅在execute_create=True且验证通过后执行）
                }
        """
        # 默认用户名映射
        if username_mapping is None:
            username_mapping = {}

        validation_errors = []
        tasks_to_create = []

        # 第一步：解析和验证所有数据
        lines = text_data.strip().split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 按制表符分割
            parts = line.split('\t')
            if len(parts) < 7:
                validation_errors.append(f'第{line_num}行: 数据格式错误，需要7列数据')
                continue

            chinese_name = parts[0].strip()
            story_id_str = parts[1].strip()
            task_name = parts[2].strip()
            task_type_cn = parts[3].strip()
            estimate_str = parts[4].strip()
            est_started = parts[5].strip()
            deadline = parts[6].strip()

            # 验证用户名映射
            if chinese_name not in username_mapping:
                validation_errors.append(f'第{line_num}行: 用户名"{chinese_name}"未在映射表中找到')
                continue

            # 验证需求ID格式
            try:
                story_id = int(story_id_str)
            except ValueError:
                validation_errors.append(f'第{line_num}行: 需求ID"{story_id_str}"格式错误')
                continue

            # 验证需求是否存在
            story_detail = self.get_story_detail(story_id)
            if not story_detail:
                validation_errors.append(f'第{line_num}行: 需求ID {story_id} 不存在或无法获取详情')
                continue

            # 验证任务类型
            task_type = task_type_dict.get(task_type_cn)
            if not task_type:
                validation_errors.append(f'第{line_num}行: 任务类型"{task_type_cn}"无效')
                continue

            # 验证预估工时
            try:
                estimate = int(estimate_str)
                if estimate <= 0:
                    validation_errors.append(f'第{line_num}行: 预估工时必须大于0')
                    continue
            except ValueError:
                validation_errors.append(f'第{line_num}行: 预估工时"{estimate_str}"格式错误')
                continue

            # 验证日期格式
            try:
                est_started = est_started.replace('/', '-')
                deadline = deadline.replace('/', '-')
                # 简单验证日期格式 YYYY-MM-DD
                from datetime import datetime
                datetime.strptime(est_started, '%Y-%m-%d')
                datetime.strptime(deadline, '%Y-%m-%d')
            except ValueError:
                validation_errors.append(f'第{line_num}行: 日期格式错误，应为YYYY/MM/DD或YYYY-MM-DD')
                continue

            # 验证任务名称
            if not task_name:
                validation_errors.append(f'第{line_num}行: 任务名称不能为空')
                continue

            # 所有验证通过，添加到待创建列表
            tasks_to_create.append({
                'line_num': line_num,
                'chinese_name': chinese_name,
                'assigned_to': username_mapping[chinese_name],
                'story_id': story_id,
                'task_name': task_name,
                'task_type': task_type,
                'task_type_cn': task_type_cn,
                'estimate': estimate,
                'est_started': est_started,
                'deadline': deadline
            })

        # 如果有验证错误，返回错误信息
        if validation_errors:
            return {
                'validation_passed': False,
                'validation_errors': validation_errors,
                'tasks_to_create': tasks_to_create,
                'create_results': []
            }

        # 如果execute_create为False，仅返回验证结果，不执行创建
        if not execute_create:
            return {
                'validation_passed': True,
                'validation_errors': [],
                'tasks_to_create': tasks_to_create,
                'create_results': []
            }

        # 第二步：批量创建任务（仅在execute_create=True时执行）
        create_results = []
        for task in tasks_to_create:
            result = self.create_task_from_story(
                story_id=task['story_id'],
                task_type=task['task_type'],
                task_name=task['task_name'],
                assigned_to=task['assigned_to'],
                estimate=task['estimate'],
                priority=3,
                est_started=task['est_started'],
                deadline=task['deadline']
            )

            create_results.append({
                'line_num': task['line_num'],
                'task_name': task['task_name'],
                'story_id': task['story_id'],
                'assigned_to': task['assigned_to'],
                'result': result
            })

        return {
            'validation_passed': True,
            'validation_errors': [],
            'tasks_to_create': tasks_to_create,
            'create_results': create_results
        }

    def close_task(self, task_id: int, comment: str = "") -> bool:
        """
        关闭禅道任务

        Args:
            task_id: 任务ID
            comment: 关闭备注（可选）

        Returns:
            bool: 是否成功关闭

        Raises:
            ValueError: 当无法提取uid参数时抛出
        """
        self._ensure_logged_in()

        # 步骤1：获取关闭任务表单页面
        url = f"{self.base_url}task-close-{task_id}.html?onlybody=yes"
        response = self.session.get(url)

        if response.status_code != 200:
            raise RuntimeError(f'获取关闭任务页面失败，状态码: {response.status_code}')

        # 步骤2：从响应中提取uid
        # 方法A：使用正则表达式
        uid_match = re.search(r"var kuid = '([a-f0-9]+)';", response.text)
        if not uid_match:
            # 方法B：使用BeautifulSoup查找隐藏字段
            soup = BeautifulSoup(response.text, 'html.parser')
            uid_input = soup.find('input', {'id': 'uid', 'name': 'uid'})
            if uid_input:
                uid = uid_input.get('value')
            else:
                raise ValueError(f"无法提取uid参数，任务ID: {task_id}")
        else:
            uid = uid_match.group(1)

        # 步骤3：提交关闭任务请求
        post_data = {
            'comment': comment,
            'uid': uid
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': url,
            'Origin': self.base_url.rstrip('/'),
            'Connection': 'keep-alive'
        }

        response = self.session.post(url, headers=headers, data=post_data)

        return response.status_code == 200

    def finish_task(self, task_id: int, consumed: Optional[float] = None, left: float = 0,
                    comment: str = "") -> bool:
        """
        完成禅道任务（不是关闭）

        Args:
            task_id: 任务ID
            consumed: 本次填写的消耗工时；传 None 时不提交该字段
            left: 剩余工时，完成任务时通常为0
            comment: 完成备注
        """
        self._ensure_logged_in()
        before_detail = self.get_task_detail(task_id)

        url = f"{self.base_url}task-finish-{task_id}.html?onlybody=yes"
        response = self.session.get(url)

        if response.status_code != 200:
            raise RuntimeError(f'获取完成任务页面失败，状态码: {response.status_code}')

        post_data = self._extract_form_data(response.text)
        uid_match = re.search(r"var kuid = '([a-f0-9]+)';", response.text)
        if not uid_match:
            soup = BeautifulSoup(response.text, 'html.parser')
            uid_input = soup.find('input', {'id': 'uid', 'name': 'uid'})
            if uid_input:
                uid = uid_input.get('value')
            else:
                raise ValueError(f"无法提取uid参数，任务ID: {task_id}")
        else:
            uid = uid_match.group(1)

        post_data['left'] = self._format_hour_value(left)
        post_data['comment'] = comment
        post_data['uid'] = uid
        post_data.update(self._build_finish_consumed_updates(post_data, consumed))

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': url,
            'Origin': self.base_url.rstrip('/'),
            'Connection': 'keep-alive'
        }

        response = self.session.post(url, headers=headers, data=post_data)
        if response.status_code != 200:
            raise RuntimeError(f"完成任务请求失败，状态码: {response.status_code}")

        after_detail = self.get_task_detail(task_id)
        if self._is_finished_task_detail(after_detail):
            return True

        before_consumed = self._parse_float_value(before_detail.get("consumed"))
        after_consumed = self._parse_float_value(after_detail.get("consumed"))
        after_left = self._parse_float_value(after_detail.get("left"))

        if consumed is not None and after_consumed >= before_consumed + consumed and after_left == float(left):
            return True

        if consumed is None and after_left == float(left):
            return True

        field_names = self._extract_form_field_names(response.text)
        consumed_fields = [name for name in field_names if 'consumed' in name.lower()]
        debug_parts = []
        if consumed_fields:
            debug_parts.append(f"页面工时字段: {', '.join(consumed_fields)}")
        elif field_names:
            debug_parts.append(f"页面字段: {', '.join(field_names[:20])}")
        debug_suffix = f"；{'；'.join(debug_parts)}" if debug_parts else ""
        raise RuntimeError(f"{self._extract_submit_error(response.text)}{debug_suffix}")

    def auto_finish_tasks_by_date(self, start_date: str, end_date: Optional[str] = None,
                                  date_field: str = "range",
                                  statuses: Optional[Iterable[str]] = None,
                                  comment: str = "按预估工时自动完成任务",
                                  dry_run: bool = True) -> Dict[str, Any]:
        """
        按日期筛选任务，并按预估工时自动补录后完成任务

        规则：
        1. 仅处理未关闭任务
        2. 仅处理状态在 statuses 中的任务，默认 wait / doing / pause
        3. 本次填写工时 = max(预估工时 - 已消耗工时, 0)
        4. 完成任务时剩余工时置为 0
        """
        self._ensure_logged_in()

        statuses = tuple(statuses or ("wait", "doing", "pause"))
        tasks_data = self.get_my_tasks()
        task_list = self._normalize_task_list(tasks_data.get('tasks', []))
        matched_tasks = self.filter_tasks_by_date(
            task_list,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field,
            statuses=statuses,
            exclude_closed=True
        )

        results = []
        success_count = 0
        skipped_count = 0
        failed_count = 0

        for task in matched_tasks:
            task_id = task.get('id')
            estimate = self._parse_float_value(task.get('estimate'))
            current_consumed = self._parse_float_value(task.get('consumed'))
            finish_consumed = self.calculate_finish_consumed(task)

            if estimate <= 0:
                results.append({
                    'task_id': task_id,
                    'task_name': task.get('name'),
                    'status': 'skipped',
                    'reason': '预估工时为空或小于等于0，无法按预估工时自动完成'
                })
                skipped_count += 1
                continue

            result_item = {
                'task_id': task_id,
                'task_name': task.get('name'),
                'matched_by': date_field,
                'estimate': estimate,
                'current_consumed': current_consumed,
                'finish_consumed': finish_consumed,
                'left': 0
            }

            if dry_run:
                result_item['status'] = 'planned'
                results.append(result_item)
                continue

            try:
                success = self.finish_task(
                    task_id=task_id,
                    consumed=finish_consumed if finish_consumed > 0 else None,
                    left=0,
                    comment=comment
                )
                result_item['status'] = 'success' if success else 'failed'
                results.append(result_item)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                result_item['status'] = 'failed'
                result_item['reason'] = str(e)
                results.append(result_item)
                failed_count += 1

        return {
            'start_date': start_date,
            'end_date': end_date or start_date,
            'date_field': date_field,
            'dry_run': dry_run,
            'matched_count': len(matched_tasks),
            'success_count': success_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
            'results': results
        }

    def get_task_types(self, project_id: int = None, story_id: int = None, module_id: int = None) -> Dict[str, str]:
        """
        动态获取禅道任务类型列表
        
        通过访问创建任务页面，解析HTML中的任务类型下拉选项，获取最新的任务类型映射。
        
        Args:
            project_id: 项目ID（可选，用于构建完整的创建任务页面URL）
            story_id: 需求ID（可选）
            module_id: 模块ID（可选）
            
        Returns:
            Dict[str, str]: 任务类型字典，键为中文名称，值为英文类型值
                          例如: {"前端编码": "frontendCoding", "后端编码": "backendCoding"}
        
        Raises:
            ValueError: 当未登录或无法解析任务类型时抛出
        """
        self._ensure_logged_in()
        
        # 构建创建任务页面URL
        # 如果提供了完整参数，使用完整URL；否则使用一个简化的URL
        if project_id and story_id and module_id:
            url = f"{self.base_url}task-create-{project_id}-{story_id}-{module_id}.html"
        else:
            # 尝试获取一个进行中的项目来构建URL
            projects = self.get_doing_projects()
            if not projects:
                raise ValueError("无法获取进行中的项目，请提供 project_id, story_id 和 module_id 参数")
            
            project = projects[0]
            project_id = project.get('id')
            if not project_id:
                raise ValueError("无法从项目中获取ID")
            
            # 使用简化的URL（禅道支持这种格式）
            url = f"{self.base_url}task-create-{project_id}-0-0.html"
        
        # 设置请求头
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Referer': f"{self.base_url}my-task.html",
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            response = self.session.get(url, headers=headers)
            
            if response.status_code != 200:
                raise RuntimeError(f'获取创建任务页面失败，状态码: {response.status_code}')
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找任务类型的select元素
            type_select = soup.find('select', {'name': 'type'})
            
            if not type_select:
                raise ValueError('无法在页面中找到任务类型选择元素')
            
            # 解析所有option元素
            task_types = {}
            options = type_select.find_all('option')
            
            for option in options:
                value = option.get('value')
                text = option.get_text(strip=True)
                
                # 跳过空值选项
                if value and text:
                    task_types[text] = value
            
            if not task_types:
                raise ValueError('未能解析到任何任务类型')
            
            return task_types
            
        except Exception as e:
            raise ValueError(f'解析任务类型失败: {e}')
