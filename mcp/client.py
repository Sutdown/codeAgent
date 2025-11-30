"""MCP 客户端 - 负责与单个 MCP 服务器通信"""
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
from threading import Thread, Lock
from queue import Queue, Empty


class MCPClient:
    """
        和单个MCP服务器进行通信
    """

    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """
        Examples:
            >>> client = MCPClient("playwright", "npx", ["@playwright/mcp@latest"])
        """
        self.name = name
        self.command = command
        self.args = args
        self.env = env

        self.process: Optional[subprocess.Popen] = None # 服务器进程对象
        self.tools: List[Dict[str, Any]] = []           # 服务器提供的工具列表
        self._lock = Lock()                             # 线程锁，用于保护消息发送过程
        self._message_id = 0                            # 消息ID计数器，确保请求与响应匹配
        self._stdout_queue: Queue = Queue()             # 标准输出消息队列
        self._running = False                           # 客户端运行状态标志

    def start(self) -> bool:
        """启动客户端"""
        try:
            full_command = [self.command] + self.args
            process_env = os.environ.copy()
            if self.env:
                process_env.update(self.env)
            is_windows = sys.platform == 'win32'

            if is_windows:
                self.process = subprocess.Popen(
                    ' '.join(full_command),  # Windows 下使用字符串命令
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    env=process_env,
                    shell=True  # Windows 必需
                )
            else:
                self.process = subprocess.Popen(
                    full_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    env=process_env
                )

            # 启动输出读取线程
            self._running = True
            # 异步和非阻塞通信，分离IO和业务逻辑
            self._stdout_thread = Thread(target=self._read_stdout, daemon=True)
            self._stdout_thread.start()

            # 初始化 MCP 连接并获取工具列表
            if not self._initialize():
                self.stop()
                return False

            print(f"✅ MCP 服务器 '{self.name}' 启动成功，提供 {len(self.tools)} 个工具")
            return True
        except Exception as e:
            print(f"❌ 启动 MCP 服务器 '{self.name}' 失败: {e}")
            return False

    def _read_stdout(self) -> None:
        """ 读取服务器输出
        在独立线程中持续读取MCP服务器的标准输出，并将读取到的行放入队列中，
        供主线程处理响应消息使用。该方法在单独的守护线程中运行。
        """
        if not self.process or not self.process.stdout:
            return

        # 客户端正常运行，服务器进程存货时，持续输出
        while self._running and self.process.poll() is None:
            try:
                # 读取原始字节并强制用 UTF-8 解码（忽略错误字符）
                line_bytes = self.process.stdout.buffer.readline()
                if line_bytes:
                    # 持续读取同时存储到队列中
                    line = line_bytes.decode('utf-8', errors='replace').strip()
                    self._stdout_queue.put(line)
            except Exception as e:
                if self._running:
                    print(f"⚠️ 读取 MCP 输出错误: {e}")
                break

    def _initialize(self) -> bool:
        """ 初始化 MCP 连接并获取工具列表 """
        # 建立连接
        result = self._send_message("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "code-agent",
                "version": "1.1.0"
            }
        })

        if not result:
            return False

        # 获取可用工具
        tools_result = self._send_message("tools/list")
        if tools_result and "tools" in tools_result:
            self.tools = tools_result["tools"]
            return True
        return False

    def _send_message(self, method: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """ 发送消息给服务器 """
        if not self.process or not self.process.stdin:
            return None

        with self._lock:
            self._message_id += 1
            message = {
                "jsonrpc": "2.0",
                "id": self._message_id,
                "method": method,
            }
            if params:
                message["params"] = params

            try:
                # 将消息转为JSON字符串并通过标准输入发送
                self.process.stdin.write(json.dumps(message) + "\n")
                # 刷新缓冲区确保消息立即发送
                self.process.stdin.flush()

                timeout_count = 0
                while timeout_count < 50:
                    try:
                        # 尝试从队列中获取响应消息
                        response_line = self._stdout_queue.get(timeout=1)
                        # 解析JSON响应并返回结果
                        response = json.loads(response_line)

                        # 检查响应是否正确
                        if response.get("id") == self._message_id:
                            if "error" in response:
                                print(f"❌ MCP 错误: {response['error']}")
                                return None
                            return response.get("result")

                        # 不是我们的响应，放回队列
                        self._stdout_queue.put(response_line)
                    except Empty:
                        timeout_count += 1
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"⚠️ 发送 MCP 消息错误: {e}")
                return None

    def stop(self) -> None:
        """ 停止客户端 """
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        print(f"🛑 MCP 停止运行: {self.name}")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """ 调用工具 """
        result = self._send_message("tools/call", {
            "tool": tool_name,
            "arguments": arguments
        })

        if result and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    return first_item["text"]
                return str(first_item)
            return str(content)
        return None

    def get_tools(self) -> List[Dict[str, Any]]:
        return self.tools.copy()

    def is_running(self) -> bool:
        """
        检查MCP服务器进程正在运行
        1. 检查客户端是否持有有效的进程对象
        2. 检查进程是否正在运行
        """
        return self.process is not None and self.process.poll() is None


