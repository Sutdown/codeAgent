"""系统提示词定义"""
from typing import List
from prompts.agent_prompts import SYSTEM_PROMPT
from tools import Tool

def build_code_agent_prompt(tools: List[Tool]) -> str:
    """ 从 markdown 文件构建 Code Agent 的系统提示词
    Args:
        tools: 可用工具列表
    Returns:
        系统提示词字符串
    """

    # 构建工具列表
    tool_lines = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)

    # 替换模板中的工具占位符
    return SYSTEM_PROMPT.replace("{tools}", tool_lines)
