# Changelog

本项目所有显著变更都记录在这里。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 新增
- 暂无

### 修复
- 暂无

---

## [0.2.0-bjyyy] - 2026-10-09

本分支首次发布。基于 [liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release) 改进。

### 新增

- **自定义 OpenAI 兼容 API**：服务端 web/server.py /api/config 接受 ase_url 字段，新增 provider: custom 路由到 llm.custom.*；xtractor/parser.py 新增 custom 分支读取自定义 base_url/model/api_key；config.example.yaml 增加注释示例；命令行 python main.py config --provider custom --base-url … --api-key … --model …
- **「测试连接」按钮**：UI 设置面板新增按钮，调用新增的 /api/test_config 端点做一次最小 LLM 调用（HumanMessage("ping")），返回 provider / model / base_url 真实回显 + 失败时返回完整 traceback
- **诊断.bat**：一键检测 Python 解释器、pip、关键依赖（flask / pywebview / langchain / yaml / sqlalchemy）、Edge WebView2 运行时、app.py 能否正常 import
- **覆盖 row UI 字段**：dashboard.html 首次配置弹窗 + 设置面板的服务商下拉新增「自定义 (OpenAI 兼容)」选项；选 custom 时显示 base_url / model 输入框；加载时回填已保存的 base_url
- **CLI 增强**：cli/commands.py 接受 openai 和 custom 作为 --provider 取值，并新增 --base-url 参数

### 修复

- **启动.bat 闪退**：原版用 UTF-8 编码写 bat，cmd.exe 按 GBK 解析时把中文注释当成命令执行，表现为「闪退」或「'XX' 不是内部或外部命令」。重写为纯 ASCII 编码，用 goto 标签代替嵌套 if 块，优先调用 python（用户已确认能用的命令），每步都有 pause 防止闪关
- **断点续传逻辑错误**：原版用 max_chapter = 507 这种「最大章节号」判断续传起点，导致 max 之前的所有章节即使未分析也会被跳过（如 169-276、316-414 这种大段缺口永远补不上）。改为逐章检查 events 表：只跳过已存在 event 的章节，自动识别并填补缺口
- **applier 损坏字段污染数据库**：原版 xtractor/applier.py 写入 events 时不校验类型，LLM 偶尔会把整段叙述写到 chapter_end 字段（如 nd='全联修罗战演练（第97-99章）小分队行踪……袭击'），导致后续 import 触发 TypeError: '>' not supported between instances of 'str' and 'int'。新增类型校验：chapter_start / chapter_end 必须能转 int，否则丢弃该字段并打印警告
- **server.py import 时 NUL 报错**：原 import 块用 >nul 2>&1 但缺 import re；新增 import re 配合新增的 _chapter_to_int() 辅助函数安全转换

### 变更

- **移除 -OO 优化标志**：原启动.bat 用 python -OO app.py 启动，-OO 会移除 assert 和 docstring，pywebview 内部可能依赖其中之一。改为 python -u app.py（无缓冲输出，错误能立刻看到）
- **README 重写**：开头明确致谢原作者，所有改进列表化展示，CLI / 故障排查 / 致谢三个章节补充
- **.gitignore 增补 *.docx**：避免误提交测试章节文件

### 已知问题

- 大量 session 记录的 db_operations 字段为空（146 批左右，集中在 1-700 章范围），这些是 LLM 返回无效 JSON 的批次。本分支没有自动重新分析的入口（用户可以删 events 对应记录后重跑，或者在「设置」里改 model 后重试）

### 致谢

本分支的 7 项改进由 [BingJYYY](https://github.com/BingJYYY) 在使用原版 [liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release) 过程中发现并修复。

如果原作者愿意合并部分改进，欢迎提 PR。

---

## 历史版本

### 0.1.0（原作者版本）

见 [liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release) 的 commit 历史。