"""
禅道工具测试
"""

import pytest
from zentao_ai_agent import ZendaoTool
from zentao_ai_agent.zentao import task_type_dict
from zentao_ai_agent.zentao.zendao_tool import strip_html_tags


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
