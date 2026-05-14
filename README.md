# 保研全程管理

帮助你高效管理保研申请全过程的桌面应用程序。

## 功能概览

- **首页仪表盘** — 统计数据、即将截止提醒、最近项目与待跟进导师
- **院校项目库** — 表格管理所有申请项目，支持增删改查与多维度筛选
- **申请进度看板** — 卡片拖拽式看板，按状态分列展示申请流程
- **时间节点** — 记录关键日期，桌面提醒未来3天到期节点
- **材料管理** — 跟踪每项材料完成状态，设置本地文件路径
- **面试记录** — 记录面试问题、评分、经验总结
- **导师联系** — 管理导师邮件往来，跟进提醒高亮
- **文书模板库** — 分类存储常用文书片段，一键复制到剪贴板
- **数据导出** — 导出全部数据为 Excel 文件（含多个工作表）

## 环境要求

- Python 3.10+
- Windows / macOS / Linux

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行程序
python main.py
```

首次运行会自动在 `~/baoyan_data/` 下创建 `data.db` 数据库。

## 项目结构

```
├── main.py              # 程序入口，主窗口和导航
├── models.py            # SQLAlchemy ORM 模型定义
├── database.py          # 数据库初始化、会话管理、CRUD 函数
├── utils.py             # 导出Excel、桌面通知、剪贴板操作
├── scheduler.py         # 后台提醒检查线程
├── build.py             # PyInstaller 打包脚本
├── requirements.txt     # Python 依赖
├── README.md            # 本文件
└── ui/
    ├── __init__.py
    ├── dashboard.py     # 首页仪表盘
    ├── project_list.py  # 院校项目库
    ├── kanban.py        # 看板视图
    ├── timeline.py      # 时间节点管理
    ├── materials.py     # 材料管理
    ├── interviews.py    # 面试记录
    ├── mentors.py       # 导师联系
    └── templates.py     # 文书模板
```

## 打包为独立可执行文件

```bash
# 安装打包工具
pip install pyinstaller

# 使用打包脚本（推荐）
python build.py

# 清理后重新打包
python build.py --clean
```

打包后，可执行文件位于 `dist/` 目录下。

## 设置开机自启

### Windows
1. 按 `Win + R`，输入 `shell:startup`，回车打开启动文件夹
2. 将 `dist/保研管理.exe` 的快捷方式复制到该文件夹

### macOS
1. 打开 系统设置 → 通用 → 登录项
2. 点击 + 号，添加 `dist/保研管理.app`

## 技术栈

- **UI 框架**: PyQt5
- **数据库**: SQLite + SQLAlchemy ORM
- **数据处理**: pandas, openpyxl
- **桌面通知**: plyer
- **打包**: PyInstaller

## License

MIT
