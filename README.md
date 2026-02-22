# Mosaic Rename (JavCover)

自动重命名 JAV 视频文件的工具，从 JavTrailers 获取日语标题，下载封面并嵌入 MP4。

现在提供 **JavCover** GUI 应用——只需双击 `.exe` 即可使用，无需安装 Python。

## 📦 下载

前往 [Releases](https://github.com/na2h2p207-hue/JavCover_Insert/releases) 下载最新 `JavCover.exe`，双击运行即可。

## 功能

- **自动重命名**：从文件名提取番号，获取日语标题，重命名为 `CODE 标题.mp4`
- **封面嵌入**：下载封面图，裁剪右半部分后嵌入 MP4 文件元数据
- **FC2 支持**：支持 FC2-PPV 格式视频
- **GUI 应用**：PyWebView 驱动的桌面 GUI，支持明暗主题切换
- **批处理 / 单文件**：支持文件夹批量处理和单文件手动修复

## 截图

### 明亮主题
![Light Theme](images/light.jpg)

### 暗黑主题
![Dark Theme](images/dark.jpg)

## 项目结构

```
├── JavCover_WebView.py     # GUI 主程序（PyWebView）
├── gui/
│   ├── index.html          # 前端结构
│   ├── style.css           # 样式（含液态玻璃效果）
│   └── script.js           # 前端逻辑
├── rename/
│   ├── rename_movies.py    # 核心重命名逻辑
│   ├── manual_fix.py       # 单文件手动修复
│   ├── fc2_scraper.py      # FC2 元数据抓取
│   └── faststart.py        # FFmpeg faststart 工具
└── archive/
    └── build_artifacts/
        └── JavCover.spec   # PyInstaller 打包配置
```

## 命令行使用

如果不想使用 GUI，也可以直接用命令行：

### 批量处理

```powershell
# 预览模式（不实际改名）
python rename/rename_movies.py --dir "H:\Videos" --dry-run

# 实际执行
python rename/rename_movies.py --dir "H:\Videos"
```

### 手动修复单文件

```powershell
python rename/manual_fix.py "路径\视频.mp4"
```

## 依赖

仅在从源码运行时需要：

```bash
pip install pywebview pythonnet cloudscraper mutagen Pillow requests
```

## 番号格式

| 格式 | 示例 |
|------|------|
| 标准 | `ABW-009`, `IPTD-764` |
| 无连字符 | `iptd00764` → `IPTD-764` |
| FC2 | `FC2-PPV-1234567` |
| DV 系列 | `DV-1234`（4 位数）|

## 许可证

本项目仅供个人学习使用。
