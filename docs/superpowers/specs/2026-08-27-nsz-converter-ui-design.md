# NSZ Converter — 独立桌面应用设计规格

**日期:** 2026-08-27  
**状态:** 待审阅  
**项目路径:** `C:\Users\Administrator\Projects\nsz-converter`

## 1. 背景与目标

用户需要一款 Windows 下可频繁使用的 NSZ → NSP 转换工具。现有 GitHub 上的 `nsz2nsp.py` 仅为单文件 CLI 脚本，功能有限。本项目为**全新独立应用**，可借鉴原项目的转换逻辑，但不依赖、不 fork 原仓库。

### 成功标准

- 双击 exe 或 bat 即可打开 GUI，无需记忆命令行
- 支持拖拽、批量队列、暂停/取消、失败重试
- 设置与转换历史持久化
- 同时保留 CLI 入口供自动化场景使用
- 代码为独立 Python 包，结构清晰、可维护

## 2. 方案选型

| 方案 | 结论 |
|------|------|
| CustomTkinter 桌面应用 | **选用** — 轻量、原生、易打包 |
| FastAPI + 浏览器 | 不选 — 对单人本地工具过重 |
| PyQt6 | 不选 — 依赖与打包体积过大 |

## 3. 项目结构

```
nsz-converter/
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── src/
│   └── nsz_converter/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       │   ├── converter.py
│       │   ├── nsz_runner.py
│       │   └── keyset.py
│       ├── queue/
│       │   ├── task.py
│       │   └── worker.py
│       ├── config/
│       │   └── settings.py
│       └── ui/
│           ├── app.py
│           ├── components/
│           │   ├── drop_zone.py
│           │   ├── queue_panel.py
│           │   └── log_panel.py
│           └── dialogs.py
│
├── scripts/
│   ├── run_gui.bat
│   └── build.bat
│
├── build/
│   └── nsz-converter.spec
│
└── tests/
    └── test_keyset.py
```

## 4. 模块职责

### 4.1 core/keyset.py

解析密钥文件路径，按优先级查找：

1. 用户配置的 `keyset_path`（设置面板）
2. 环境变量 `NSZ_KEYSET`
3. `~/.switch/prod.keys`
4. 当前工作目录 `./.switch/prod.keys`
5. 目标目录或 CWD 下的 `keys.txt`

返回 `(path, home_override)` 供 nsz 子进程使用。

### 4.2 core/nsz_runner.py

- 定位 nsz 可执行文件（PATH → pip scripts 目录）
- 检测坏解释器（断链 shebang）
- 启动 `nsz -D <file>` 子进程
- 实时解析 stdout 中的 `Decompress` 行作为进度
- 支持 `cancel()` 通过 `Popen.terminate()` 终止
- 通过回调推送：`on_progress(line)`, `on_complete(duration)`, `on_error(msg)`

### 4.3 core/converter.py

单文件转换 orchestrator：

- 输入：nsz 文件路径
- 检查对应 `.nsp` 是否已存在 → 跳过并归档源文件
- 调用 nsz_runner 执行转换
- 成功后移动 `.nsz` 到 `{cwd}/nsz_sources/`（保留相对路径，处理重名）
- 返回 `ConversionResult(status, message, duration)`

### 4.4 queue/task.py

```python
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    file_path: str
    status: TaskStatus
    progress: str       # 最新 Decompress 行
    duration: float
    error: str
    retries: int
```

### 4.5 queue/worker.py

后台 `threading.Thread` 消费队列：

- `add_tasks(paths)` — 扫描目录下所有 `.nsz` 或单个文件
- `start()` / `pause()` / `resume()` / `cancel_current()` / `clear()`
- `retry_task(task_id)` — 失败任务重新入队
- 状态变更通过 `on_task_update(task)` 回调通知 UI
- 暂停：完成当前文件后停止取下一个
- 取消当前：terminate 子进程，标记 CANCELLED

### 4.6 config/settings.py

