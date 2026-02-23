#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝自动抢购脚本
功能：定时抢购淘宝限量发售商品
"""

import time
import logging
from datetime import datetime
from configparser import ConfigParser
from playwright.sync_api import sync_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 读取配置
config = ConfigParser()
config.read('config.ini', encoding='utf-8')

class TaobaoFlashSale:
    def __init__(self):
        """初始化抢购类"""
        self.username = config.get('account', 'username', fallback='')
        self.password = config.get('account', 'password', fallback='')
        self.product_url = config.get('product', 'url', fallback='')
        self.flash_sale_time = config.get('flash_sale', 'time', fallback='')
        self.browser_type = config.get('browser', 'type', fallback='chrome')
        self.headless = config.getboolean('browser', 'headless', fallback=False)
        self.browser = None
        self.page = None
        
        logger.info('淘宝自动抢购脚本初始化完成')
        logger.info(f'商品链接: {self.product_url}')
        logger.info(f'抢购时间: {self.flash_sale_time}')
    
    def init_browser(self):
        """初始化浏览器"""
        logger.info(f'初始化 {self.browser_type} 浏览器...')
        playwright = sync_playwright().start()
        
        if self.browser_type == 'chrome':
            self.browser = playwright.chromium.launch(
                headless=self.headless,
                slow_mo=0,  # 无延迟，提高速度
                args=[
                    '--disable-extensions',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
        elif self.browser_type == 'firefox':
            self.browser = playwright.firefox.launch(
                headless=self.headless,
                slow_mo=0
            )
        elif self.browser_type == 'edge':
            self.browser = playwright.chromium.launch(
                channel='msedge',
                headless=self.headless,
                slow_mo=0,
                args=[
                    '--disable-extensions',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
        else:
            raise ValueError(f'不支持的浏览器类型: {self.browser_type}')
        
        self.page = self.browser.new_page()
        # 设置页面超时
        self.page.set_default_timeout(30000)
        logger.info('浏览器初始化成功')
    
    def login(self):
        """登录淘宝账号"""
        logger.info('开始登录淘宝账号...')
        
        # 打开淘宝登录页
        self.page.goto('https://login.taobao.com')
        time.sleep(2)
        
        # 检查是否已登录
        if 'login' in self.page.url:
            logger.info('需要登录账号')
            
            # 如果配置了账号密码，尝试自动登录
            if self.username and self.password:
                logger.info('使用配置的账号密码自动登录...')
                try:
                    # 点击账号密码登录
                    self.page.click('text=密码登录')
                    time.sleep(1)
                    
                    # 输入账号密码
                    self.page.fill('#fm-login-id', self.username)
                    self.page.fill('#fm-login-password', self.password)
                    time.sleep(0.5)
                    
                    # 点击登录按钮
                    self.page.click('#login-form > div.fm-btn > button')
                    time.sleep(5)
                    
                    # 检查是否登录成功
                    if 'login' not in self.page.url:
                        logger.info('登录成功！')
                    else:
                        logger.warning('自动登录失败，可能需要验证码，请手动登录...')
                        logger.info('请在浏览器中完成登录，完成后按回车键继续...')
                        input()
                except Exception as e:
                    logger.error(f'自动登录出错: {e}')
                    logger.info('请在浏览器中完成登录，完成后按回车键继续...')
                    input()
            else:
                logger.info('未配置账号密码，请手动登录...')
                logger.info('请在浏览器中完成登录，完成后按回车键继续...')
                input()
        else:
            logger.info('已经登录，跳过登录步骤')
    
    def navigate_to_product(self):
        """导航到商品页面"""
        logger.info(f'导航到商品页面: {self.product_url}')
        
        # 打开商品页面
        self.page.goto(self.product_url)
        time.sleep(2)
        
        # 检查是否成功进入商品页面
        if 'detail' in self.page.url:
            logger.info('成功进入商品页面')
        else:
            logger.warning('可能未成功进入商品页面，请检查链接是否正确')
    
    def check_flash_sale_time(self):
        """检查抢购时间是否到达"""
        logger.info('开始监控抢购时间...')
        
        # 解析抢购时间
        sale_time = datetime.strptime(self.flash_sale_time, '%Y-%m-%d %H:%M:%S')
        logger.info(f'抢购时间设置为: {sale_time}')
        
        while True:
            current_time = datetime.now()
            time_diff = (sale_time - current_time).total_seconds()
            
            if time_diff <= 0:
                logger.info('抢购时间已到达！开始执行抢购...')
                break
            elif time_diff < 60:
                logger.info(f'距离抢购时间还有 {time_diff:.2f} 秒')
                time.sleep(0.1)  # 精确到0.1秒
            elif time_diff < 300:
                logger.info(f'距离抢购时间还有 {time_diff:.0f} 秒')
                time.sleep(1)
            else:
                logger.info(f'距离抢购时间还有 {time_diff:.0f} 秒')
                time.sleep(60)
    
    def 抢购(self):
        """执行抢购操作"""
        logger.info('开始执行抢购操作...')
        
        try:
            # 循环尝试抢购，提高成功率
            for i in range(10):
                logger.info(f'尝试抢购第 {i+1} 次...')
                
                # 刷新页面，确保页面状态最新
                if i > 0:
                    self.page.reload()
                    time.sleep(0.5)
                
                # 尝试点击立即购买按钮
                try:
                    # 淘宝/天猫的购买按钮选择器可能不同，这里尝试多种可能
                    buy_buttons = [
                        'text=立即购买',
                        'text=马上抢',
                        'text=立即抢购',
                        '#J_LinkBuy',
                        '.btn-buy'
                    ]
                    
                    clicked = False
                    for selector in buy_buttons:
                        try:
                            if self.page.is_visible(selector, timeout=1000):
                                self.page.click(selector, timeout=1000)
                                clicked = True
                                logger.info(f'成功点击购买按钮: {selector}')
                                break
                        except Exception:
                            continue
                    
                    if not clicked:
                        logger.warning('未找到购买按钮，可能商品还未到抢购时间')
                        time.sleep(0.1)
                        continue
                    
                    # 等待订单页面加载
                    time.sleep(1)
                    
                    # 尝试提交订单
                    submit_buttons = [
                        'text=提交订单',
                        '#submitOrderPC_1 > div > a',
                        '.submit-btn'
                    ]
                    
                    for selector in submit_buttons:
                        try:
                            if self.page.is_visible(selector, timeout=2000):
                                self.page.click(selector, timeout=1000)
                                logger.info(f'成功点击提交订单按钮: {selector}')
                                logger.info('抢购成功！请尽快完成支付')
                                return
                        except Exception:
                            continue
                    
                except Exception as e:
                    logger.error(f'抢购操作出错: {e}')
                    time.sleep(0.1)
            
            logger.warning('抢购失败，可能商品已售罄或网络延迟')
        except Exception as e:
            logger.error(f'抢购过程出错: {e}')
    
    def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            logger.info('关闭浏览器...')
            self.browser.close()
            logger.info('浏览器已关闭')
    
    def run(self):
        """运行整个抢购流程"""
        try:
            logger.info('淘宝自动抢购脚本开始运行')
            
            # 初始化浏览器
            self.init_browser()
            
            # 步骤1：登录
            self.login()
            
            # 步骤2：导航到商品页面
            self.navigate_to_product()
            
            # 步骤3：等待抢购时间
            self.check_flash_sale_time()
            
            # 步骤4：执行抢购
            self.抢购()
            
            logger.info('淘宝自动抢购脚本运行完成')
            
            # 保持浏览器打开，方便用户查看结果
            logger.info('脚本运行完成，浏览器将保持打开状态，请手动关闭...')
            
        except Exception as e:
            logger.error(f'脚本运行出错: {e}')
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # 不自动关闭浏览器，让用户手动处理
            # self.close_browser()
            pass

if __name__ == '__main__':
    tb_flash_sale = TaobaoFlashSale()
    tb_flash_sale.run()
