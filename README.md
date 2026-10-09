# 📖 网文动态大纲智能体（BJYYY 改进版）

> 本项目是 [liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release) 的改进分支。
> 原作者：[liu220738-sys](https://github.com/liu220738-sys) · 本分支改进者：[BingJYYY](https://github.com/BingJYYY)
> 完整改动见 [CHANGELOG.md](./CHANGELOG.md)

一个专为长期连载小说设计的 AI 智能体，帮你自动提取角色、事件、世界观、伏笔，维护动态大纲数据库。

---

## 它能干什么？

写小说或拆书时，几百章之后，最头疼的是什么？忘了某个角色第几章出场、忘了某个伏笔埋了没埋、忘了主角什么时候升的级。

这个工具就是帮你解决这些问题的：

- **提交新章节** → AI 自动分析，提取角色、事件、设定、伏笔
- **整本导入** → 把 txt 文件丢进去，自动分章逐批分析，几百章的书几十分钟搞定
- **实时查看** → 浏览器（或桌面窗口）里随时查看所有角色、事件、伏笔、关系、时间线
- **增量更新** → 每次只分析新内容，不会重复处理旧章节
- **设定冲突检测** → 自动检查前后矛盾的地方，提醒你注意

---

## 本分支相比原版的改进

详细见 [CHANGELOG.md](./CHANGELOG.md)，简要列表：

| # | 改进点 | 说明 |
|---|--------|------|
| 1 | 启动.bat 闪退修复 | 改用纯 ASCII 编码 + goto 标签重写，解决 cmd 把中文当命令解析的 bug |
| 2 | 自定义 OpenAI 兼容 API | 配置面板新增「自定义 (OpenAI 兼容)」选项，可填 base_url / model，兼容 Moonshot / Ollama / 任意代理 |
| 3 | 「测试连接」按钮 | 配置完 API 后一键测试，立刻反馈 base_url / model 是否正确 |
| 4 | 断点续传修复 | 改为逐章判断 events 表，跳过已存在章节的同时**自动填补缺口**（不再因 max_chapter 误判而漏掉章节） |
| 5 | applier 类型校验 | 写入前校验 chapter_start / chapter_end 必须能转 int，丢弃损坏的字段而不是污染数据库 |
| 6 | 诊断.bat | 一键检测 Python 装没装、依赖齐不齐、WebView2 装没装 |
| 7 | CLI 支持 custom provider | python main.py config --provider custom --base-url … --model … --api-key … |

---

## 快速开始

### 第一步：安装 Python

需要 Python 3.9+。到 https://www.python.org/downloads/ 下载安装。
**安装时勾选 "Add Python to PATH"。**

### 第二步：克隆仓库

`ash
git clone https://github.com/BingJYYY/novel-agent-bjyyy.git
cd novel-agent-bjyyy
`

### 第三步：双击 启动.bat（Windows）

启动.bat 会自动：
1. 检测 Python 解释器
2. 安装缺失的依赖
3. 启动桌面应用

**如果双击后没反应**，请双击 诊断.bat，把输出截图发给开发者。

### 第四步：配置 API

启动后会自动弹出配置弹窗：
- **DeepSeek / 通义千问 / 智谱 GLM / OpenAI**：选对应服务商，填 API Key
- **其他 OpenAI 兼容服务（Moonshot / Ollama / 代理）**：选「自定义 (OpenAI 兼容)」，填 base_url + 模型名 + API Key
- 填完点「**测试连接**」验证配置正确，再保存

> 怎么获取 API Key？
> - DeepSeek：https://platform.deepseek.com/
> - 通义千问：https://bailian.console.aliyun.com/
> - 智谱 GLM：https://open.bigmodel.cn/
> - 月之暗面：https://platform.moonshot.cn/

### 第五步：导入小说

1. 切换到「提交章节」标签
2. 点击「📂 整本导入」选择 txt 文件
3. 等待自动分析完成

txt 文件需包含「第X章」标记，如 第1章 觉醒日。橙瓜、作家助手等导出的 txt 均可直接使用。

---

## 命令行使用

`ash
# 从文件提交章节
python main.py submit -f chapter.txt -c "第5-7章"

# 交互式提交（粘贴正文）
python main.py submit

# 快速阅读（不维护数据库）
python main.py quick -f chapter.txt

# 查看数据库状态
python main.py query status

# 查看所有角色 / 事件 / 完整大纲
python main.py query characters
python main.py query events
python main.py query full

# 配置 LLM（含自定义 provider）
python main.py config --provider deepseek --api-key sk-xxx
python main.py config --provider custom --base-url https://api.moonshot.cn/v1 --api-key sk-xxx --model moonshot-v1-8k

# 在浏览器中打开仪表盘（不用桌面应用）
python main.py serve
`

---

## Web 仪表盘标签页

| 标签 | 内容 |
|------|------|
| 提交章节 | 粘贴正文、整本导入 |
| 概览 | 数据库状态摘要，主角信息 |
| 角色 | 所有角色卡片，含状态变更历史 |
| 事件 | 按事件段展示，区分进行中/已完成 |
| 设定 | 世界观设定，按分类分组 |
| 伏笔 | 未解决/推进/已回收分类展示 |
| 时间线 | 按故事时间排序的事件流 |
| 冲突 | 自动检测到的设定矛盾 |
| 设置 | LLM 服务商 / API Key / 模型配置 |

---

## 故障排查

| 现象 | 解决方法 |
|------|---------|
| 双击 启动.bat 没反应 | 跑 诊断.bat，看 Python / 依赖 / WebView2 哪个出问题 |
| TypeError: '>' not supported between instances of 'str' and 'int' | 升级到本分支，旧版会在 chapter_end 损坏时崩溃；本分支已修复 |
| 整本导入后看不到数据，但章节数显示正常 | 在「设置」里点「测试连接」，看是不是 base_url / model 配错 |
| 断网 / API 限流 | 单批失败会自动重试 1 次；整本导入可重新触发，已成功章节不会重复 |
| pywebview 启动闪退 | 安装 Edge WebView2 运行时：https://developer.microsoft.com/microsoft-edge/webview2/ |

---

## 致谢

- 原项目：[liu220738-sys/novel-agent-release](https://github.com/liu220738-sys/novel-agent-release)
- 提示词设计、数据库模型、核心提取逻辑来自原作者
- 本分支的贡献：见 [CHANGELOG.md](./CHANGELOG.md) 的版本记录

## License

MIT