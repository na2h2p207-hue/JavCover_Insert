# Mosaic Rename (JavCover)

自动重命名 JAV 视频文件的工具，从 JavTrailers 获取日语标题，下载封面并嵌入 MP4。

现在提供 **JavCover** GUI 应用——只需双击 `.exe` 即可使用，无需安装 Python。

## 📦 下载

前往 [Releases](https://github.com/na2h2p207-hue/JavCover_Insert/releases) 下载最新 `JavCover.exe`，双击运行即可。

## 🌟 核心特性

- **完全兼容 SHT 网站格式**：无论下载的原始文件名包含多复杂的后缀或前缀，都能精准提取番号并清理重命名。
- **智能标题解析**：自动移除从 JavTrailers 获取的冗余演员名及多余的罗马音后缀。
- **特征标签保留**：重命名时自动识别并原样保留 `无码-lada`、`-C` 等关键版本线索，拒绝由于重命名丢失高清/无码说明。
- **视频结构修复**：内置验证逻辑，自动拦截并利用 FFmpeg 修复由 LosslessCut 等第三方剪辑工具造成的 `dat` atom 损坏。
- **Faststart 优化**：全自动将 MP4 的 `moov` atom 前置到文件首部，让视频在网页端和播放器中实现“秒开”缓冲。
- **安全封面嵌入**：将封面智能裁剪为完美的 378:538 比例，通过 Mutagen 底层库安全注入视频元数据。
- **极致 GUI 体验**：基于 PyWebView 的跨级桌面客户端，采用原生响应液态玻璃 (Liquid Glass) 设计语法，支持明亮/暗黑自适应主题。
- **实时封面预览与保存**：在提取信息时可以在界面中实时看到处理好比例的完美封面预览图，同时所有的封面文件也会整洁地保存在自定义本地文件夹中。
  <br><img src="images/generated-1771221918008.png" width="300" alt="Cover Preview Example">
- **多工作流兼容**：完全支持一键批量处理，亦可通过 GUI 界面进行单文件手动精准修复。

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

| 格式 | 示例 | 支持说明 |
|------|------|----------|
| 标准带连字符 | `ABW-009` | 完美解析 |
| 无连字符 | `iptd00764` → `IPTD-764` | 自动补全连字符并去除多余零前缀 |
| DV 系列 (4 位) | `DV-1234` | 自动识别匹配 DV 专属 4 位数规则 |
| SHT 网站专属 | `[SHT] SSNI-123_FHD...` | 自动剥离干扰前缀后缀 |
| 复杂特殊字串 | `h_086ssni123` | 深度正则匹配提取代码序列 |

## 许可证

本项目仅供个人学习使用。
