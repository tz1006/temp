#!/usr/bin/python3
# -*- coding: UTF-8 -*- 
# filename: checker.py
# version: v1
# discription: 当停牌列表变动时发送短信

import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor
import json
import time
import nexmo



class stock():
    def __init__(self, code):
        self.__s = requests.session()
        self.__s.keep_alive = False
        self.code = code
        self.sscode = self.__sscode()
        self.name = self.__name()
        self.status = self.__status()
        #self.open = gap(code)[0]
        #self.high = gap(code)[1]
        #self.low = gap(code)[2]
        #self.close = close(code)
        self.__get_index()
    # sh600123
    def __sscode(self):
        code = str(self.code)
        if code[0]+code[1] =='60':
            code = 'sh%s' % code
        else:
            code = 'sz%s' % code
        return code
    # 停牌
    def __status(self):
        url = 'http://apiapp.finance.ifeng.com/stock/isopen?code=%s' % self.sscode
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=5)
                except:
                    #print('Error!------------------------------------')
                    pass
        isopen = r.json()['data'][0]['isopen']
        if isopen == 1:
            return True
        else:
            return False
    # 股票名
    def __name(self):
        url = 'http://hq.sinajs.cn/list=%s' % self.sscode
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=5)
                except:
                    pass
        name = r.text.split("\"")[1].split(",",1)[0]
        return name
    # Index
    def __get_index(self):
        url = 'http://suggest.eastmoney.com/SuggestData/Default.aspx?type=1&input=%s' % self.code
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=5)
                except:
                    pass
        self.__index = r.text.split(',')[-2]
        today = datetime.now(timezone('Asia/Shanghai'))
        self.__today = ['%d' % today.year, '%02d' % today.month, '%02d' % today.day]
    # (价格, 均价)
    def price(self):
        url = 'https://api.finance.ifeng.com/aminhis/?code=%s&type=five' % self.sscode
        r = None
        while r == None:
            try:
                r = self.__s.get(url, timeout=5, verify=False)
            except:
                pass
        if r.text == '':
            #print('无法获取 %s 价格。' % stock_code)
            price = ''
            average = ''
        else:
            now = r.json()[-1]['record'][-1]
            # date
            date = now[0].split(' ')[0]
            # Price
            price = float(now[1])
            # diff
            diff = float(now[2])
            # Average
            average = float(now[4])
        return (price, average)
    # (涨幅, 价格波动)
    def wave(self):
        url = 'https://123.103.93.175/q.php?l=%s' % self.sscode
        #url = 'https://hq.finance.ifeng.com/q.php?l=%s' % self.sscode
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=5, verify=False)
                except:
                    pass
        j = json.loads(r.text.split('=', 1)[1].split(';')[0])
        data = j[list(j)[0]]
        price = data[0]
        price_diff = data[2]
        wave = data[3]
        return (wave, price_diff)
    # 涨幅2
    # MA 当日 (ma5, ma10, ma20, ma30)
    def ma(self):
        span = '%s%s%s' % (self.__today[0], self.__today[1], self.__today[2])
        url = 'https://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?id=%s%s&TYPE=k&rtntype=1&QueryStyle=2.2&QuerySpan=%s%%2C1&extend=ma' % (self.code, self.__index, span)
        #print(url)
        r = None
        while r == None:
            try:
                r = self.__s.get(url, timeout=5, verify=False)
            except:
                pass
        if r.text == '({stats:false})':
            return
        else:
            date = r.text.split(',', 1)[0].split('(')[1]
            today = '%s-%s-%s' % (self.__today[0], self.__today[1], self.__today[2])
            if date == today:
                ma_data = r.text.split('[')[1].split(']')[0].split(',')
                ma5 = float(ma_data[0])
                ma10 = float(ma_data[1])
                ma20 = float(ma_data[2])
                ma30 = float(ma_data[3])
                return(ma5, ma10, ma20, ma30)
            else:
                return
    # KDJ 当日 (k, d, j)
    def kdj(self):
        span = '%s%s%s' % (self.__today[0], self.__today[1], self.__today[2])
        url = 'https://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?id=%s%s&TYPE=k&rtntype=1&QueryStyle=2.2&QuerySpan=%s%%2C1&extend=kdj' % (self.code, self.__index, span)
        #print(url)
        r = None
        while r == None:
            try:
                r = self.__s.get(url, timeout=5, verify=False)
            except:
                pass
        if r.text == '({stats:false})':
            return
        else:
            date = r.text.split(',', 1)[0].split('(')[1]
            today = '%s-%s-%s' % (self.__today[0], self.__today[1], self.__today[2])
            #today = '2018-03-15'
            if date == today:
                kdj_data = r.text.split('[')[1].split(']')[0].split(',')
                k = float(kdj_data[0])
                d = float(kdj_data[1])
                j = float(kdj_data[2])
                return(k, d, j)
            else:
                return
    def macd(self):
        span = '%s%s%s' % (self.__today[0], self.__today[1], self.__today[2])
        url = 'https://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?id=%s%s&TYPE=k&rtntype=1&QueryStyle=2.2&QuerySpan=%s%%2C1&extend=macd' % (self.code, self.__index, span)
        #print(url)
        r = None
        while r == None:
            try:
                r = self.__s.get(url, timeout=5, verify=False)
            except:
                pass
        if r.text == '({stats:false})':
            return
        else:
            date = r.text.split(',', 1)[0].split('(')[1]
            today = '%s-%s-%s' % (self.__today[0], self.__today[1], self.__today[2])
            #today = '2018-03-15'
            if date == today:
                macd_data = r.text.split('[')[1].split(']')[0].split(',')
                dif = float(macd_data[0])
                dea = float(macd_data[1])
                macd = float(macd_data[2])
                return(dif, dea, macd)
            else:
                return
    def history(self):
        pass
    def help(self):
        print('''
            .code
            .name
            .status
            .close
            .open
            .high
            .low
            .price()
            .wave()
            .ma()
            .kdj()
            .macd
            .help
            ''')



