import os
from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """运行时配置"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    provider = "deepseek"
    model = "deepseek-chat"
    base_url = "https://api.deepseek.com"
    max_steps = 100
    temperature = 0.7
    show_steps = False

def print_menu() -> None:
    print("\n1. 执行新任务")
    print("2. 多轮对话模式")
    print("3. 查看可用工具")
    print("4. 退出")

def execute_new_task():
    pass

def multi_round_chat():
    pass

def view_available_tools():
    pass

def agent_intreactive(config: Config)->int:
    print("欢迎使用deepseek驱动的code agent")

    # TODO 启用MCP

    try:
        while True:
            try:
                print_menu()
                choice = int(input("请选择操作（输入数字1-4）："))
                if choice == 1:
                    execute_new_task()
                elif choice == 2:
                    multi_round_chat()
                elif choice == 3:
                    view_available_tools()
                elif choice == 4:
                    print("程序退出，再见！")
                    return 0
                else:
                    print("输入错误，请选择1-4之间的数字！\n")
            except ValueError:
                print("输入格式错误，请输入数字！\n")
    finally:
        # 关闭MCP
        # TODO 关闭MCP服务器
        print("MCP服务器已关闭")


def main(argv: Any=None)->int:
    config = Config()
    return agent_intreactive(config)


if __name__ == "__main__":
    raise SystemExit(main())