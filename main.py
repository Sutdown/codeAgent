from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List

from dotenv import load_dotenv

from clients import PROVIDER_DEFAULTS, create_llm_client, LLMError
from core import ReActAgent
from mcp import load_mcp_config, MCPManager
from tools import Tool, default_tools

# 尝试导入 colorama 用于彩色输出
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # 如果没有 colorama，定义空的颜色常量
    class Fore:
        GREEN = ""
        YELLOW = ""
        RED = ""
        CYAN = ""
        MAGENTA = ""
        BLUE = ""

    class Style:
        BRIGHT = ""
        RESET_ALL = ""

@dataclass
class Config:
    """运行时配置"""
    api_key: str
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    max_steps: int = 100
    temperature: float = 0.7
    show_steps: bool = False

def get_api_key_for_provider(provider: str) -> str | None:
    """根据提供商获取对应的 API 密钥"""
    provider_env_map = {
        "deepseek": "DEEPSEEK_API_KEY",
    }
    env_var = provider_env_map.get(provider.lower())
    return os.getenv(env_var) if env_var else None

def print_separator(char: str = "=", length: int = 70) -> None:
    """打印分隔线"""
    print(f"{Fore.CYAN}{char * length}{Style.RESET_ALL}")

def print_header(text: str) -> None:
    """打印标题"""
    print_separator()
    print(f"{Fore.GREEN}{Style.BRIGHT}{text.center(70)}{Style.RESET_ALL}")
    print_separator()

def print_welcome() -> None:
    """打印欢迎界面"""
    print("\n")
    print_header("DM-Code-Agent")
    print(f"{Fore.YELLOW}欢迎使用 LLM 驱动的 DM-Code-Agent 智能体系统！{Style.RESET_ALL}")

