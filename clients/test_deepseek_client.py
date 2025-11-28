import unittest
from clients.deepseek_client import DeepseekClient, DeepSeekError

class TestDeepseekClientRealAPI(unittest.TestCase):
    """通过真实API调用测试DeepseekClient（需配置有效API密钥）"""

    @classmethod
    def setUpClass(cls):
        """初始化客户端（从环境变量获取API密钥）"""
        cls.api_key = "your app key"

        cls.client = DeepseekClient(
            api_key=cls.api_key,
        )

    def test_send_recv_real_message(self):
        """发送真实消息到DeepSeek API并验证响应"""
        # 准备测试消息
        test_messages = [
            {"role": "user", "content": "你好，请简单介绍一下你自己"}
        ]

        # 发送请求
        try:
            response = self.client.send_recv(test_messages)
        except DeepSeekError as e:
            self.fail(f"API调用失败: {str(e)}")

        print("response: ", response)
        # 验证响应结构
        self.assertIsInstance(response, dict, "响应应为字典类型")
        self.assertIn("choices", response, "响应应包含choices字段")
        self.assertIsInstance(response["choices"], list, "choices应为列表类型")
        self.assertGreater(len(response["choices"]), 0, "choices列表不应为空")

        # 测试文本提取
        extracted_text = self.client.extract_txt(response)
        print("extracted_text: ", extracted_text)
        self.assertEqual(extracted_text, response["choices"][0]["message"]["content"].strip(), "文本提取结果不匹配")

    def test_format_error(self):
        """测试格式错误"""
        with self.assertRaises(DeepSeekError) as context:
            self.client.send_recv(
                messages=[{"role": "user", "content": "测试错误"}],
                response_format={"type": "json_object"}
            )
        print("context: ", context)
        self.assertEqual(str(context.exception), "400 Bad Request")

if __name__ == "__main__":
    unittest.main()