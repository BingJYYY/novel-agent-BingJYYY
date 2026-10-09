<div align="center">

# 📖 网文动态大纲智能体
### Novel Outline Agent

**用 AI 自动分析网文章节，提取动态大纲、人物关系、伏笔与冲突。**

[![release](https://img.shields.io/github/v/release/BingJYYY/novel-agent-BingJYYY)](https://github.com/BingJYYY/novel-agent-BingJYYY/releases)
[![License](https://img.shields.io/github/license/BingJYYY/novel-agent-BingJYYY)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#-环境要求)

原作者：[liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release) · 改进与发布：[BingJYYY](https://github.com/BingJYYY/novel-agent-BingJYYY)

</div>

---

一个专为长期连载小说设计的 AI 智能体，帮你自动提取角色、事件、世界观、伏笔，维护动态大纲数据库。

## 它能干什么？

写小说或拆书时，几百章之后最头疼的是什么？忘了某个角色第几章出场、忘了某个伏笔埋了没埋、忘了主角什么时候升的级。这个工具就是帮你解决这些问题的：

- **提交新章节** → AI 自动分析，提取角色、事件、设定、伏笔
- **整本导入** → 把 txt 文件丢进去，自动分章逐批分析，几百章的书几十分钟搞定
- **实时查看** → 浏览器（或桌面窗口）里随时查看所有角色、事件、伏笔、关系、时间线
- **增量更新 / 断点续传** → 每次只分析新内容；中途中断后重启会从上次成功的章节继续，不会重头再来
- **设定冲突检测** → 自动检查前后矛盾的地方，提醒你注意

## 本分支相比原版的改进

| # | 改进点 | 说明 |
|---|--------|------|
| 1 | 启动.bat 闪退修复 | 改用纯 ASCII 编码 + goto 标签重写，解决 cmd 把中文当命令解析的 bug |
| 2 | 自定义 OpenAI 兼容 API | 配置面板新增「自定义 (OpenAI 兼容)」选项，可填 base_url / model，兼容 Moonshot / Ollama / 任意代理 |
| 3 | 「测试连接」按钮 | 配置完 API 后一键测试，立刻反馈 base_url / model 是否正确 |
| 4 | 断点续传修复 | 改为逐章判断 events 表，跳过已存在章节的同时**自动填补缺口**（不再因 max_chapter 误判而漏掉章节） |
| 5 | applier 类型校验 | 写入前校验 chapter_start / chapter_end 必须能转 int，丢弃损坏的字段而不是污染数据库 |
| 6 | 诊断.bat | 一键检测 Python 装没装、依赖齐不齐、WebView2 装没装 |

## 📦 快速开始

### 环境要求

- **Python 3.10+**（推荐 3.11）
- **Windows 10/11**（自带 WebView2）；macOS / Linux 需自行安装 WebView2 运行时
- 任意能调用 OpenAI Chat Completions 接口的服务（OpenAI、DeepSeek、智谱、Ollama、月之暗面 等）

### 1. 下载与安装依赖

前往 [Releases](https://github.com/BingJYYY/novel-agent-BingJYYY/releases) 下载最新 ZIP 并解压，或：

```bash
git clone https://github.com/BingJYYY/novel-agent-BingJYYY.git
cd novel-agent-BingJYYY
```

安装依赖（**必需**，项目使用了 Flask / langchain / pywebview 等第三方库）：

```bash
python -m pip install -r requirements.txt
```

> pip 慢？临时用国内镜像：
> ```bash
> python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
> ```

### 2. 配置 API

复制示例配置：

```bash
copy config.example.yaml config.yaml     # Windows
# 或
cp config.example.yaml config.yaml       # macOS / Linux
```

打开 `config.yaml`，填入你的 API Key：

```yaml
provider: openai        # openai / anthropic / azure / custom
api_key: sk-xxxxxxxxxxxx
model: gpt-4o-mini
```

### 3. 启动

**Windows**：直接双击 `启动.bat`

**任意系统**：

```bash
python app.py
```

浏览器会自动打开 http://localhost:5000

## 🔧 配置自定义 API（OpenAI 兼容）

Web UI → 右上角「设置」 → 服务商选 **「自定义 (OpenAI 兼容)」**：

| 字段 | 示例 |
|------|------|
| API Base URL | `https://api.deepseek.com/v1` |
| API Key | `sk-xxxxxxxxxxxx` |
| Model | `deepseek-chat` |

点 **「测试连接」** 验证配置无误后再保存。

支持所有 `/v1/chat/completions` 兼容端点：

- DeepSeek · `https://api.deepseek.com/v1`
- 智谱 GLM · `https://open.bigmodel.cn/api/paas/v4`
- 月之暗面 Kimi · `https://api.moonshot.cn/v1`
- Ollama（本地）· `http://localhost:11434/v1`，**API Key 可留空**
- SiliconFlow、OpenRouter、自建网关……任何兼容 OpenAI 协议的服务都行

## 🛠️ 故障排查

启动报错或分析卡住？把诊断输出复制给 AI 助手（**Codex / DeepSeek / Claude / ChatGPT** 等），它能直接帮你定位问题：

**Windows**：双击 `诊断.bat`，它会输出 Python 版本、依赖、WebView2 等检测结果。

**任意系统**：

```bash
python -c "import sys, flask, yaml, requests, webview; print(sys.version)"
```

把下面几样贴给 AI 助手即可：

1. 完整的报错堆栈（终端或弹窗里那段红色文字）
2. `诊断.bat` 的输出
3. 你的操作系统 / Python 版本
4. 你想实现的目标

> 💡 **不需要**找"开发者"或"原作者"——AI 助手拿到以上信息后通常一两轮对话就能定位到具体文件和行号。

| 现象 | 解决方法 |
|------|---------|
| 双击 `启动.bat` 没反应 | 跑 `诊断.bat`，看 Python / 依赖 / WebView2 哪个出问题 |
| `TypeError: '>' not supported between instances of 'str' and 'int'` | 升级到本分支；旧版在 chapter_end 损坏时会崩溃，本分支已修复 |
| 整本导入后看不到数据，但章节数显示正常 | 在「设置」里点「测试连接」，看是不是 base_url / model 配错 |
| 断网 / API 限流 | 单批失败会自动重试 1 次；整本导入可重新触发，已成功章节不会重复 |
| pywebview 启动闪退 | 安装 Edge WebView2 运行时：https://developer.microsoft.com/microsoft-edge/webview2/ |

## 📂 项目结构

```
novel-agent-BingJYYY/
├── app.py                  # Web 入口（pywebview 启动 Flask）
├── 启动.bat                # Windows 一键启动
├── 诊断.bat                # Windows 一键诊断
├── config.example.yaml     # 配置示例
├── requirements.txt        # 依赖列表
├── web/
│   ├── server.py           # Flask 路由
│   └── templates/          # HTML 模板
├── extractor/
│   ├── parser.py           # 章节解析 + LLM 调用（多 provider）
│   └── applier.py          # 分析结果写入数据库
├── cli/
│   └── commands.py         # 命令行入口
└── novel.db                # 运行时数据（分析结果）
```

## 🤝 致谢

本项目基于 [liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release) 改进。

原作者：[liu220738-sys](https://github.com/liu220738-sys) · 改进与发布：[BingJYYY](https://github.com/BingJYYY/novel-agent-BingJYYY)

## 📄 License

本项目使用 **MIT License** —— 详见 [LICENSE](LICENSE) 文件。
