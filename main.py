#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taobao Flash Sale Script
Function: Timed purchase of limited edition products on Taobao
"""

import sys
import io

# Set standard output to UTF-8 encoding to solve terminal garbled problem
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time
import logging
from datetime import datetime
from configparser import ConfigParser
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Read configuration
config = ConfigParser()
config.read('config.ini', encoding='utf-8')

class TaobaoFlashSale:
    def __init__(self):
        """Initialize flash sale class"""
        self.username = config.get('account', 'username', fallback='')
        self.password = config.get('account', 'password', fallback='')
        self.product_url = config.get('product', 'url', fallback='')
        self.flash_sale_time = config.get('flash_sale', 'time', fallback='')
        self.browser_type = config.get('browser', 'type', fallback='chrome')
        self.headless = config.getboolean('browser', 'headless', fallback=False)
        self.browser = None
        self.page = None
        
        logger.info('Taobao Flash Sale Script initialized')
        logger.info(f'Product URL: {self.product_url}')
        logger.info(f'Flash Sale Time: {self.flash_sale_time}')
    
    def init_browser(self):
        """Initialize browser"""
        logger.info(f'Initializing {self.browser_type} browser...')
        playwright = sync_playwright().start()
        
        if self.browser_type == 'chrome':
            self.browser = playwright.chromium.launch(
                headless=self.headless,
                slow_mo=0,  # No delay, improve speed
                args=[
                    '--disable-extensions',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ],
                executable_path="C:\\Users\\Jared\\AppData\\Local\\ms-playwright\\chromium-1208\\chrome-win64\\chrome.exe"
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
            raise ValueError(f'Unsupported browser type: {self.browser_type}')
        
        self.page = self.browser.new_page()
        # Set page timeout
        self.page.set_default_timeout(30000)
        logger.info('Browser initialized successfully')
    
    def login(self):
        """Login to Taobao account"""
        logger.info('Starting Taobao login...')
        
        # Open Taobao login page
        self.page.goto('https://login.taobao.com')
        time.sleep(2)
        
        # Check if already logged in
        if 'login' in self.page.url:
            logger.info('Login required')
            
            # If username and password are configured, try auto-login
            if self.username and self.password:
                logger.info('Attempting auto-login with configured credentials...')
                try:
                    # Click password login
                    self.page.click('text=密码登录')
                    time.sleep(1)
                    
                    # Enter username and password
                    self.page.fill('#fm-login-id', self.username)
                    self.page.fill('#fm-login-password', self.password)
                    time.sleep(0.5)
                    
                    # Click login button
                    self.page.click('#login-form > div.fm-btn > button')
                    time.sleep(5)
                    
                    # Check if login successful
                    if 'login' not in self.page.url:
                        logger.info('Login successful!')
                    else:
                        logger.warning('Auto-login failed, verification code may be required, please login manually...')
                        logger.info('Please complete login in the browser, then press Enter to continue...')
                        input()
                except Exception as e:
                    logger.error(f'Auto-login error: {e}')
                    logger.info('Please complete login in the browser, then press Enter to continue...')
                    input()
            else:
                logger.info('Username and password not configured, please login manually...')
                logger.info('Please complete login in the browser, then press Enter to continue...')
                input()
        else:
            logger.info('Already logged in, skipping login step')
    
    def navigate_to_product(self):
        """Navigate to product page"""
        logger.info(f'Navigating to product page: {self.product_url}')
        
        # Open product page
        self.page.goto(self.product_url)
        time.sleep(2)
        
        # Check if successfully entered product page
        if 'detail' in self.page.url:
            logger.info('Successfully entered product page')
        else:
            logger.warning('May not have entered product page successfully, please check if the link is correct')
    
    def check_flash_sale_time(self):
        """Check if flash sale time has arrived"""
        logger.info('Starting flash sale time monitoring...')
        
        # Parse flash sale time
        sale_time = datetime.strptime(self.flash_sale_time, '%Y-%m-%d %H:%M:%S')
        logger.info(f'Flash sale time set to: {sale_time}')
        
        while True:
            current_time = datetime.now()
            time_diff = (sale_time - current_time).total_seconds()
            
            if time_diff <= 0:
                logger.info('Flash sale time arrived! Starting purchase...')
                break
            elif time_diff < 60:
                logger.info(f'Time until flash sale: {time_diff:.2f} seconds')
                time.sleep(0.1)  # Accurate to 0.1 seconds
            elif time_diff < 300:
                logger.info(f'Time until flash sale: {time_diff:.0f} seconds')
                time.sleep(1)
            else:
                logger.info(f'Time until flash sale: {time_diff:.0f} seconds')
                time.sleep(60)
    
    def 抢购(self):
        """Execute purchase operation"""
        logger.info('Starting purchase operation...')
        
        try:
            # Loop to try purchasing multiple times, improve success rate
            for i in range(10):
                logger.info(f'Purchase attempt {i+1}...')
                
                # Refresh page to ensure latest page state
                if i > 0:
                    self.page.reload()
                    time.sleep(0.5)
                
                # Try to click buy now button
                try:
                    # Taobao/Tmall buy button selectors may vary, try multiple possibilities
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
                                logger.info(f'Successfully clicked buy button: {selector}')
                                break
                        except Exception:
                            continue
                    
                    if not clicked:
                        logger.warning('Buy button not found, product may not be available for purchase yet')
                        time.sleep(0.1)
                        continue
                    
                    # Wait for order page to load
                    time.sleep(1)
                    
                    # Try to submit order
                    submit_buttons = [
                        'text=提交订单',
                        '#submitOrderPC_1 > div > a',
                        '.submit-btn'
                    ]
                    
                    for selector in submit_buttons:
                        try:
                            if self.page.is_visible(selector, timeout=2000):
                                self.page.click(selector, timeout=1000)
                                logger.info(f'Successfully clicked submit order button: {selector}')
                                logger.info('Purchase successful! Please complete payment as soon as possible')
                                return
                        except Exception:
                            continue
                    
                except Exception as e:
                    logger.error(f'Purchase operation error: {e}')
                    time.sleep(0.1)
            
            logger.warning('Purchase failed, product may be sold out or network delay')
        except Exception as e:
            logger.error(f'Purchase process error: {e}')
    
    def close_browser(self):
        """Close browser"""
        if self.browser:
            logger.info('Closing browser...')
            self.browser.close()
            logger.info('Browser closed')
    
    def run(self):
        """Run the entire flash sale process"""
        try:
            logger.info('Taobao Flash Sale Script started')
            
            # Initialize browser
            self.init_browser()
            
            # Step 1: Login
            self.login()
            
            # Step 2: Navigate to product page
            self.navigate_to_product()
            
            # Step 3: Wait for flash sale time
            self.check_flash_sale_time()
            
            # Step 4: Execute purchase
            self.抢购()
            
            logger.info('Taobao Flash Sale Script completed')
            
            # Keep browser open for user to view results
            logger.info('Script completed, browser will remain open, please close manually...')
            
        except Exception as e:
            logger.error(f'Script runtime error: {e}')
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Do not automatically close browser, let user handle it
            # self.close_browser()
            pass

if __name__ == '__main__':
    tb_flash_sale = TaobaoFlashSale()
    tb_flash_sale.run()