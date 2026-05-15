# 保研全程管理 v5

Web 端保研申请全流程管理系统。Flask 后端 + 原生 HTML/CSS/JS 前端，企业级专业 UI。

## 功能概览

| 模块 | 说明 |
|------|------|
| **首页仪表盘** | 统计数据、即将截止提醒、待跟进导师、最近项目 |
| **保研通知** | 嵌入 baoyantongzhi.com 实时夏令营/预推免通知，iframe 内直接浏览 |
| **硕士专业查询** | 520 所研招网院校 + 338 个真实硕士专业数据，支持学科评估详情 |
| **申请进度看板** | 拖拽卡片在不同状态列之间移动，实时更新 |
| **我的项目库** | 院校申请项目管理，含材料清单、时间节点、状态跟踪 |
| **时间节点** | 关键日期管理，临近/过期高亮提醒 |
| **材料管理** | 每项材料状态跟踪（未开始/进行中/已完成），支持关联本地文件 |
| **面试记录** | 面试日期、形式、问题、星级评分、经验总结 |
| **导师联系** | 导师邮件往来记录，待跟进高亮提醒 |
| **文书模板库** | 批量上传/下载（ZIP），原格式存储，支持预览 Word/PDF/Excel/TXT |
| **数据导出** | 一键导出全部数据为 Excel 文件 |

## 快速开始

```bash
cd web
pip install -r requirements.txt
python app.py
```

浏览器打开 **http://localhost:5000**

首次运行自动创建数据库 `~/baoyan_data/data.db`，并预置 520 所院校 + 338 个硕士专业数据。

## 项目结构

```
web/
├── app.py                  # Flask 后端，REST API
├── launcher.py             # PyInstaller 打包入口
├── run.py                  # 生产模式入口 (waitress)
├── startup.bat             # Windows 开机自启脚本
├── build_exe.py            # PyInstaller 打包脚本
├── requirements.txt        # Python 依赖
├── scraper.py              # 研招网院校数据采集
├── seed_db.py              # 数据库初始化/种子数据
├── data/                   # 数据文件
│   ├── seed_data.py        # 硕士专业 & 夏令营种子数据
│   ├── university_details.py  # 学科评估数据
│   └── all_universities.json  # 520 所研招网院校
├── templates/
│   └── index.html          # 单页应用 HTML
├── static/
│   ├── css/style.css       # 企业级 UI 样式
│   └── js/app.js           # 前端逻辑
└── uploads/                # 上传文件存储 (~/baoyan_data/uploads/)
```

## 24/7 运行

**本机开机自启**:
1. `Win + R` → `shell:startup` → 回车
2. 创建快捷方式指向 `web/startup.bat`
3. 开机后自动在 `http://localhost:5000` 运行

**命令行启动**:
```bash
cd web
python run.py    # 生产模式 (waitress)
```

## 打包为 .exe

```bash
cd web
pip install pyinstaller
python build_exe.py
```

输出: `dist/保研管理.exe`，双击启动后自动打开浏览器。

## 技术栈

- **后端**: Flask + SQLAlchemy + SQLite
- **前端**: 原生 HTML/CSS/JS (Fira Sans + Fira Code 字体)
- **数据处理**: pandas, openpyxl, pdfplumber, python-docx
- **生产部署**: waitress (WSGI)
- **打包**: PyInstaller (单文件 .exe)
- **数据来源**: 中国研究生招生信息网 (yz.chsi.com.cn) 520 所院校 + 教育部第四轮学科评估

## License

MIT
