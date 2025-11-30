from typing import Dict, List, Optional, Any

from mcp.client import MCPClient
from mcp.config import MCPConfig
from tools import Tool


class MCPManager:
    """
    MCP管理器，负责管理多个MCP服务器
    """

    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config or MCPConfig()
        self.clients: Dict[str, MCPClient] = {}
        self._tools_cache: List[Tool] = []