def print_menu() -> None:
    """打印主菜单"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}主菜单：{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  1.{Style.RESET_ALL} 执行新任务")
    print(f"{Fore.GREEN}  2.{Style.RESET_ALL} 多轮对话模式")
    print(f"{Fore.GREEN}  3.{Style.RESET_ALL} 查看可用工具列表")
    print(f"{Fore.GREEN}  4.{Style.RESET_ALL} 配置设置")
    print(f"{Fore.GREEN}  5.{Style.RESET_ALL} 退出程序")
    print()

def show_tools(tools: List[Tool]) -> None:
    """显示可用工具列表"""
    print_separator("-")
    print(f"{Fore.CYAN}{Style.BRIGHT}可用工具列表：{Style.RESET_ALL}\n")

    for idx, tool in enumerate(tools, start=1):
        print(f"{Fore.GREEN}{idx}. {tool.name}{Style.RESET_ALL}")
        print(f"   {Fore.YELLOW}描述：{Style.RESET_ALL}{tool.description}")
        print()

    print_separator("-")

def configure_settings(config: Config) -> None:
    """配置设置"""
    print_separator("-")
    print(f"{Fore.CYAN}{Style.BRIGHT}当前配置：{Style.RESET_ALL}\n")
    print(f"  提供商：{Fore.YELLOW}{config.provider}{Style.RESET_ALL}")
    print(f"  模型：{Fore.YELLOW}{config.model}{Style.RESET_ALL}")
    print(f"  Base URL：{Fore.YELLOW}{config.base_url}{Style.RESET_ALL}")
    print(f"  最大步骤数：{Fore.YELLOW}{config.max_steps}{Style.RESET_ALL}")
    print(f"  温度：{Fore.YELLOW}{config.temperature}{Style.RESET_ALL}")
    print(f"  显示步骤：{Fore.YELLOW}{'是' if config.show_steps else '否'}{Style.RESET_ALL}")
    print()

    print(f"{Fore.CYAN}选择要修改的设置（直接回车跳过）：{Style.RESET_ALL}\n")

    config_changed = False

    # 修改提供商
    provider_input = input(f"LLM 提供商 (deepseek) [{config.provider}]: ").strip().lower()
    if provider_input and provider_input in ["deepseek"]:
        if provider_input != config.provider:
            # 尝试获取新提供商的 API 密钥
            new_api_key = get_api_key_for_provider(provider_input)
            if not new_api_key:
                print(f"{Fore.RED}✗ 未找到 {provider_input.upper()}_API_KEY 环境变量{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}请在 .env 文件中配置 {provider_input.upper()}_API_KEY{Style.RESET_ALL}")
            else:
                config.provider = provider_input
                config.api_key = new_api_key  # 更新 API 密钥
                # 自动更新默认模型和 base_url
                defaults = PROVIDER_DEFAULTS.get(provider_input, {})
                config.model = defaults.get("model", config.model)
                config.base_url = defaults.get("base_url", config.base_url)
                config_changed = True
                print(f"{Fore.GREEN}✓ 已更新提供商为 {provider_input}，模型和 URL 已自动调整{Style.RESET_ALL}")
    elif provider_input and provider_input not in ["deepseek"]:
        print(f"{Fore.RED}✗ 无效的提供商{Style.RESET_ALL}")

    # 修改模型
    model_input = input(f"模型名称 [{config.model}]: ").strip()
    if model_input:
        config.model = model_input
        config_changed = True
        print(f"{Fore.GREEN}✓ 已更新模型为 {model_input}{Style.RESET_ALL}")

    # 修改 Base URL
    base_url_input = input(f"Base URL [{config.base_url}]: ").strip()
    if base_url_input:
        config.base_url = base_url_input
        config_changed = True
        print(f"{Fore.GREEN}✓ 已更新 Base URL 为 {base_url_input}{Style.RESET_ALL}")

    # 修改最大步骤数
    try:
        max_steps_input = input(f"最大步骤数 [{config.max_steps}]: ").strip()
        if max_steps_input:
            new_max_steps = int(max_steps_input)
            if new_max_steps > 0:
                config.max_steps = new_max_steps
                config_changed = True
                print(f"{Fore.GREEN}✓ 已更新最大步骤数为 {new_max_steps}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ 最大步骤数必须大于 0{Style.RESET_ALL}")
    except ValueError:
        print(f"{Fore.RED}✗ 无效的数字{Style.RESET_ALL}")

    # 修改温度
    try:
        temp_input = input(f"温度 (0.0-2.0) [{config.temperature}]: ").strip()
        if temp_input:
            new_temp = float(temp_input)
            if 0.0 <= new_temp <= 2.0:
                config.temperature = new_temp
                config_changed = True
                print(f"{Fore.GREEN}✓ 已更新温度为 {new_temp}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ 温度必须在 0.0 到 2.0 之间{Style.RESET_ALL}")
    except ValueError:
        print(f"{Fore.RED}✗ 无效的数字{Style.RESET_ALL}")

    # 修改显示步骤
    show_steps_input = input(f"显示步骤 (y/n) [{'y' if config.show_steps else 'n'}]: ").strip().lower()
    if show_steps_input in ['y', 'yes', '是']:
        if not config.show_steps:
            config.show_steps = True
            config_changed = True
        print(f"{Fore.GREEN}✓ 已启用显示步骤{Style.RESET_ALL}")
    elif show_steps_input in ['n', 'no', '否']:
        if config.show_steps:
            config.show_steps = False
            config_changed = True
        print(f"{Fore.GREEN}✓ 已禁用显示步骤{Style.RESET_ALL}")

    print_separator("-")

def create_step_callback(show_steps: bool):
    """创建步骤回调函数，用于实时打印 agent 执行状态"""
    def callback(step_num: int, step: Any) -> None:
        if show_steps:
            print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[步骤 {step_num}]{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}思考：{Style.RESET_ALL}{step.thought}")
            print(f"  {Fore.YELLOW}动作：{Style.RESET_ALL}{step.action}")
            if step.action_input:
                print(f"  {Fore.YELLOW}输入：{Style.RESET_ALL}{json.dumps(step.action_input, ensure_ascii=False)}")
            print(f"  {Fore.YELLOW}观察：{Style.RESET_ALL}{step.observation}")
        else:
            # 即使不显示详细步骤，也显示简要进度
            print(f"{Fore.CYAN}[步骤 {step_num}] {step.action}{Style.RESET_ALL}", end=" ", flush=True)
            if step.action == "finish" or step.action == "task_complete":
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            elif step.action == "error":
                print(f"{Fore.RED}✗{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}")

    return callback

def multi_turn_conversation(config: Config, tools: List[Tool]) -> None:
    """多轮对话"""
    print_separator("-")
    print(f"{Fore.CYAN}{Style.BRIGHT}多轮对话模式{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}进入多轮对话模式，智能体会记住之前的所有对话内容{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}输入 'exit' 退出对话模式，输入 'reset' 重置对话历史{Style.RESET_ALL}\n")
    print_separator("-")

    try:
        # 创建客户端和智能体
        client = create_llm_client(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
        )
        step_callback = create_step_callback(config.show_steps)

        agent = ReActAgent(
            client,
            tools,
            max_steps=config.max_steps,
            temperature=config.temperature,
            step_callback=step_callback,
        )

        conversation_count = 0

        while True:
            print(f"\n{Fore.CYAN}[对话 {conversation_count + 1}]{Style.RESET_ALL}")
            task = input(f"{Fore.YELLOW}请输入任务（exit 退出，reset 重置历史）：{Style.RESET_ALL}\n> ").strip()

            if not task:
                print(f"{Fore.RED}✗ 任务描述不能为空{Style.RESET_ALL}")
                continue

            if task.lower() == "exit":
                print(f"\n{Fore.YELLOW}退出多轮对话模式{Style.RESET_ALL}")
                break

            if task.lower() == "reset":
                agent.reset_conversation()
                conversation_count = 0
                print(f"{Fore.GREEN}✓ 对话历史已重置{Style.RESET_ALL}")
                continue

            try:
                print(f"\n{Fore.CYAN}正在执行任务...{Style.RESET_ALL}\n")
                print_separator("-")

                # 执行任务
                result = agent.run(task)
                conversation_count += 1

                # 显示最终结果
                print(f"\n{Fore.GREEN}{Style.BRIGHT}最终答案：{Style.RESET_ALL}\n")
                print(result.get("final_answer", ""))
                print()
                print_separator("-")

            except LLMError as e:
                print(f"\n{Fore.RED}{Style.BRIGHT}✗ API 错误：{Style.RESET_ALL}{e}")
                print_separator("-")
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}退出多轮对话模式{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}{Style.BRIGHT}✗ 发生错误：{Style.RESET_ALL}{e}")
                print_separator("-")

    except Exception as e:
        print(f"\n{Fore.RED}{Style.BRIGHT}✗ 初始化错误：{Style.RESET_ALL}{e}")
        print_separator("-")

def execute_task(config: Config, tools: List[Tool]) -> None:
    """执行任务"""
    print_separator("-")
    print(f"{Fore.CYAN}{Style.BRIGHT}执行新任务{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}请输入任务描述（输入完成后按回车）：{Style.RESET_ALL}")

    task = input("> ").strip()

    if not task:
        print(f"{Fore.RED}✗ 任务描述不能为空{Style.RESET_ALL}")
        return

    try:
        # 创建客户端和智能体
        client = create_llm_client(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
        )

        # 创建步骤回调函数
        step_callback = create_step_callback(config.show_steps)

        agent = ReActAgent(
            client,
            tools,
            max_steps=config.max_steps,
            temperature=config.temperature,
            step_callback=step_callback,
        )

        print(f"\n{Fore.CYAN}正在执行任务...{Style.RESET_ALL}\n")
        print_separator("-")

        # 执行任务
        result = agent.run(task)

        # 显示最终结果
        print(f"\n{Fore.GREEN}{Style.BRIGHT}最终答案：{Style.RESET_ALL}\n")
        print(result.get("final_answer", ""))
        print()
        print_separator("-")

    except LLMError as e:
        print(f"\n{Fore.RED}{Style.BRIGHT}✗ API 错误：{Style.RESET_ALL}{e}")
        print_separator("-")
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}任务已被用户中断{Style.RESET_ALL}")
        print_separator("-")
    except Exception as e:
        print(f"\n{Fore.RED}{Style.BRIGHT}✗ 发生错误：{Style.RESET_ALL}{e}")
        print_separator("-")

def interactive_mode(config: Config) -> int:
    """交互式菜单模式"""
    print_welcome()

    # 初始化 MCP 管理器
    mcp_config = load_mcp_config()
    mcp_manager = MCPManager(mcp_config)

    # 启动所有启用的 MCP 服务器
    print(f"{Fore.CYAN}正在加载 MCP 服务器...{Style.RESET_ALL}")
    started_count = mcp_manager.start_all()
    if started_count > 0:
        print(f"{Fore.GREEN}✓ 成功启动 {started_count} 个 MCP 服务器{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}ℹ 未启用 MCP 服务器{Style.RESET_ALL}")

    # 获取包含 MCP 工具的工具列表
    mcp_tools = mcp_manager.get_tools()
    tools = default_tools(include_mcp=True, mcp_tools=mcp_tools)

    if mcp_tools:
        print(f"{Fore.GREEN}✓ 加载了 {len(mcp_tools)} 个 MCP 工具{Style.RESET_ALL}")

    try:
        while True:
            try:
                print_menu()
                choice = input(f"{Fore.CYAN}请选择操作 (1-5): {Style.RESET_ALL}").strip()

                if choice == "1":
                    # 执行新任务
                    execute_task(config, tools)

                elif choice == "2":
                    # 多轮对话模式
                    multi_turn_conversation(config, tools)

                elif choice == "3":
                    # 查看工具列表
                    show_tools(tools)

                elif choice == "4":
                    # 配置设置
                    configure_settings(config)

                elif choice == "5":
                    # 退出程序
                    print(f"\n{Fore.YELLOW}感谢使用！再见！{Style.RESET_ALL}\n")
                    return 0

                else:
                    print(f"{Fore.RED}✗ 无效的选择，请输入 1-5{Style.RESET_ALL}")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}感谢使用！再见！{Style.RESET_ALL}\n")
                return 0
            except EOFError:
                print(f"\n\n{Fore.YELLOW}感谢使用！再见！{Style.RESET_ALL}\n")
                return 0
            except Exception as e:
                print(f"\n{Fore.RED}{Style.BRIGHT}✗ 发生错误：{Style.RESET_ALL}{e}\n")

    finally:
        # 清理 MCP 资源
        print(f"{Fore.CYAN}正在关闭 MCP 服务器...{Style.RESET_ALL}")
        mcp_manager.stop_all()
        print(f"{Fore.GREEN}✓ MCP 服务器已关闭{Style.RESET_ALL}")

def main() -> int:
    """主入口函数"""
    load_dotenv()
    # 获取提供商的默认配置
    provider_defaults = PROVIDER_DEFAULTS.get("deepseek", {})
    # 创建配置
    config = Config(
        api_key=get_api_key_for_provider("deepseek"),
        provider="deepseek",
        model=provider_defaults.get("model"),
        base_url=provider_defaults.get("base_url"),
    )

    return interactive_mode(config)

if __name__ == "__main__":
    raise SystemExit(main())