持久化到 `%APPDATA%/nsz-converter/config.json`：

```json
{
  "keyset_path": "",
  "window_geometry": "900x700",
  "show_native_progress": false,
  "max_history": 50,
  "history": [
    {"file": "Game.nsz", "status": "completed", "time": "2026-08-27T12:00:00", "duration": 12.3}
  ]
}
```

### 4.7 ui/app.py — 主窗口

CustomTkinter 布局：

```
┌─────────────────────────────────────────────────┐
│  NSZ Converter                         [⚙ 设置] │
├─────────────────────────────────────────────────┤
│  [拖拽区域: 拖入 .nsz 或文件夹]                   │
│  [选择文件夹]  [选择文件]                         │
├─────────────────────────────────────────────────┤
│  队列                          [▶][⏸][✕ 清空]   │
│  ┌ 状态 │ 文件名          │ 进度      │ 用时 ┐   │
│  │  ✓   │ Game1.nsz      │ 完成      │ 12s  │   │
│  │  ▶   │ Game2.nsz      │ ████░ 45% │  8s  │   │
│  │  ○   │ Game3.nsz      │ 等待      │  -   │   │
│  │  ✗   │ Game4.nsz      │ 失败 [重试]│  -   │   │
│  └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  日志                              [清空] [复制] │
│  ┌ scrollable text area ────────────────────┐   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

设置对话框：密钥路径浏览、显示原生进度开关、历史记录查看。

拖拽：`tkinterdnd2` 绑定 `<<Drop>>` 事件，解析 dropped paths。

## 5. 入口与启动

| 方式 | 命令 |
|------|------|
| GUI（默认） | `python -m nsz_converter` |
| GUI 显式 | `python -m nsz_converter gui` |
| CLI | `python -m nsz_converter convert <目录>` |
| Windows bat | `scripts\run_gui.bat` |
| 打包 exe | `dist\nsz-converter.exe` |

`run_gui.bat` 内容：检测 Python → 检测 nsz → 启动 GUI。

## 6. 打包

PyInstaller one-file 模式：

- 入口：`nsz_converter.ui.app:main`
- 包含 customtkinter 资源
- **不包含** nsz 包（运行时检测，界面提示 `pip install nsz`）
- 输出：`dist/nsz-converter.exe`
- 构建脚本：`scripts/build.bat`

## 7. 依赖

```
# requirements.txt
customtkinter>=5.2
tkinterdnd2>=0.3

# 用户自行安装
nsz  # pip install nsz

# 开发/打包
pyinstaller>=6.0
pytest>=8.0
```

## 8. 错误处理

| 场景 | 行为 |
|------|------|
| nsz 未安装 | 启动时检测，弹窗提示安装命令，禁用转换按钮 |
| 密钥缺失 | 弹窗引导配置密钥路径或放置 prod.keys |
| 转换失败 | 任务标记 FAILED，日志显示错误，可重试 |
| 磁盘空间不足 | 捕获 nsz 错误输出，显示在日志 |
| 重复 .nsp 存在 | 跳过转换，归档 .nsz，标记 SKIPPED |

## 9. 测试

- `test_keyset.py`：密钥路径优先级、home_override 逻辑
- 手动测试清单：拖拽、队列、暂停/取消、重试、设置持久化、exe 打包运行

## 10. 与原项目关系

- **借鉴**：nsz 调用方式、密钥查找顺序、源文件归档到 `nsz_sources/`
- **独立**：全新代码、独立仓库、独立配置路径、独立文档
- **不保留**：不 import、不复制原 `nsz2nsp.py`

## 11. 实现顺序

1. 项目脚手架（pyproject.toml, src 包结构）
2. core 模块（keyset → nsz_runner → converter）
3. queue 模块（task → worker）
4. config 模块
5. UI 组件（drop_zone → queue_panel → log_panel → app）
6. CLI 入口（__main__.py）
7. 启动脚本（run_gui.bat）
8. 测试
9. PyInstaller 打包
10. README 文档