class stocklist():
    def __init__(self):
        self.list = []
        self.sha = []
        self.sza = []
        self.szzx = []
        self.szcy = []
        self.stock = []
        self.get_list()
        self.__load()
    # 载入列表
    def get_list(self):
        message = '尝试从文件导入股票代码'
        log.stocklist(message)
        try:
            self.list = self.get_list_from_txt()
        except:
            self.dl_list()
    def get_list_from_txt(self):
        with open('database/stocklist.txt', 'r') as f:
            data = f.read()
        li = json.loads(data)
        message = '文件导入%s支股票代码' % len(li)
        log.stocklist(message)
        return li
    def __save_list_to_txt(self):
        data = json.dumps(self.list)
        if os.path.exists('database') == False:
            os.makedirs('database')
        with open("database/stocklist.txt","w") as f:
            f.write(data)
        message = '保存%s支股票代码到文件' % len(self.list)
        log.stocklist(message)
    def dl_list(self):
        message = '从网络下载股票代码'
        log.stocklist(message)
        start_time = datetime.now()
        self.list = self.get_sha() + self.get_sza() + self.get_szzx() + self.get_szcy()
        self.list = list(set(self.list))
        end_time = datetime.now()
        timedelsta = (end_time - start_time).seconds
        message = '成功导入%s支股票代码，耗时%s秒。' % (len(self.list), timedelsta)
        log.stocklist(message)
        self.__save_list_to_txt()
    # 上海A股
    def get_sha(self):
        self.sha.clear()
        start_time = datetime.now()
        url = 'http://query.sse.com.cn/security/stock/getStockListData2.do?&stockType=1&pageHelp.beginPage=1&pageHelp.pageSize=2000'
        header = {
    	  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0',
    	  'Referer': 'http://www.sse.com.cn/assortment/stock/list/share/'
    	  }
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=20, headers = header)
                except:
                    pass
        stock_data = r.json()['pageHelp']['data']
        for i in stock_data:
            code = i['SECURITY_CODE_A']
            self.sha.append(code)
        end_time = datetime.now()   
        timedelsta = (end_time - start_time).seconds
        message = '从 上海A股 导入%s支股票代码，耗时%s秒。' % (len(self.sha), timedelsta)
        log.stocklist(message)
        return(self.sha)
    # 深圳A股
    def get_sza(self):
        self.sza.clear()
        start_time = datetime.now()
        index_url = 'http://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=7&AJAX=AJAX-FALSE&CATALOGID=1110&TABKEY=tab2&tab2PAGENO=1'
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(index_url)
                except:
                    pass
        index_html = r.content
        index_soup = BeautifulSoup(index_html, "html.parser")
        index = int(index_soup.select('td')[-3].text.split()[1][1:-1])
        message = '正在获取 深A 代码列表，一共%s页。' % (index+1)
        #log.stocklist(message)
        print(message)
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(self.get_sza_page, range(index))
        end_time = datetime.now()
        timedelsta = (end_time - start_time).seconds
        message = '从 深圳A股 导入%s支股票代码，耗时%s秒。' % (len(self.sza), timedelsta)
        log.stocklist(message)
        return(self.sza)
    def get_sza_page(self, page_num):
        page_num = page_num + 1
        url = 'http://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=7&AJAX=AJAX-FALSE&CATALOGID=1110&TABKEY=tab2&tab2PAGENO=%s' % page_num
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=10)
                except:
                    #print('Error!------------------------------------')
                    #message = '载入第%d页码失败' % page_num
                    #log.stocklist(message)
                    #print(message)
                    pass
        html = r.content
        soup = BeautifulSoup(html, "html.parser")
        source = soup.select('tr[bgcolor="#ffffff"]')
        source1 = soup.select('tr[bgcolor="#F8F8F8"]')
        source += source1
        for i in source:
            code = i.select('td')[2].text
            self.sza.append(code)
        #print(page_num)
    # 深圳中小板
    def get_szzx(self):
        self.szzx.clear()
        start_time = datetime.now()
        index_url = 'http://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=7&AJAX=AJAX-FALSE&CATALOGID=1110&TABKEY=tab5&tab5PAGENO=1'
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(index_url)
                except:
                    pass
        index_html = r.content
        index_soup = BeautifulSoup(index_html, "html.parser")
        index = int(index_soup.select('td')[-3].text.split()[1][1:-1])
        message = '正在获取 深圳中小板 代码列表，一共%s页。' % (index+1)
        #log.stocklist(message)
        print(message)
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(self.get_szzx_page, range(index))
        end_time = datetime.now()
        timedelsta = (end_time - start_time).seconds
        message = '从 深圳中小板 导入%s支股票代码，耗时%s秒。' % (len(self.szzx), timedelsta)
        log.stocklist(message)
        return(self.szzx)
    def get_szzx_page(self, page_num):
        page_num = page_num + 1
        url = 'http://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=7&AJAX=AJAX-FALSE&CATALOGID=1110&TABKEY=tab5&tab5PAGENO=%s' % page_num
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=10)
                except:
                    #message = '载入第%d页码失败' % page_num
                    #log.stocklist(message)
                    #print(message)
                    pass
        html = r.content
        soup = BeautifulSoup(html, "html.parser")
        source = soup.select('tr[bgcolor="#ffffff"]')
        source1 = soup.select('tr[bgcolor="#F8F8F8"]')
        source += source1
        for i in source:
            code = i.a.u.text
            self.szzx.append(code)
    # 深圳创业板
    def get_szcy(self):
        self.szcy.clear()
        start_time = datetime.now()
        index_url = 'http://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=7&AJAX=AJAX-FALSE&CATALOGID=1110&TABKEY=tab6&tab6PAGENO=1'
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(index_url)
                except:
                    pass
        index_html = r.content
        index_soup = BeautifulSoup(index_html, "html.parser")
        index = int(index_soup.select('td')[-3].text.split()[1][1:-1])
        message = '正在获取 深圳创业板 代码列表，一共%s页。' % (index+1)
        #log.stocklist(message)
        print(message)
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(self.get_szcy_page, range(index))
        end_time = datetime.now()
        timedelsta = (end_time - start_time).seconds
        message = '从 深圳创业板 导入%s支股票代码，耗时%s秒。' % (len(self.szcy), timedelsta)
        log.stocklist(message)
        return(self.szcy)
    def get_szcy_page(self, page_num):
        page_num = page_num + 1
        url = 'http://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=7&AJAX=AJAX-FALSE&CATALOGID=1110&TABKEY=tab6&tab6PAGENO=%s' % page_num
        with requests.session() as s:
            s.headers['connection'] = 'close'
            r = None
            while r == None:
                try:
                    r = s.get(url, timeout=10)
                except:
                    #message = '载入第%d页码失败' % page_num
                    #log.stocklist(message)
                    #print(message)
                    pass
        html = r.content
        soup = BeautifulSoup(html, "html.parser")
        source = soup.select('tr[bgcolor="#ffffff"]')
        source1 = soup.select('tr[bgcolor="#F8F8F8"]')
        source += source1
        for i in source:
            code = i.a.u.text
            self.szcy.append(code)
    # 载入股票
    def __load(self):
        self.stock.clear()
        message = '尝试加载%s支股票' % len(self.list)
        log.stocklist(message)
        start_time = datetime.now()
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(self.add, self.list)
        #self.__drop()
        end_time = datetime.now()
        timedelsta = (end_time - start_time).seconds
        message = '成功加载%s支股票，耗时%s秒。' % (len(self.list), timedelsta)
        log.stocklist(message)
    def __drop(self):
        c = 0
        for i in self.stock:
            if i.status == False:
                self.stock.remove(i)
                c += 1
        message = '移除%s个停牌股票' % c
        log.stocklist(message)
    def add(self, i):
        a = stock(i)
        self.stock.append(a)
        #print(i)
    def help(self):
        print('''sl.list\nsl.sha\nsl.sza\nsl.szzx\nsl.szcy\nsl.get_sha()\nsl.get_sza()\nsl.get_szzx()\nsl.get_szcy()\n
            ''')



