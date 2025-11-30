"""MCP 配置管理"""
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class MCPServerConfig:
    """
    MCP服务器的配置信息，包括启动命令，参数和环境变量等。
    name: MCP服务器名称
    command: 启动MCP服务器的命令
    args: 命令行
    """
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    enabled: bool = True

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "MCPServerConfig":
        """
        从字典中创建MCP服务器配置
        :param data: 字典数据
        :return: MCP服务器配置
        Examples:
            >>> data = {"command": "npx", "args": ["@playwright/mcp@latest"], "enabled": True}
            >>> config = MCPServerConfig.from_dict("playwright", data)
            >>> config.command
        """
        return cls(
            name=name,
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env"),
            enabled=data.get("enabled", True)
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        将MCP服务器配置转换为字典
        :return: 字典数据
        Examples:
            >>> config = MCPServerConfig("test", "npx", ["tool"], {"DEBUG": "1"}, True)
            >>> data = config.to_dict()
            >>> "command" in data and "args" in data
        """
        result = {
            "command": self.command,
            "args": self.args
        }
        if self.env:
            result["env"] = self.env
        if not self.enabled:
            result["enabled"] = self.enabled
        return result

@dataclass
class MCPConfig:
    """
    Attributes:
        servers (Dict[str, MCPServerConfig]): 服务器名称到配置的映射字典
    """
    servers: Dict[str, MCPServerConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPConfig":
        mcp_servers = data.get("mcpServers", {})
        servers = {
            name: MCPServerConfig.from_dict(name, config)
            for name, config in mcp_servers.items()
        }
        return cls(servers=servers)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mcpServers": {
                name: server.to_dict()
                for name, server in self.servers.items()
            }
        }

    def add_server(self, config: MCPServerConfig) -> None:
        self.servers[config.name] = config

    def remove_server(self, name: str) -> None:
        if name in self.servers:
            del self.servers[name]

    def get_enabled_servers(self) -> Dict[str, MCPServerConfig]:
        return {
            name: server
            for name, server in self.servers.items()
            if server.enabled
        }

def load_mcp_config(config_path: str = "mcp_config.json") -> MCPConfig:
    if not os.path.exists(config_path):
        return MCPConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MCPConfig.from_dict(data)
    except Exception as e:
        print(f"⚠️ 加载 MCP 配置失败: {e}，使用空配置")
        return MCPConfig()


def save_mcp_config(config: MCPConfig, config_path: str = "mcp_config.json") -> bool:
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 保存 MCP 配置失败: {e}")
        return False