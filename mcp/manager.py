from typing import Dict, List, Optional, Any
from mcp.client import MCPClient
from mcp.config import MCPConfig, MCPServerConfig
from tools import Tool


class MCPManager:
    """
    MCP管理器，负责管理多个MCP服务器
    """

    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config or MCPConfig()     # 所有的服务器配置信息
        self.clients: Dict[str, MCPClient] = {} # 服务器名称对应的客户端
        self._tools_cache: List[Tool] = []      # 缓存的工具列表

    def start_all(self) -> int:
        """
                启动所有启用的MCP服务器
                return：
                    返回启动成功的服务器数量
                """
        enabled_servers = self.config.get_enabled_servers()
        success_count = 0
        for name, server_config in enabled_servers.items():
            if self.start_server(name): # 启动服务器
                success_count += 1

        if success_count > 0:
            self._rebuild_tools_cache() # 重建工具缓存

        return success_count

    def start_server(self, name: str) -> bool:
        """启动指定服务器
        检查服务器是否在运行，没有运行就根据配置启动新的客户端实例
        """
        if name in self.clients and self.clients[name].is_running():
            print(f"⚠️ MCP 服务器 '{name}' 已在运行中")
            return True

        server_config = self.config.get_server_config(name)
        if not server_config:
            print(f"❌ 未找到 MCP 服务器配置：{name}")
            return False

        if not server_config.enabled:
            print(f"⚠️ MCP 服务器 '{name}' 已禁用")
            return False

        client = MCPClient(
            name,
            server_config.command,
            server_config.args,
            server_config.env
        )

        if client.start():
            self.clients[name] = client
            self._rebuild_tools_cache()
            return True

        return False

    def stop_server(self, name: str) -> None:
        if name in self.clients:
            self.clients[name].stop()
            del self.clients[name]
            self._rebuild_tools_cache()

    def stop_all(self) -> None:
        for client in self.clients.values():
            client.stop()
        self.clients.clear()
        self._tools_cache.clear()

    def _rebuild_tools_cache(self) -> None:
        """重建工具缓存"""
        self._tools_cache.clear()

        for server_name, client in self.clients.items():
            if not client.is_running():
                continue

            mcp_tools = client.get_tools()
            for tool_def in mcp_tools:
                tool_name = tool_def.get("name", "")
                description = tool_def.get("description", "")
                input_schema = tool_def.get("inputSchema", {})

                wrapped_tool = self._create_tool_wrapper(
                    server_name=server_name,
                    tool_name=tool_name,
                    description=description,
                    input_schema=input_schema
                )
                self._tools_cache.append(wrapped_tool)

    def _create_tool_wrapper(
        self,
        server_name: str,
        tool_name: str,
        description: str,
        input_schema: Dict[str, Any]
    ) -> Tool:
        """
        创建MCP工具的包装器
        """
        full_description = f"[MCP:{server_name}] {description}"

        # 构建完整工具描述
        if input_schema and "properties" in input_schema:
            properties = input_schema["properties"]
            required = input_schema.get("required", [])

            params_desc = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required

                param_str = f'"{param_name}": {param_type}'
                if not is_required:
                    param_str = f"optional {param_str}"
                if param_desc:
                    param_str += f" ({param_desc})"

                params_desc.append(param_str)

            if params_desc:
                full_description += f". Arguments: {{{', '.join(params_desc)}}}"

        # 创建工具执行函数
        def runner(arguments: Dict[str, Any]) -> str:
            """
            工具执行函数
            """
            client = self.clients.get(server_name)
            if not client or not client.is_running():
                return f"❌ MCP 服务器 '{server_name}' 未运行"

            result = client.call_tool(tool_name, arguments)
            if result is None:
                return f"❌ 调用 MCP 工具 '{tool_name}' 失败"

            return result

        return Tool(
            name=f"mcp_{server_name}_{tool_name}",
            description=full_description,
            runner=runner
        )


    def get_tools(self) -> List[Tool]:
        return self._tools_cache.copy()

    def get_running_servers(self) -> List[str]:
        return [
            server_name for server_name, client in self.clients.items()
            if client.is_running()
        ]

    def get_server_status(self) -> Dict[str, bool]:
        status = {}
        for name in self.config.servers.keys():
            client = self.clients.get(name)
            status[name] = client.is_running() if client else False
        return status

    def add_server_config(self, config: MCPServerConfig) -> None:
        self.config.add_server(config)

    def remove_server_config(self, name: str) -> None:
        self.stop_server(name)
        self.config.remove_server(name)

