import json
import logging
import os
import threading

import requests
from wxauto import WeChat

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量
timer = None
running = False
WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=6dcde160-5bf5-4f26-b1f8-4fcae5905030"  # 内置 Webhook

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
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
        logger.error(f"请求失败: {e}")
        return None

def send_wechat_message(content):
    try:
        payload = {"msgtype": "text", "text": {"content": content}}
        response = requests.post(WECHAT_WEBHOOK, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("企业微信消息发送成功")
    except Exception as e:
        logger.error(f"企业微信消息发送失败: {e}")

def process_response(wx: WeChat):
    response = send_request()
    if response and response.get('status') == 200:
        if response.get('data'):
            content = json.dumps(response['data'], ensure_ascii=False, indent=2)
            logger.info(f"查询结果: {content}")

            try:
                send_wechat_message(content)
                logger.info("企业微信机器人查询结果发送成功")
            except Exception as e:
                logger.error(f"企业微信机器人查询结果发送失败: {e}")

            try:
                wx.SendMsg(content, "文件传输助手")
                logger.info("微信消息发送成功")
            except Exception as e:
                logger.error(f"微信消息发送失败: {e}")
        else:
            logger.info("未查询到结果")
    else:
        logger.warning("响应无效或请求失败")
    if running:
        schedule_next(wx)

def schedule_next(wx: WeChat):
    global timer
    config = load_config()
    timer = threading.Timer(config['interval'], process_response, args=(wx,))
    timer.daemon = True
    timer.start()

def start_task(wx: WeChat):
    global running, timer
    if not running:
        running = True
        logger.info("定时任务开始")
        process_response(wx)
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