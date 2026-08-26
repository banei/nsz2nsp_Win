# NSZ Converter (Windows)

独立的 NSZ → NSP 转换桌面工具，面向 Nintendo Switch 游戏文件。提供图形界面与命令行两种使用方式。

**仓库地址：** https://github.com/banei/nsz2nsp_Win

## 功能

- 拖拽或选择 `.nsz` 文件 / 文件夹
- 批量队列转换，实时进度显示
- 暂停 / 继续 / 取消当前任务
- 失败任务一键重试
- 密钥路径配置与转换历史持久化
- 支持 `python -m nsz_converter` 与打包 exe 双模式启动

## 系统要求

- Windows 10/11（主要目标平台）
- Python 3.10+
- [nsz](https://pypi.org/project/nsz/) 工具：`pip install nsz`
- Switch 密钥文件 `prod.keys`

## 安装

```powershell
cd C:\Users\Administrator\Projects\nsz-converter
python -m pip install -e .
python -m pip install nsz
```

## 密钥配置

按优先级自动查找：

1. 应用设置中配置的密钥路径
2. 环境变量 `NSZ_KEYSET`
3. `%USERPROFILE%\.switch\prod.keys`
4. 当前目录 `.switch\prod.keys`
5. 目标目录或当前目录的 `keys.txt`

也可在 GUI **设置** 中直接指定 `prod.keys` 路径。

## 使用方法

### 图形界面（推荐）

```powershell
python -m nsz_converter
# 或
scripts\run_gui.bat
```

### 命令行

```powershell
python -m nsz_converter convert "D:\Games\某个目录"
python -m nsz_converter convert "D:\Games" --progress
```

### 打包 exe（双击即用）

```powershell
scripts\build.bat
```

打包完成后，双击运行：

```
dist\NSZ-Converter.exe
```

无需安装 Python 或执行命令行，但本机仍需已安装 `nsz`（`pip install nsz`）和密钥文件。

## 配置存储

设置与历史记录保存在：

```
%APPDATA%\nsz-converter\config.json
```

## 注意事项

- 转换成功后，原始 `.nsz` 会移至当前工作目录下的 `nsz_sources/` 文件夹
- 若对应 `.nsp` 已存在，将跳过转换并归档源文件
- 密钥文件为敏感信息，请勿分享或提交到仓库

## 开发

```powershell
python -m pip install -e ".[dev]"
pytest
```

## 许可证

MIT License
