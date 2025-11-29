import unittest
from typing import List, Dict
from memory.context_compressor import ContextCompressor  # 正确导入模块


class TestContextCompressor(unittest.TestCase):  # 注意这里的冒号，之前的代码可能漏了
    def setUp(self):
        """初始化测试环境，创建压缩器实例和测试用对话历史"""
        self.compressor = ContextCompressor(compress_every=5, keep_recent=3)

        # 构建测试用对话历史（系统消息 + 多轮用户-助手对话）
        self.sample_history = [
            {"role": "system", "content": "你是代码助手"},
            {"role": "user", "content": "读取文件：main.py"},
            {"role": "assistant", "content": "执行工具 read_file，输入：{'path': 'main.py'}"},
            {"role": "user", "content": "编辑文件：config.json"},
            {"role": "assistant", "content": "执行工具 edit_file，输入：{'path': 'config.json'}"},
            {"role": "user", "content": "运行测试"},
            {"role": "assistant", "content": "执行工具 run_test，输入：{}"},
            {"role": "user", "content": "有错误吗？"},
            {"role": "assistant", "content": "错误：测试用例失败"},
            {"role": "user", "content": "修复错误"},
            {"role": "assistant", "content": "执行工具 fix_error，输入：{}"},
            {"role": "user", "content": "完成了吗？"},
            {"role": "assistant", "content": "成功修复，任务完成"},
        ]

    def test_should_compress(self):
        """测试是否需要压缩的判断逻辑"""
        # 1. 对话轮数不足时不压缩
        short_history = self.sample_history[:4]  # 2轮用户消息
        self.assertFalse(self.compressor.should_compress(short_history))

        # 2. 对话轮数达标时压缩
        full_history = self.sample_history  # 5轮用户消息
        self.assertTrue(self.compressor.should_compress(full_history))

    def test_compress_basic(self):
        """测试基本压缩功能"""
        compressed = self.compressor.compress(self.sample_history)

        # 验证结构：系统消息 + 压缩摘要 + 最近3*2轮对话（6条消息）
        system_msgs = [m for m in compressed if m["role"] == "system"]
        summary_msgs = [m for m in compressed if m["role"] == "user" and "历史对话摘要" in m["content"]]
        recent_msgs = [m for m in compressed if
                       m["role"] not in ["system"] or "历史对话摘要" not in m.get("content", "")]

        self.assertEqual(len(system_msgs), 1)  # 保留系统消息
        self.assertEqual(len(summary_msgs), 1)  # 生成1条摘要
        self.assertEqual(len(recent_msgs), 8)  # 最近3轮（6条）

    def test_extract_key_information(self):
        """测试关键信息提取逻辑"""
        # 提取前5轮非系统消息作为测试数据
        test_messages = [m for m in self.sample_history if m["role"] != "system"][:10]
        summary = self.compressor._extract_key_information(test_messages)
        # 验证提取结果
        self.assertIn("涉及文件：config.json, main.py", summary)  # 提取文件
        self.assertIn("使用的工具：edit_file, fix_error, read_file, run_test", summary)  # 提取工具
        self.assertIn("错误：测试用例失败", summary)  # 提取错误
        self.assertIn("修复错误", summary)  # 提取完成的操作

    def test_extract_no_information(self):
        """测试无关键信息时的默认摘要"""
        empty_messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]
        summary = self.compressor._extract_key_information(empty_messages)
        self.assertEqual(summary, "进行了 2 轮对话，讨论了代码相关任务。")

    def test_get_compression_stats(self):
        """测试压缩统计信息计算"""
        original = self.sample_history
        compressed = self.compressor.compress(original)
        stats = self.compressor.get_compression_stats(original, compressed)

        self.assertEqual(stats["original_messsages"], len(original))
        self.assertEqual(stats["compressed_messages"], len(compressed))
        self.assertGreater(stats["compression_ratio"], 0)  # 压缩率为正
        self.assertEqual(stats["saved_messages"], len(original) - len(compressed))

    def test_turn_count_reset(self):
        """测试压缩后对话轮数计数器重置"""
        # 压缩前计数器
        self.compressor.should_compress(self.sample_history)
        self.assertEqual(self.compressor.turn_count, 6)  # 5轮用户消息

        # 压缩后计数器
        compressed = self.compressor.compress(self.sample_history)
        self.assertEqual(self.compressor.turn_count, 4)  # 保留最近3轮


if __name__ == "__main__":
    unittest.main()