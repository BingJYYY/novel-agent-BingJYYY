# 📖 网文动态大纲智能体

> 一个专为长期连载小说设计的 AI 智能体，帮你自动提取角色、事件、世界观、伏笔，维护动态大纲数据库。

## 它能干什么？

你写小说或拆书时，最头疼的是什么？几百章之后，忘了某个角色第几章出场、忘了某个伏笔埋了没埋、忘了主角什么时候升的级。

这个工具就是帮你解决这些问题的：

- **提交新章节** → AI 自动分析，提取角色、事件、设定、伏笔
- **整本导入** → 把 txt 文件丢进去，自动分章逐批分析，几百章的书几十分钟搞定
- **实时查看** → 浏览器（或桌面窗口）里随时查看所有角色、事件、伏笔、关系、时间线
- **增量更新** → 每次只分析新内容，不会重复处理旧章节
- **设定冲突检测** → 自动检查前后矛盾的地方，提醒你注意

---

## 核心功能一览

| 功能 | 说明 |
|------|------|
| 📝 提交章节 | 粘贴章节正文，AI 自动分析入库 |
| 📦 整本导入 | 上传 txt 文件，自动分章批量分析，支持断点续传 |
| 👤 角色数据库 | 所有角色的等级、身份、阵营、能力、状态变更历史 |
| 🎬 事件大纲 | 按事件段划分，不是逐章流水账 |
| 🌍 世界观设定 | 力量体系、势力、地点、规则……按分类整理 |
| 🔮 伏笔追踪 | 未解决 → 推进 → 已回收，全程追踪 |
| ⏱️ 时间线 | 故事内部时间顺序，区分明确/相对/模糊时间 |
| ⚠️ 设定冲突 | 自动检测前后矛盾 |
| 🔗 关系数据库 | 人物之间的阵营、信任、合作/敌对关系 |
| 📚 多小说管理 | 同时管理多部小说，数据互不干扰 |

---

## 目录结构

```
novel-agent/
├── main.py                     # CLI 命令行入口
├── app.py                      # 桌面应用启动器
├── 启动.bat                     # 双击启动（Windows）
├── requirements.txt            # Python 依赖
├── config.example.yaml         # 配置模板（也可用环境变量或命令行，无需修改）
├── .gitignore                  # Git 忽略规则
│
├── db/                         # 数据库层
│   ├── models.py               # 14 张表的 SQLAlchemy 模型
│   └── repository.py           # 所有 CRUD 操作
│
├── extractor/                  # AI 分析层
│   ├── prompt.py               # 系统提示词（在这里自定义你的分析规则）
│   ├── parser.py               # LLM 调用与响应解析
│   └── applier.py              # 将 AI 输出写入数据库
│
├── cli/                        # 命令行界面
│   └── commands.py             # submit / quick / query / config / serve 命令
│
└── web/                        # Web 仪表盘
    ├── server.py               # Flask 后端
    ├── static/
    └── templates/
        └── dashboard.html      # 仪表盘前端页面
```

---

## 快速开始

### 第一步：安装 Python

