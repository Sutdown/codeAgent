### code agent

##### client

```txt
client
	- base_client：    抽象基类
		- send_recv：  向LLM API发送和接收消息
		- extract_txt：从响应消息中提取文本
		- chat：send_recv and extract_txt
```

##### tools

核心工具模块，提供了智能体（Agent）可调用的各类工具函数，支持文件操作、代码执行、代码分析等核心功能，是智能体与外部环境交互的主要接口。

```txt
file_tools
	- create_file    创建或者覆盖文本文件
	- read_file      读取文件内容
	- list_directory 列出当前目录内容
	- edit_file      编辑文件的指定行（插入，替换，删除）
	- search_in_file 在文件中搜索文本or正则表达式，支持上下文显示
execution_tools
	- run_python 运行python代码or脚本
	- run_shell  运行shell命令
	- run_tests  运行python测试套件
	- run_linter 运行代码检查/格式化工具
code_analysis_tools
	- parse_ast              解析Python文件的AST抽象语法树提取代码信息
	- get_function_signature 提取指定函数的签名
	- find_dependencies      分析文件的依赖关系
	- get_code_metrics       获取代码度量信息
```


