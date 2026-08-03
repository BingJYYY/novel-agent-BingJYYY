#!/usr/bin/env python3
"""
小说动态大纲与快速阅读智能体

用法：
    python main.py submit -f chapter.txt -c "第5-7章"
    python main.py submit                    # 交互式粘贴
    python main.py quick -f chapter.txt      # 快速阅读模式
    python main.py query status              # 查看数据库状态
    python main.py query characters          # 查看角色
    python main.py query events              # 查看事件
    python main.py query full                # 输出完整大纲
    python main.py config --show             # 查看配置
    python main.py config --provider deepseek --api-key sk-xxx
"""

from cli.commands import cli

if __name__ == "__main__":
    cli()