需要 Python 3.10 或以上版本。如果没有，去 [python.org](https://www.python.org/) 下载安装。

安装时 **勾选 "Add Python to PATH"**。

### 第二步：安装依赖

打开终端（PowerShell 或 CMD），进入项目目录：

```bash
cd "d:\novel-agent-release"
pip install -r requirements.txt
```

### 第三步：配置 API Key

**方式一：弹窗直接填写（推荐，启动后自动弹出）**

双击 `启动.bat` 或运行 `python main.py serve`，页面会自动弹出配置弹窗，选择服务商、填入 API Key 即可。

**方式二：仪表盘设置页**

启动后点击右上角 **⚙️ 设置** 标签页，也可以修改配置。

**方式三：设置环境变量**

```bash
# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="sk-你的密钥"

# Windows (CMD)
set DEEPSEEK_API_KEY=sk-你的密钥

# Linux / Mac
export DEEPSEEK_API_KEY=sk-你的密钥
```

支持的变量名：`DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY`（通义） / `ZHIPU_API_KEY`（智谱） / `OPENAI_API_KEY`

**方式四：命令行**

```bash
python main.py config --api-key sk-你的密钥
```

> **怎么获取 API Key？**
> - DeepSeek：去 [platform.deepseek.com](https://platform.deepseek.com/) 注册，在 API Keys 页面创建
> - 通义千问：去 [阿里云百炼](https://bailian.console.aliyun.com/) 
> - 智谱 GLM：去 [open.bigmodel.cn](https://open.bigmodel.cn/)

### 第四步：启动

**双击 `启动.bat`** 即可。会自动打开桌面应用窗口。

如果想在浏览器中使用，运行：

```bash
python main.py serve
```

然后打开浏览器访问 `http://127.0.0.1:15000`。

---

## 使用方式

### 日常写作使用（写一章分析一章）

1. 打开应用，在「提交章节」页面粘贴你刚写好的章节正文
2. 填写章节号，如 `第5章`
3. 首次使用时填一下主角名
4. 点击「提交分析」，几秒钟后分析结果就出来了
5. 切换到「角色」「事件」等标签页查看更新

### 拆书使用（分析别人或自己的整本小说）

1. 点击右上角小说名，新建一部小说
2. 在「提交章节」页面点击「📂 整本导入」
3. 选择你的 txt 文件（需要包含 "第X章" 格式的章节标记）
4. 等待自动分析完成（150 万字的书大约 30-50 分钟）
5. 去喝杯咖啡，回来全部数据已在数据库中

### 断点续传

如果导入中断了（关了页面、网络断了），再次导入同一个文件，系统会自动跳过已完成的章节，从中断处继续。

---

## Web 仪表盘说明

| 标签页 | 内容 |
|--------|------|
| **提交章节** | 粘贴正文、选择文件、整本导入 |
| **概览** | 数据库状态摘要，主角信息，进行中的事件 |
| **角色** | 所有角色卡片，支持搜索，含状态变更历史 |
| **事件** | 按事件段展示，区分进行中/已完成/已锁定 |
| **设定** | 世界观设定，按分类（力量体系/势力/地点等）分组 |
| **伏笔** | 未解决/推进/已回收分类展示 |
| **时间线** | 按故事时间排序的事件流 |
| **冲突** | 自动检测到的设定矛盾 |

---

## 常用命令

```bash
# 从文件提交章节
python main.py submit -f chapter.txt -c "第5-7章"

# 交互式提交（粘贴正文）
python main.py submit

# 快速阅读（不维护数据库）
python main.py quick -f chapter.txt

# 查看数据库状态
python main.py query status

# 查看所有角色
python main.py query characters

# 查看所有事件
python main.py query events

# 输出完整动态大纲
python main.py query full
```

---

## 自定义提示词

提示词已内置在 `extractor/prompt.py` 中，开箱即用。如果你有特殊需求，可以直接编辑 `SYSTEM_PROMPT` 变量，调整分析规则、输出格式等。

提示词越详细，分析结果越符合你的需求。

---

## 支持的 AI 模型

| 服务商 | 模型 | 费用参考 |
|--------|------|---------|
| DeepSeek | deepseek-chat | ¥2/百万 tokens 输入 |
| 通义千问 | qwen-plus | 略有差异 |
| 智谱 GLM | glm-4 | 略有差异 |

所有模型都通过 OpenAI 兼容接口调用，部分模型免费额度足够日常使用。

---

## 注意事项

1. **不要上传真实 API Key**：`config.yaml` 已在 `.gitignore` 中排除，上传代码时不会包含
2. **不要上传小说数据**：`.db` 文件和 `novels.json` 已在 `.gitignore` 中排除
3. **定期备份**：你的分析数据存在 `.db` 文件中，建议定期复制备份
4. **章节格式**：导入 txt 文件时，章节需要包含「第X章」标记，如 `第1章 觉醒日`
5. **断网重连**：如果 API 调用失败，工具会自动重试一次，仍失败会跳过当前批次继续

---

## 常见问题

**Q: 导入中断了怎么办？**
A: 重新导入同一个文件，系统会自动跳过已分析的章节，从中断处继续。

**Q: 可以同时管理多部小说吗？**
A: 可以。点击右上角小说名，新建小说即可。每部小说独立一个数据库。

**Q: 分析结果不对怎么办？**
A: 可以编辑 `extractor/prompt.py` 中的提示词，调整分析规则让 AI 更符合你的习惯。

**Q: 数据存在哪？**
A: SQLite 数据库文件（`novel.db` 或 `novel-小说名.db`），可用 [DB Browser for SQLite](https://sqlitebrowser.org/) 直接打开查看。

---

## License

MIT
