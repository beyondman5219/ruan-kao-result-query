import json
import os
import threading
import smtplib
from email.mime.text import MIMEText

import requests
from wxauto import WeChat

from logging_config import logger  # 从独立模块导入 logger

# 全局变量
timer = None
running = False


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}", exc_info=True)
        raise


def send_request():
    config = load_config()
    try:
        headers = {'Cookie': config['cookies']}
        files = {'stage': (None, config['stage'])}
        response = requests.post(
            "https://bm.ruankao.org.cn/query/score/result",
            headers=headers,
            files=files,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"请求失败: {e}", exc_info=True)
        return None


def send_email(content, email_config, title='成绩查询结果'):
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = title
        msg['From'] = email_config['email']
        msg['To'] = email_config['email']

        # QQ SMTP 配置
        smtp_server = 'smtp.qq.com'
        smtp_port = 587
        smtp_user = email_config['email']
        smtp_password = email_config['password']

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [smtp_user], msg.as_string())
        server.quit()
        logger.info("QQ 邮箱通知发送成功")
    except Exception as e:
        logger.error(f"QQ 邮箱通知发送失败: {e}", exc_info=True)


def process_response():
    response = send_request()
    if response and response.get('status') == 200:
        if response.get('data'):
            content = response['data']
            title = f"【{content['KSSJ']}-{content['ZGMC']}】软考成绩查询成功"
            msg = f"""   # 成绩查询结果
----------------------------------------
考试时间: {content['KSSJ']}
资格名称: {content['ZGMC']}
证件号: {content['ZJH']}
准考证号: {content['ZKZH']}
姓名: {content['XM']}
----------------------------------------
综合知识: {content['SWCJ']}
案例分析: {content['XWCJ']}
论文: {content['LWCJ']}
----------------------------------------
"""

            logger.info(f"查询结果: {msg}")

            try:
                email_config = load_config()
                send_email(msg, {
                    'email': email_config.get('email', ''),
                    'password': email_config.get('password', '')
                }, title)
                logger.info("QQ 邮箱查询结果发送成功")
            except Exception as e:
                logger.error(f"QQ 邮箱查询结果发送失败: {e}", exc_info=True)

            # 微信通知开关控制，需登录微信
            # 注意：开启此功能前需确保微信已登录，否则可能失败
            if load_config().get('enable_wechat', False):
                try:
                    wx = WeChat()
                    wx.SendMsg(msg, "文件传输助手")
                    logger.info("微信消息发送成功")
                except Exception as e:
                    logger.error(f"微信消息发送失败: {e.args}", exc_info=True)
        else:
            logger.info("未查询到结果")
    else:
        logger.warning("响应无效或请求失败")
    if running:
        schedule_next()


def schedule_next():
    global timer
    config = load_config()
    timer = threading.Timer(config['interval'], process_response, args=())
    timer.daemon = True
    timer.start()


def start_task():
    global running, timer
    if not running:
        running = True
        logger.info("定时任务开始")
        process_response()
    else:
        logger.info("定时任务已在运行")


def stop_task():
    global running, timer
    if running:
        running = False
        if timer:
            timer.cancel()
            timer = None
        logger.info("定时任务停止")
    else:
        logger.info("定时任务未运行")
