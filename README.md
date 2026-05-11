# 基于深度学习的鸟类智能检测系统

基于 **PySide6 + Ultralytics YOLOv8** 的鸟类目标检测桌面应用。支持图片/批量图片/视频/实时摄像头四种输入，含登录注册、参数调节、类别筛选、统计图表、日志等完整功能。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

首次启动需注册账号（SQLite 本地存储），之后登录即可使用。

## 功能概览

| 功能 | 说明 |
| --- | --- |
| 多种输入源 | 单张图片 / 文件夹批量 / 视频文件 / USB 摄像头 |
| 模型支持 | 任意 Ultralytics YOLO `.pt`、`.onnx`、`.engine` |
| GPU 预热 | 加载模型后自动 dummy 推理，防止首帧崩溃 |
| 用户认证 | 登录/注册，SQLite 存储，SHA-256 + 盐值加密 |
| 参数调节 | 弹窗设置置信度 / IoU / 视频跳帧 / 摄像头跳帧 / 推理尺寸 |
| 类别筛选 | 弹窗勾选要检测的鸟类类别 |
| 检测控制 | 开始 / 暂停 / 继续 / 停止，位于左侧面板 |
| 双画面显示 | 左侧原始画面 + 右侧检测结果，可拖拽调整比例 |
| 实时统计 | 画面下方显示当前检出目标数和类别数 |
| 统计图表 | 弹窗显示 matplotlib 柱状图，中文正常渲染 |
| 检测明细 | 弹窗显示完整检测结果表格（序号/类别/置信度/坐标/尺寸） |
| 日志系统 | 着色日志（info/success/warn/error），弹窗查看并支持保存 |
| 结果保存 | 可选保存检测后图片/视频 |
| 中文路径 | `np.fromfile + cv2.imdecode` 全程避免中文路径乱码 |
| 动态路径 | 模型/保存/字体路径基于项目根目录动态解析，迁移无需改配置 |

## 项目结构

```
main.py                  # 入口：创建 QApplication → 登录 → MainWindow
auth.py                  # 登录/注册界面 + SQLite 用户数据库
ui_main.py               # 主界面：UI 构建 + 信号连接 + 业务逻辑 + 弹窗类
detection_thread.py      # QThread 子类，后台 YOLO 推理，Qt 信号更新 UI
config.py                # 动态路径、默认参数、中英文类别字典
Font/DroidSansFallback.ttf  # 中文字体
runs/save_results/       # 检测结果保存目录
weights/                 # 预训练权重
```

### 弹窗组件（均在 `ui_main.py` 中）

| 类名 | 用途 |
| --- | --- |
| `ParamsDialog` | 置信度 / IoU / 跳帧 / 推理尺寸 |
| `ClassFilterDialog` | 勾选检测类别，支持全选/全不选 |
| `StatisticsDialog` | matplotlib 柱状图统计 |
| `DetailDialog` | 完整检测明细表格 |
| `LogDialog` | 日志查看 / 保存 / 清空 |

### 线程模型

`DetectionThread` 继承 `QThread`，通过 Qt 信号更新 UI：`frame_ready` → 双画面、`progress_update` → 进度条、`log_message` → 日志、`statistics_update` → 实时统计、`detail_record` → 明细表格、`detection_done` → 结束回调。暂停/继续使用 `QMutex + QWaitCondition`。

## 中英文类别字典

编辑 `config.py` 中的 `CLASS_NAMES_CN` 字典即可增删类别翻译，格式为 `'英文类名': '中文类名'`。未在字典中定义的类别直接显示英文名。

## 常见问题

**摄像头列表为空** → 点击「刷新」按钮重新枚举。

**首次推理 CUDA 崩溃** → 已内置 dummy 预热，如仍崩溃请检查 torch/CUDA 版本匹配。

**统计图表中文乱码** → 确保 `Font/DroidSansFallback.ttf` 存在；系统会自动回退到 Microsoft YaHei。

**Excel 导出失败** → 确认安装了 openpyxl：`pip install openpyxl`。

## 许可

仅用于学习与研究，模型版权归原作者所有。
