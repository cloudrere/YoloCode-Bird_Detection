# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 **PySide6 + Ultralytics YOLOv8** 的鸟类目标检测桌面应用（Windows），支持图片/批量图片/视频/实时摄像头四种输入。包含完整的 GUI 参数调节、类别筛选、结果保存与统计、日志着色、Excel 导出功能。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 GUI 应用
python main.py

# 训练模型（参考模板）
python base_code/train.py

# 验证模型（参考模板）
python base_code/val.py
```

## 核心架构

```
main.py                  # 入口：创建 QApplication + MainWindow
ui_main.py               # 主界面（~1400 行）：全部 UI 构建 + 信号连接 + 业务逻辑
detection_thread.py      # 检测线程：QThread 子类，通过 Qt 信号与 UI 通信
config.py                # 默认路径、参数、中英文类别字典
```

### 线程模型

`DetectionThread` 继承 `QThread`，在后台运行 YOLO 推理，通过以下 Qt 信号更新 UI：
- `frame_ready` → 更新检测前/后双画面
- `progress_update` → 更新进度条
- `log_message` → 写入日志
- `detection_done` → 检测结束回调
- `statistics_update` → 更新统计表格
- `detail_record` → 追加检测明细

暂停/继续使用 `QMutex + QWaitCondition` 实现，停止通过 `_is_running` 标志位控制。

四个主要处理模式：`_process_single_image`, `_process_image_folder`, `_process_video`, `_process_camera`。

### 自定义控件

- `ImageLabel`：重写 `paintEvent` 实现自适应缩放的图像显示，通过 `setImage(bgr)` 接收 OpenCV BGR 图像
- 全局样式表 `APP_QSS` 定义在 `ui_main.py` 顶部，使用对象名选择器（如 `#startBtn`）区分控件样式

### 中文路径处理

全程使用 `numpy.fromfile(path, dtype=np.uint8)` + `cv2.imdecode/cv2.imencode` 替代 `cv2.imread/imwrite`，避免中文路径乱码。

### 类别翻译

`config.py` 中的 `CLASS_NAMES_CN` 字典维护英→中类别映射，`get_chinese_name()` 函数在 UI 中使用。未在字典中定义的类别直接显示英文名。

### 数据集与权重

- `weights/` — 预训练权重（默认 `yolov8n.pt`），训练后的 `best.pt` 在 `runs/exp*/weights/`
- `dataset/img/` — 训练用图片
- `runs/save_results/` — 检测结果保存目录
- `runs/exp*/` — 训练实验输出目录

### ultralytics 版本

项目内含 Ultralytics YOLO v8.1.30 完整代码，非 pip 安装的包，修改 `ultralytics/` 目录即可定制模型行为。
