import unittest
import tempfile
import os
from pathlib import Path

from tools.execution_tools import run_python, run_shell, run_tests, run_linter


class TestExecutionToolsCoreFlow(unittest.TestCase):
    """核心执行工具流程测试"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # 测试run_python核心功能
    def test_run_python_basic(self):
        # 测试直接执行代码
        result = run_python({"code": "print('hello')"})
        self.assertIn("hello", result)
        self.assertIn("return code: 0", result)

        # 测试执行脚本文件
        test_script = self.temp_path / "test.py"
        test_script.write_text("print('from script')")
        result = run_python({"path": str(test_script)})
        self.assertIn("from script", result)

    # 测试run_shell核心功能
    def test_run_shell_basic(self):
        # 测试基础命令执行
        if os.name == "nt":  # Windows
            result = run_shell({"command": "echo hello"})
        else:  # Unix
            result = run_shell({"command": "echo 'hello'"})
        self.assertIn("hello", result)
        self.assertIn("returncode: 0", result)

    # 测试run_tests核心功能
    def test_run_tests_basic(self):
        # 创建基础测试文件
        test_file = self.temp_path / "test_case.py"
        test_file.write_text("""
import unittest
class TestBasic(unittest.TestCase):
    def test_pass(self):
        self.assertTrue(True)
""")

        # 测试pytest
        result = run_tests({"test_path": str(test_file), "framework": "pytest"})
        self.assertIn("1 passed", result)
        self.assertIn("returncode: 0", result)

    # 测试run_linter核心功能
    def test_run_linter_basic(self):
        # 创建规范代码文件
        good_file = self.temp_path / "good_code.py"
        good_file.write_text("x = 1\n")

        # 测试flake8无错误情况
        result = run_linter({"path": str(good_file), "tool": "flake8"})
        self.assertIn("returncode: 0", result)

        # 测试black无错误情况
        result = run_linter({"path": str(good_file), "tool": "black"})
        self.assertIn("returncode: 0", result)


if __name__ == "__main__":
    unittest.main()