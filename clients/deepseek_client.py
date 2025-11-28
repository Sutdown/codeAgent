from __future__ import annotations
from typing import List, Dict, Any, Optional
from clients.base_client import LLMError, BaseClient
import requests

class DeepSeekError(LLMError):
    """
    DeepSeek API错误
    """

class DeepSeekClient(BaseClient):
    """
    DeepSeek API客户端
    """
    def __init__(
            self,
            api_key: str,
            *args,
            model: str = "deepseek-chat",
            base_url: str = "https://api.deepseek.com",
            endpoint: str = "/v1/chat/completions",
            timeout: int = 600,
    ) -> None:
        super().__init__(api_key, model=model, base_url=base_url, timeout=timeout)
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def send_recv(
            self,
            messages: List[Dict[str,str]],
            *,
            response_format: Optional[Dict[str, Any]] = None,
            stream: bool = False,
            **extra: Any,
    ) -> Dict[str, Any]:
        """
        发送消息并接收回复
        Args:
            messages: 聊天消息列表
            **extra: 额外的参数
        Return:
            API响应的字典
        """
        if stream:
            raise DeepSeekError("streaming is not supported")
        data: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if response_format:
            data["response_format"] = response_format
        data.update(extra)

        full_url = f"{self.base_url}/{self.endpoint.lstrip('/')}"
        response = self.session.post(
            full_url,
            json=data,
            timeout=self.timeout,
        )
        if not response.ok:
            raise DeepSeekError(f"{response.status_code} {response.reason}")
        return response.json()

    def extract_txt(self, data: Dict[str, Any]) -> str:
        """
        从API响应中提取文本
        Args:
            data: API响应的字典
        Return:
            文本
        """
        if not isinstance(data, dict):
            raise DeepSeekError("invalid response")

        # Response API format:
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        # Chat completions format:
        output_text = data.get("choices", [{}])[0].get("message", {}).get("content")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        raise DeepSeekError("invalid response")

    @staticmethod
    def _format_error(response: requests.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        message = f"DeepSeek API error: {response.status_code} {response.reason}"
        if isinstance(body, dict):
            detail = body.get("error", {}).get("message") or body.get("error_msg")
            if not detail:
                detail = body.get("message")
            if detail:
                message = f"{message} - {detail}"
        elif body:
            message = f"{message} - {body}"
        return message