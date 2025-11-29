# Code Agent

agent有三种基本架构：ReAct，plan and solve，reflection三种模式。

- **ReAct (Reasoning and Acting)：** 一种将“思考”和“行动”紧密结合的范式，让智能体边想边做，动态调整。

  核心在于循环 Thought-Action-Observation 这整个过程，在思考当前情况的时，反思上一步结果指定下一步计划，形成一个不断增长的上下文。最终能够达到：**推理让行动更具有目的性，行动为推理提供实时依据，观察则用于不断优化每次的推理**。

- **Plan-and-Solve：** 一种“三思而后行”的范式，智能体首先生成一个完整的行动计划，然后严格执行。

  核心在于 原始问题，完整计划，历史步骤和结果，当前步骤 这整个思路

- **Reflection：** 一种赋予智能体“反思”能力的范式，通过自我批判和修正来优化结果。

  先完成整个问题，再审视前面的结果进行反思，常见会通过 ”事实错误，逻辑漏洞，效率问题，遗漏信息等“ 多个常见的不同角度进行反思，对初稿进行反复修改，形成更完善的修订稿。


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

##### prompt

提示词的基本要素在于：指令（模型需要执行的任务或命令），上下文（包含的外部信息或者额外的上下文信息），输入数据，输出指示。

另外更加具体的描述：可以在提示词中添加角色，可用的额外工具，少量的样本提示等，以期达到最好的效果。

- 角色定义
- 工具清单（tools）
- 格式规约（thought/action）
- 动态上下文（memory）
- 少样本提示

##### memory

```txt
context_compressor
	- should_compress 	当对话轮数大于a时，需要压缩
	- compress 			保留最近b条对话和第1条系统prompt，其余压缩
	- _extract_key_information 提取(a-b-1)条信息的摘要，包括文件路径，执行工具，错误信息，任务完成情况四类
	- get_compression_status   获取压缩信息（原信息，压缩后信息，压缩率，节省的消息数量）
```

