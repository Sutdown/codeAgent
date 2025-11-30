from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from clients import BaseClient
from core.planner import TaskPlanner
from memory import ContextCompressor
from prompts import build_code_agent_prompt
from tools import Tool


@dataclass
class Step:
    """表示智能体的一个推理步骤。"""

    thought = ""                # type: str  # 智能体的思考过程
    action = ""                 # type: str  # 要执行的动作/工具名称
    action_input = None         # type: Any  # 动作的输入参数
    observation = ""            # type: str  # 执行动作后的观察结果
    raw = ""                    # type: str  # 原始数据

class ReActAgent:
    """ReAct代理，基于LLM和工具进行推理。"""
    def __init__(
            self,
            client: BaseClient,
            tools : List[Tool],
            *,
            max_steps: int = 200,
            temperature: float = 0.0,
            system_prompt: Optional[str] = None,
            step_callback: Optional[Callable[[int, Step], None]] = None,  # 步骤回调函数
            enable_planning: bool = True,
            enable_compression: bool = True,
    ) -> None:
        if not tools:
            raise ValueError("必须为 ReactAgent 提供至少一个工具。")

        self.client = client                             # 与大模型通话的客户端
        self.tools = {tool.name: tool for tool in tools} # 可用工具的映射
        self.tools_list = tools                          # 工具列表，用于规划器初始化

        self.max_steps = max_steps
        self.temperature = temperature
        self.system_prompt = system_prompt or build_code_agent_prompt(tools)

        self.step_callback = step_callback                   # 步骤执行回调函数
        self.conversation_history: List[Dict[str, str]] = [] # 多轮对话历史记录

        # 规划器
        self.enable_planning = enable_planning
        self.planner = TaskPlanner(client, tools) if enable_planning else None

        # 上下文压缩器（每 5 轮对话压缩一次）
        self.enable_compression = enable_compression
        self.compressor = ContextCompressor(client, compress_every=5, keep_recent=3) if enable_compression else None
