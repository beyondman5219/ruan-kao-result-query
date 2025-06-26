import json
import logging
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QMessageBox, QTextEdit
from PySide6.QtCore import Qt

from core.score_checker import start_task, stop_task  # 从 core 目录导入
from wxauto import WeChat  # 修正为 wxautox 匹配你的依赖
from logging_config import logger,formatter  # 从独立模块导入 logger

# 自定义日志处理器
class TextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)
        self.text_edit.ensureCursorVisible()  # 自动滚动到最新日志

class SettingsDialog(QDialog):
    def __init__(self, wx: WeChat, parent=None):
        super().__init__(parent)
        self.wx = wx
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.setWindowTitle("成绩查询配置")
        self.resize(450, 400)  # 增加高度以容纳日志窗口
        # 启用最小化和最大化按钮
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Cookies
        layout.addWidget(QLabel("Cookies:"))
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("请输入 Cookie 字符串（例如 UUID=xxx; PHPSESSID=xxx）")
        layout.addWidget(self.cookies_input)

        # Stage
        layout.addWidget(QLabel("查询参数 (Stage):"))
        self.stage_input = QLineEdit()
        self.stage_input.setPlaceholderText("请输入查询参数（例如 2024年下半年）")
        layout.addWidget(self.stage_input)

        # Interval
        layout.addWidget(QLabel("定时频率 (秒):"))
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("请输入定时频率（例如 60）")
        layout.addWidget(self.interval_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存并启动")
        self.save_btn.clicked.connect(self.save_settings)
        self.stop_btn = QPushButton("停止任务")
        self.stop_btn.clicked.connect(self.stop_task)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        # Log Display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit { background-color: white; border: 1px solid #D2D2D7; border-radius: 8px; padding: 5px; font-size: 12px; color: #1D1D1F; }
        """)
        # 设置自适应大小
        self.log_text.setSizePolicy(self.log_text.sizePolicy().horizontalPolicy(), self.log_text.sizePolicy().verticalPolicy().Expanding)
        layout.addWidget(self.log_text)

        # 配置日志输出
        log_handler = TextEditLogger(self.log_text)
        log_handler.setFormatter(logger.handlers[0].formatter if logger.handlers else formatter)  # 使用现有格式器
        logger.addHandler(log_handler)

        # macOS 风格
        self.setStyleSheet("""
            QDialog { background-color: #F5F5F7; }
            QWidget { font-family: 'SF Pro Display'; }
            QPushButton { background-color: #007AFF; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-size: 13px; }
            QPushButton:hover { background-color: #0069D9; }
            QPushButton[text="取消"], QPushButton[text="停止任务"] { background-color: #E5E5EA; color: #1D1D1F; }
            QPushButton[text="取消"]:hover, QPushButton[text="停止任务"]:hover { background-color: #D1D1D6; }
            QLabel { color: #1D1D1F; font-size: 13px; }
            QLineEdit { background-color: white; border: 1px solid #D2D2D7; border-radius: 8px; padding: 5px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #007AFF; }
        """)

    def load_settings(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.cookies_input.setText(config.get('cookies', ''))
                self.stage_input.setText(config.get('stage', ''))
                self.interval_input.setText(str(config.get('interval', 60)))
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", "无法加载配置文件，使用默认值")

    def validate_inputs(self):
        cookies = self.cookies_input.text().strip()
        stage = self.stage_input.text().strip()
        interval = self.interval_input.text().strip()

        if not cookies:
            return False, "Cookies 不能为空"
        if not stage:
            return False, "查询参数不能为空"
        try:
            interval_val = int(interval)
            if interval_val <= 0:
                return False, "定时频率必须是正整数"
        except ValueError:
            return False, "定时频率必须是整数"
        return True, ""

    def save_settings(self):
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            QMessageBox.warning(self, "错误", error_msg)
            return

        config = {
            "cookies": self.cookies_input.text().strip(),
            "stage": self.stage_input.text().strip(),
            "interval": int(self.interval_input.text().strip())
        }
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            logger.info("配置文件保存成功")
            start_task(self.wx)
            QMessageBox.information(self, "成功", "配置文件保存并任务启动成功")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}", exc_info=True)
            QMessageBox.warning(self, "错误", f"保存配置文件失败: {e}")

    def stop_task(self):
        stop_task()
        logger.info("定时任务已停止")
        QMessageBox.information(self, "成功", "定时任务已停止")