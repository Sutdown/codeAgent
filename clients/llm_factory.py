from __future__ import annotations
from typing import Optional

from clients.base_client import BaseClient
from clients.deepseek_client import DeepSeekClient

def create_llm_client(
    provider: str,
    api_key: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 600,
    **kwargs,
) -> BaseClient:
    """
    Args:
        provider: 提供商名称 ("deepseek", "openai", "claude", "gemini")
        api_key: API 密钥
        model: 模型名称（可选，使用默认值）
        base_url: API 基础 URL（可选，使用默认值）
        timeout: 请求超时时间（秒）
        **kwargs: 其他特定于提供商的参数

    Returns:
        对应的 LLM 客户端实例

    Raises:
        ValueError: 如果提供商不支持
    """
    provider_lower=provider.lower()
    if provider_lower == "deepseek":
        params = {
            "api_key": api_key,
            "model": model or "deepseek-chat",
            "base_url": base_url or "https://api.deepseek.com",
            "timeout": timeout,
        }
        return DeepSeekClient(**params)

    else:
        raise ValueError(f"不支持的提供商: {provider}")

# 默认配置
PROVIDER_DEFAULTS = {
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
    },
}