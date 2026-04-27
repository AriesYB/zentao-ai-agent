# Zentao AI Agent

用于规划禅道任务并执行常见禅道操作的脚本仓库。当前仓库以 `skills/zentao-task-planner` 技能包为核心，提供任务规划、任务列表查看、批量创建任务、按日期完成任务、关闭已完成任务等能力。

## 当前状态

- 当前可用实现位于 `skills/zentao-task-planner/scripts/`
- 公共逻辑位于 `skills/zentao-task-planner/scripts/zentao_common.py`
- 测试位于 `tests/test_zentao.py`

## 功能

- 查询当前或下一段连续工作日
- 查看个人任务列表
- 根据标准化 TSV 任务表批量创建任务
- 按日期范围预览或批量完成任务
- 关闭已完成但未关闭的任务

## 环境要求

- Python 3.10+
- `uv` 或 `pip`
- 可访问的禅道系统账号

## 安装

先安装 `uv`：

```bash
pip install uv
```

再同步项目依赖：

```bash
uv sync
```

如果只想手动安装脚本运行所需的最小依赖，也可以执行：

```bash
pip install requests beautifulsoup4 python-dotenv chinese-calendar
```

## 配置

复制 `.env.example`，填写禅道配置：

```env
ZENTAO_BASE_URL=https://your-zentao-url.com/zentao/
ZENTAO_ACCOUNT=your_username
ZENTAO_PASSWORD=your_password
ZENTAO_NAME=your_name
```

脚本默认读取 `skills/zentao-task-planner/.env`。如果不放在该位置，可以通过 `--env-file` 显式指定。

## 快速开始

### 1. 查询工作日

```bash
python skills/zentao-task-planner/scripts/get_next_workdays.py --week-type next
```

### 2. 查看任务列表

```bash
python skills/zentao-task-planner/scripts/list_tasks.py --view active --summary-only
```

### 3. 预览批量创建任务

```bash
python skills/zentao-task-planner/scripts/create_tasks.py --plan-file task-plan.tsv --username-mapping "{\"张三\":\"zhangsan\"}"
```

### 4. 预览按日期完成任务

```bash
python skills/zentao-task-planner/scripts/finish_tasks_by_date.py --start-date 2026-04-27
```

### 5. 确认后执行有副作用操作

真正写入禅道时，再追加 `--execute`。例如：

```bash
python skills/zentao-task-planner/scripts/finish_tasks_by_date.py --start-date 2026-04-27 --execute
```

## 任务表格式

批量创建任务使用制表符分隔的 TSV 文本，表头为：

```text
人员姓名	需求编号	任务名称（功能点）	任务类型	预计工时（小时）	预计开始	预计结束
```

示例：

```text
张三	103615	【#103615-PageIndex解析文件-研究】研究测试PageIndex官网版api	研究	4	2025/11/24	2025/11/24
张三	103615	【#103615-PageIndex解析文件-编码】编写调用代码解析采购需求文件	后端编码	4	2025/11/24	2025/11/24
```

## 项目结构

```text
zentao-ai-agent/
├── skills/
│   └── zentao-task-planner/
│       ├── SKILL.md
│       ├── .env.example
│       ├── references/
│       │   ├── commands.md
│       │   ├── workdays.md
│       │   ├── list-tasks.md
│       │   ├── create-tasks.md
│       │   ├── finish-tasks.md
│       │   └── close-tasks.md
│       └── scripts/
│           ├── zentao_common.py
│           ├── get_next_workdays.py
│           ├── list_tasks.py
│           ├── create_tasks.py
│           ├── finish_tasks_by_date.py
│           └── close_finished_tasks.py
├── tests/
│   └── test_zentao.py
├── .env.example
├── pyproject.toml
├── uv.lock
└── README.md
```

## 任务类型

任务类型映射定义在 `skills/zentao-task-planner/scripts/zentao_common.py` 的 `TASK_TYPE_DICT` 中，包含例如：

- 需求、市场/用户调研、需求分析
- 产品方案设计、UI设计、架构设计、详细设计
- 前端编码、后端编码、联调、代码走查、自测/单元测试
- 测试用例、产品功能测试、回归测试、集成测试、自动化测试
- 生产问题处理、生产问题复盘
- 培训、请假、其他

## 测试

运行测试：

```bash
uv run pytest tests/test_zentao.py
```

## 参考文档

- `skills/zentao-task-planner/SKILL.md`
- `skills/zentao-task-planner/references/commands.md`
- `skills/zentao-task-planner/references/workdays.md`
- `skills/zentao-task-planner/references/list-tasks.md`
- `skills/zentao-task-planner/references/create-tasks.md`
- `skills/zentao-task-planner/references/finish-tasks.md`
- `skills/zentao-task-planner/references/close-tasks.md`

## 许可证

MIT License
