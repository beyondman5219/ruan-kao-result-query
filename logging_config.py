import logging

# 全局 logger 配置
logger = logging.getLogger('app_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]  %(message)s')