import sys
import os
import json
import psutil
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.settings_dialog import SettingsDialog  # 导入共享 logger
from logging_config import logger  # 从独立模块导入 logger
from core.score_checker import stop_task
from wxauto import WeChat

# 初始化配置文件
def initialize_config():
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.json')
    if not os.path.exists(config_path):
        default_config = {
            "cookies": "",
            "stage": "2024年下半年",
            "interval": 60
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        logger.info("创建了默认配置文件")

class QueryApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        initialize_config()
        logger.info("应用程序启动")
        self.wx = WeChat()
        self.settings_dialog = SettingsDialog(self.wx)
        self.settings_dialog.show()
        if os.path.exists("bot.ico"):
            self.setWindowIcon(QIcon("bot.ico"))

        # 绑定窗口关闭事件
        self.aboutToQuit.connect(self.cleanup)

    def cleanup(self):
        stop_task()
        try:
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            for child in children:
                child.terminate()
            psutil.wait_procs(children, timeout=3)
        except Exception as e:
            logger.error(f"终止子进程失败: {e}", exc_info=True)
        logger.info("资源清理完成")

def main():
    app = QueryApp()
    try:
        return app.exec()
    except Exception as e:
        logger.error(f"程序运行错误: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())