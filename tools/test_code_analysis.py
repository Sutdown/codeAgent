import unittest
import tempfile
import os
import json
from pathlib import Path
from tools.code_analysis_tools import (  # 修正导入路径
    parse_ast,
    get_function_signature,
    find_dependencies,
    get_code_metrics
)


class TestCodeAnalysisTools(unittest.TestCase):
    def setUp(self):
        # 创建临时Python文件用于测试
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'  # 添加编码参数
        )
        self.file_path = self.temp_file.name
        # 写入更简洁的测试代码，避免缩进问题
        self.temp_file.write("""
import os
from typing import List

GLOBAL_VAR = 42

class TestClass:
    def test_method(self):
        pass

def add(a: int, b: int) -> int:
    return a + b
        """)
        self.temp_file.close()

    def tearDown(self):
        # 清理临时文件
        if os.path.exists(self.file_path):
            os.unlink(self.file_path)

    def test_parse_ast(self):
        """测试AST解析功能"""
        result = parse_ast({"path": self.file_path})

        # 先检查是否返回错误信息
        self.assertNotIn("不存在", result, f"解析失败: {result}")
        self.assertNotIn("不是文件", result, f"解析失败: {result}")
        self.assertNotIn("不是Python文件", result, f"解析失败: {result}")
        self.assertNotIn("语法错误", result, f"解析失败: {result}")

        # 再尝试解析JSON
        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            self.fail(f"解析返回的不是有效的JSON: {result}, 错误: {str(e)}")

        # 验证基本结构
        self.assertEqual(data["file"], self.file_path)
        self.assertIsInstance(data["imports"], list)
        self.assertIsInstance(data["classes"], list)
        self.assertIsInstance(data["functions"], list)
        self.assertIsInstance(data["global_variables"], list)

        # 验证内容提取
        self.assertEqual(len(data["imports"]), 2)  # os 和 typing
        self.assertEqual(len(data["classes"]), 1)  # TestClass
        self.assertEqual(len(data["functions"]), 1)  # add
        self.assertEqual(len(data["global_variables"]), 1)  # GLOBAL_VAR

if __name__ == '__main__':
    unittest.main()