class logging():
    def __init__(self):
        self.__check_dir()
        self.__start()
    def __check_dir(self):
        if os.path.exists('log') == False:
            os.makedirs('log')
    def __start(self):
        pool = ThreadPoolExecutor(max_workers=1)
        pool.submit(self.write)
    def write(self):
        self.list = []
        while True:
            if len(self.list) == 0:
                time.sleep(5)
            else:
                filename = self.list[0][0]
                message = self.list[0][1]
                with open('log/%s.log' % filename , 'a') as f:
                    f.write(message)
                self.list.remove(self.list[0])
    def sms(self, text):
        message = '%s  %s\n' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
        print(text)
        json = ('sms', message)
        self.list.append(json)
    def stocklist(self, text):
        message = '%s  %s\n' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
        print(text)
        json = ('stocklist', message)
        self.list.append(json)
    def worklist(self, text):
        message = '%s  %s\n' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
        print(text)
        json = ['worklist', message]
        self.list.append(json)
    # temp
    def suspend(self, text):
        message = '%s  %s\n' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
        print(text)
        json = ['suspend', message]
        self.list.append(json)


log = logging()


class sms():
    sleep = 2
    number = 16018666656
    key = 'd1258708'
    secret = 'No1secret'
    def __init__(self, phone):
        self.phone = phone
        self.list = []
        self.__login()
        self.start()
    def __login(self):
        self.__client = nexmo.Client(key=self.key, secret=self.secret)
        message = '登录短信客户端'
        #print(message)
        log.sms(message)
    def start(self):
        message = '开启发送短信'
        #print(message)
        log.sms(message)
        pool = ThreadPoolExecutor(max_workers=1)
        pool.submit(self.starter)
    def starter(self):
        self.status = True
        while self.status == True:
            if len(self.list) == 0:
                time.sleep(2)
            else:
                text = self.list[0]
                self.__send_sms(text)
                self.list.remove(text)
    def stop(self):
        self.status = False
        message = '停止发送短信'
        #print(message)
        log.sms(message)
    def send(self, text):
        self.list.append(text)
    def __send_sms(self, text):
        c = 0
        result = None
        while result != '0':
            #print(c)
            if c == 5:
                status = '失败'
                break
            result = self.__client.send_message({
            'from': self.number,
            'to': self.phone,
            'text': text,
            'type': 'unicode'
            })['messages'][0]['status']
            status = '成功'
            c += 1
        message = '发送%s： %s ' % (status, text)
        #print(message)
        sms.log(message)
    def help(self):
        print('''sms.list\nsms.send(number, text)\n/log
            ''')

sms = sms(16267318573)


def suspend_list():
    li = []
    sl = stocklist()
    for i in sl.stock:
        if i.status == False:
            li.append(i.code)
    return len(li)

def suspend_checker():
    last = 0
    while True:
        current = suspend_list()
        if current != last:
            if last != 0:
                message = '停牌列表更新%s' % current
                log.suspend(message)
                sms.send(message)
            last = current
        time.sleep(300)


print('suspend_checker()')

import code
code.interact(banner = "", local = locals())



