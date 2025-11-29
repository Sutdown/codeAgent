import os
import tempfile
import unittest
from pathlib import Path
from tools.file_tools import (
    create_file,
    read_file,
    list_directory,
    edit_file,
    search_in_file
)


class TestFileTools(unittest.TestCase):
    def setUp(self):
        """创建临时目录，在每个测试方法执行前调用"""
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)

    def tearDown(self):
        """清理临时目录，在每个测试方法执行后调用"""
        self.temp_dir_obj.cleanup()

    def test_create_file(self):
        """测试创建文件功能"""
        file_path = self.temp_dir / "test.txt"
        content = "Hello, World!"

        # 测试正常创建
        result = create_file({
            "path": str(file_path),
            "content": content
        })
        self.assertIn(f"已将 {len(content)} 个字符写入", result)
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_text(encoding="utf-8"), content)

        # 测试覆盖文件
        new_content = "New content"
        create_file({
            "path": str(file_path),
            "content": new_content
        })
        self.assertEqual(file_path.read_text(encoding="utf-8"), new_content)

        # 测试content非字符串的错误
        with self.assertRaises(ValueError) as exc_context:
            create_file({"path": str(file_path), "content": 123})
        self.assertIn("工具参数 'content' 必须是字符串", str(exc_context.exception))

    def test_read_file(self):
        """测试读取文件功能"""
        file_path = self.temp_dir / "test.txt"
        content = "Line 1\nLine 2\nLine 3\nLine 4"
        file_path.write_text(content, encoding="utf-8")

        # 测试读取全部内容
        result = read_file({"path": str(file_path)})
        self.assertEqual(result, content)

        # 测试读取行范围
        result = read_file({
            "path": str(file_path),
            "line_start": 2,
            "line_end": 3
        })
        self.assertEqual(result, "Line 2\nLine 3")

        # 测试只指定起始行
        result = read_file({
            "path": str(file_path),
            "line_start": 3
        })
        self.assertEqual(result, "Line 3\nLine 4")

        # 测试只指定结束行
        result = read_file({
            "path": str(file_path),
            "line_end": 2
        })
        self.assertEqual(result, "Line 1\nLine 2")

        # 测试文件不存在
        non_existent = self.temp_dir / "nonexistent.txt"
        result = read_file({"path": str(non_existent)})
        self.assertIn(f"文件 {non_existent} 不存在", result)

        # 测试行号无效
        with self.assertRaises(ValueError) as exc_context:
            read_file({"path": str(file_path), "line_start": -1})
        self.assertIn("line_start 必须是大于 0 的整数", str(exc_context.exception))

    def test_edit_file(self):
        """测试编辑文件功能"""
        file_path = self.temp_dir / "test.txt"
        initial_content = "Line 1\nLine 2\nLine 3"
        file_path.write_text(initial_content, encoding="utf-8")

        # 测试插入操作
        edit_file({
            "path": str(file_path),
            "operation": "insert",
            "line_start": 2,
            "content": "Inserted line"
        })
        self.assertEqual(
            file_path.read_text(encoding="utf-8"),
            "Line 1\nInserted line\nLine 2\nLine 3"
        )

        # 测试替换操作
        edit_file({
            "path": str(file_path),
            "operation": "replace",
            "line_start": 2,
            "line_end": 2,
            "content": "Replaced line"
        })
        self.assertEqual(
            file_path.read_text(encoding="utf-8"),
            "Line 1\nReplaced line\nLine 2\nLine 3"
        )

        # 测试删除操作
        edit_file({
            "path": str(file_path),
            "operation": "delete",
            "line_start": 2,
            "line_end": 2
        })
        self.assertEqual(
            file_path.read_text(encoding="utf-8"),
            "Line 1\nLine 2\nLine 3"
        )

        # 测试无效操作
        with self.assertRaises(ValueError) as exc_context:
            edit_file({
                "path": str(file_path),
                "operation": "invalid",
                "line_start": 1
            })
        self.assertIn(
            "operation 必须是 'insert'、'replace' 或 'delete' 之一",
            str(exc_context.exception)
        )


if __name__ == "__main__":
    unittest.main()