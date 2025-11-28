from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMError(RuntimeError):
    """
    Base class for all LLM API errors.
    """

class BaseClient(ABC):
    """ LLM客户端的抽象基类 """
    def __init__(
            self,
            api_key: str,
            *,
            model: str,
            base_url: str,
            timeout: int = 600,
    ) -> None:
        if not api_key:
            raise LLMError("api_key is required")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @abstractmethod
    def send_recv(
            self,
            messages: List[Dict[str,str]],
            **extra: Any,
    ) -> Dict[str, Any]:
        """
        发送消息并接收回复
        Args:
            messages: 消息列表，包含role和content
            **extra: 额外参数（比如temperature，max_tokens)等
        Return:
            API响应的字典
        """
        pass

    @abstractmethod
    def extract_txt(self, data: Dict[str, Any]):
        """
        从API响应中提取文本
        Args:
            data: API响应的字典
        Return:
            文本
        """
        pass

    def chat(
            self,
            messages: List[Dict[str,str]],
            **extra: Any,
    ) -> str:
        """
        聊天
        Args:
            messages: 聊天消息列表
            **extra: 额外的参数
        Return:
            回复文本
        """
        data = self.send_recv(messages, **extra)
        return self.extract_txt(data)