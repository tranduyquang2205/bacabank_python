import requests
import json
import time
import datetime
from requests.cookies import RequestsCookieJar
import base64
import re
import urllib.parse
from bs4 import BeautifulSoup

class BacABank:
    def __init__(self):
        self.keyanticaptcha = "b8246038ce1540888c4314a6c043dcae"
        self.cookies = RequestsCookieJar()
        self.session = requests.Session()
        self.account_number = ''
        self.account_url = ''
        self.last_url = ''
        self.dse_sessionId = ''
        self.dse_processorId=''
        self.check_balance = False
        self.transactions = []
    def check_error_message(self,html_content):
        pattern = r'<span style="color: black"><strong>(.*?)</strong></span>'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    def extract_account_number(self,html_content):
        pattern = r'acctNo=([0-9]{8,16})'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    def extract_account_url(self,html_content):
        pattern = r'"(/IBSRetail/Request\?&dse_sessionId=.*&dse_applicationId=-1&dse_pageId=[4-5]&dse_operationName=retailQueryAccountInformationProc&dse_processorState=initial&dse_nextEventName=detail&option=account&acctNo=[0-9]{8,16}&acctType=CA)"'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    def extract_balance(self,html_content):
        pattern = r'<div class="col-sm-5">\s+Số dư khả dụng\s+</div>\s+<div class="col-sm-7 text-right">\s+(.*)\r\s'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    def extract_dse_processorId(self,html_content):
        pattern = r'<input type="hidden" name="dse_processorId" value="(.*)"'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    def extract_page_url(self,html_content,page):
        pattern = r'<a style="color:#100719;" href="([^>]*)">'+str(page)+'</a>'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    def extract_transaction_history(self,html_string):
            soup = BeautifulSoup(html_string, "html.parser")
            tbody = soup.find('tbody', id='allResultTableBody')
            if tbody:
                rows = tbody.find_all('tr', class_='bg1')
            else:
                return []

            history_records = []

            for row in rows:
                columns = row.find_all('td')
                record = {
                    "transaction_iD": columns[0].text.strip(),
                    "time": columns[1].text.strip(),
                    "amount": columns[2].text.strip(),
                    "status": columns[3].text.strip(),
                    "method": columns[4].text.strip(),
                    "description": columns[5].get('title', '').strip()
                }
                history_records.append(record)

            return history_records
    def login(self, username, password):
        url = "https://ebanking.baca-bank.vn/IBSRetail/Request?&dse_sessionId=s2xe-FimkVx4j9lPeztr8eF&dse_applicationId=-1&dse_pageId=1&dse_operationName=retailIndexProc&dse_errorPage=error_page.jsp&dse_processorState=initial&dse_nextEventName=start"

        payload = {}
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        }

        response = self.session.get(url, headers=headers, data=payload,allow_redirects=True)
        pattern = r'dse_sessionId=(.*?)&dse_applicationId=(.*?)&dse_pageId=(.*?)&dse_operationName=(.*?)&dse_errorPage=(.*?)&dse_processorState=(.*?)&dse_nextEventName=(.*?)\';'
        pattern_url = r'window.location.href = \'(.*?)\';'
        match = re.search(pattern, response.text)
        match_url = re.search(pattern_url, response.text)
        self.dse_sessionId = str(match.group(1))
        if match_url:
            url1 = 'https://ebanking.baca-bank.vn'+match_url.group(1)
            payload = {}
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://ebanking.baca-bank.vn/IBSRetail/EstablishSession?&fromOpName=retailIndexProc&fromStateName=initial&fromEventName=start',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
            }
            response = self.session.get(url1, headers=headers, data=payload)
            base64_captcha_img = self.getCaptcha()
            task = self.createTaskCaptcha(base64_captcha_img)
            time.sleep(1)
            captchaText = self.checkProgressCaptcha(json.loads(task)['taskId'])
            payload = 'dse_sessionId='+str(match.group(1))+'&dse_applicationId=-1&dse_pageId=2&dse_operationName=retailUserLoginProc&dse_errorPage=index.jsp&dse_processorState=initial&dse_nextEventName=start&_userName='+username+'&_password='+urllib.parse.quote(password)+'&_password1=&_verifyCode='+captchaText
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://ebanking.baca-bank.vn',
            'Connection': 'keep-alive',
            'Referer': url1,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
            }

            response = self.session.post("https://ebanking.baca-bank.vn/IBSRetail/Request", headers=headers, data=payload)
            dse_processorId = self.extract_dse_processorId(response.text)
            if dse_processorId:
                payload = 'dse_sessionId='+str(match.group(1))+'&dse_applicationId=-1&dse_pageId=3&dse_operationName=retailUserLoginProc&dse_errorPage=error_page.jsp&dse_processorState=loginConductJSP&dse_nextEventName=ok&dse_processorId='+dse_processorId+'&_loginedConduct=forceLastLogin'
                
                headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://ebanking.baca-bank.vn',
                'Connection': 'keep-alive',
                'Referer': url1,
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache'
                }

                response = self.session.post("https://ebanking.baca-bank.vn/IBSRetail/Request", headers=headers, data=payload)
        
            pattern2 = r'dse_sessionId=(.*?)&dse_applicationId=(.*?)&dse_pageId=(.*?)&dse_operationName=(.*?)&dse_errorPage=(.*?)&dse_processorState=(.*?)&dse_nextEventName=(.*?)&toOpName=(.*?)\';'
            pattern_url2 = r'window.location.href = \'(.*?)\';'
            match2 = re.search(pattern2, response.text)
            match_url2 = re.search(pattern_url2, response.text)
            url2 = 'https://ebanking.baca-bank.vn'+match_url2.group(1)
            self.last_url = url2
            payload = {}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://ebanking.baca-bank.vn/IBSRetail/Request',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache'
                }
            response = self.session.get(url2, headers=headers, data=payload)
            check_error_message = self.check_error_message(response.text)
            if check_error_message:
                return {
                    'success': False,
                    'message': check_error_message
                }
            else:
                self.account_number = self.extract_account_number(response.text)
                account_url = self.extract_account_url(response.text)
                if account_url:
                    self.account_url = 'https://ebanking.baca-bank.vn' + self.extract_account_url(response.text)
                else:

                    return {
                    'success': False,
                    'message': 'error'
                    }
                return {
                    'success': True,
                    'message': 'Đăng nhập thành công',
                    'account_number': self.account_number
                }

    def get_balance(self):
        
        payload = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': self.last_url,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
            }
        response = self.session.get(self.account_url, headers=headers, data=payload)
        self.dse_processorId = self.extract_dse_processorId(response.text)
        balance =  self.extract_balance(response.text).replace(',','')
        self.check_balance = True
        return {
            'account_number': self.account_number,
            'balance' : balance
        }

    def createTaskCaptcha(self, base64_img):
            url = "https://api.anti-captcha.com/createTask"
            payload = json.dumps({
            "clientKey": "f3a44e66302c61ffec07c80f4732baf3",
            "task": {
                "type": "ImageToTextTask",
                "body": base64_img,
                "phrase": False,
                "case": False,
                "numeric": 0,
                "math": False,
                "minLength": 0,
                "maxLength": 0
            },
            "softId": 0
            })
            headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            return(response.text)

    def checkProgressCaptcha(self, task_id):
        url = 'https://api.anti-captcha.com/getTaskResult'
        data = {
            "clientKey": "f3a44e66302c61ffec07c80f4732baf3",
            "taskId": task_id
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_json = json.loads(response.text)
        if response_json["status"] != "ready":
            time.sleep(1)
            return self.checkProgressCaptcha(task_id)
        else:
            return response_json["solution"]["text"]
    def getCaptcha(self):
        url = 'https://ebanking.baca-bank.vn/IBSRetail/servlet/ImageServlet'
        headers = {}
        response = self.session.get(url, headers=headers)
        return base64.b64encode(response.content).decode('utf-8')
    def get_transactions_by_page(self,url,page,limit):
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://ebanking.baca-bank.vn',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
        }

        response = self.session.get("https://ebanking.baca-bank.vn"+url, headers=headers)
        transaction_history = self.extract_transaction_history(response.text)

        if page*10 < limit:
            if transaction_history:
                self.transactions += transaction_history
            page=page+1
            
            page_url = self.extract_page_url(response.text,page)
            if page_url:
                return self.get_transactions_by_page(page_url,page,limit)
        else:
            if transaction_history:
                self.transactions += transaction_history[:limit - (page-1)*10]
        return True
            
        
        
        
    def get_transactions(self,fromDate,toDate,limit=100):
        self.transactions = []
        if not self.check_balance:
            self.get_balance()
        payload = 'dse_sessionId='+self.dse_sessionId+'&dse_applicationId=-1&dse_operationName=retailQueryAccountInformationProc&dse_pageId=9&dse_processorState=showAccDetailsState&dse_processorId='+self.dse_processorId+'&dse_errorPage=error_page.jsp&dse_nextEventName=query&vErrorPage=%2Faccountmanagement%2Fquery_transaction_information.jsp&research=yes&beginDate='+urllib.parse.quote(fromDate)+'&endDate='+urllib.parse.quote(toDate)+'&_period=&is_detail_search=&transaction_channel=&transaction_type='
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.100.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://ebanking.baca-bank.vn',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
        }

        response = self.session.post("https://ebanking.baca-bank.vn/IBSRetail/Request", headers=headers, data=payload)
        self.transactions = self.extract_transaction_history(response.text)
        
        page_url = self.extract_page_url(response.text,2)
        if page_url:
            self.get_transactions_by_page(page_url,2,limit)
        return self.transactions 

# bacabank = BacABank()
# username = "0702326373"
# password = "Tran7788@"
# fromDate="02/08/2023"
# toDate="02/02/2024"
# limit = 105
# session_raw = bacabank.login(username, password)
# print(session_raw)

# balance = bacabank.get_balance()
# print(balance)

# history = bacabank.get_transactions(fromDate,toDate,limit)
# print(len(history))
# print(history)