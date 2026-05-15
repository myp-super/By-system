# 免费公网部署指南 — PythonAnywhere

无需银行卡，3步上线。

## 第1步：注册 PythonAnywhere

打开 [www.pythonanywhere.com](https://www.pythonanywhere.com) → 点击 **Create a Beginner account** → 填邮箱+用户名+密码即可完成注册，无需信用卡。

你会得到域名：`你的用户名.pythonanywhere.com`

## 第2步：上传代码

在 PythonAnywhere 控制台（Consoles 标签）打开一个 **Bash** 终端，运行：

```bash
# 克隆项目
git clone https://github.com/myp-super/By-system.git baoyan-web
cd baoyan-web/web

# 安装依赖
pip install --user -r requirements.txt
```

## 第3步：配置 Web App

1. 点击顶部 **Web** 标签 → **Add a new web app**
2. 选择 **Manual configuration** → 选择 **Python 3.11**
3. 在 **Code** 部分，修改 **WSGI configuration file** 链接，点击打开文件
4. 删除文件全部内容，粘贴以下代码：

```python
import sys
import os

# 你的项目路径（把 YOURUSERNAME 替换成你的 PythonAnywhere 用户名）
project_home = '/home/YOURUSERNAME/baoyan-web/web'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置数据目录
os.environ['BAOYAN_DATA_DIR'] = '/home/YOURUSERNAME/baoyan_data'

from app import app as application
```

5. 回到 Web 标签，在 **Working directory** 中填入：
   ```
   /home/YOURUSERNAME/baoyan-web/web
   ```

6. 点击顶部绿色 **Reload** 按钮

完成！访问 `你的用户名.pythonanywhere.com` 即可使用。

## 免费账户限制

| 项目 | 限制 |
|------|------|
| 运行时间 | 每天 100 秒 CPU |
| 外网访问 | 免费域名可以访问公开网站 |
| 强制停机 | 每 24 小时会重启一次 |
| 后台任务 | 不支持 |
| 磁盘空间 | 512 MB |

对于个人使用完全足够。如果需要更好的性能，可以考虑升级到付费计划（$5/月）。

## 自定义域名

如果你有自己的域名（如 example.com），PythonAnywhere 免费账户不支持绑定自定义域名。付费计划支持。
