# -*- coding: utf-8 -*-
'''
@dateTm: 2019-09-20
@author: liqingyun
'''
# -*- coding: utf-8 -*-

from urllib import request
from urllib import error
from bs4 import BeautifulSoup
from multiprocessing import Pool
from multiprocessing import Manager
import re
import time
import os
import datetime


# 运行路径
dir_url = os.path.dirname(os.path.realpath(__file__))
cache_txt = dir_url + '/cache.txt'
url_txt = dir_url + '/url.txt'

domain = 'http://dzwz7.ncms5.hnjing.net'
cache = []

def remove(filename):
	'''
	清空文件
	'''
	f = open(filename, 'a+', encoding='utf-8')
	f.seek(0)
	f.truncate()
	f.close()

def getHtml(url, ua_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko', num_retries=5):
	'''
	读取html页面
	'''
	headers = {'User-Agent': ua_agent}
	req = request.Request(url, headers=headers)
	html = None
	try:
		response = request.urlopen(req)
		html = response.read().decode('utf-8')
	except error.URLError or error.HTTPError as e:
		if num_retries > 0:
			if hasattr(e, 'code') and 500 <= e.code < 600:
				getHtml(url, ua_agent, num_retries - 1)
	return html

def get_urls(html):
	'''
	获取当前页面中所有的超链接的列表信息
	'''
	links = []
	soup = BeautifulSoup(html, 'html.parser')
	url_list = soup.find_all('a')
	for link in url_list:
		links.append(link.get('href'))
	return links

#    匹配规则^http或者com$,cn$
def save_file(murl, fileName):
	with open(fileName, 'ab') as f:
		f.write(murl.encode())

def CrawlInfo(url, q):
	# 获取当前节点的信息
	global crawl_queue
	global cache
	crawl_queue = []  # 声明待爬队列
	hlinks = []

	print('------- Begin ------')
	print('url: ' + url)
	print('------- Loop ------')

	html = getHtml(url)
	links = get_urls(html)
	for murl in links:
		if re.findall('^http', str(murl)):
			if domain in str(murl):
				murl = str(murl)
				hlinks.append(murl)
				cache.append(murl)
				save_file(murl + '\n', cache_txt)
				print(murl)
		elif re.findall('^//', str(murl)):
			if domain in str(murl):
				murl = 'http:' + str(murl)
				hlinks.append(murl)
				cache.append(murl)
				save_file(murl + '\n', cache_txt)
				print(murl)
		elif re.findall('^/', str(murl)):
			murl = domain + str(murl)
			hlinks.append(murl)
			cache.append(murl)
			save_file(murl + '\n', cache_txt)
			print(murl)
		elif re.findall('^javascript', str(murl)):
			links.remove(murl)
		else:
			pass
	for _ in hlinks:
		crawl_queue.append(_)
		time.sleep(0.1)
	q.put(url)  # 当前的URL处理完成，通知主进程

if __name__ == '__main__':
	# 清空缓存文件
	remove(cache_txt)
	remove(url_txt)
	# 使用进程池
	pool = Pool()
	q = Manager().Queue()
	crawled_queue = []  # 已爬队列
	seedUrl = domain + ''
	# 当前页的处理
	CrawlInfo(seedUrl, q)
	crawl_queue.append(seedUrl)
	# 在待爬队列中再做一次去重
	crawl_queue = list(set(crawl_queue))
	# 抓取队列中的信息为空，则退出循环
	while crawl_queue:
		url = crawl_queue.pop(0)
		# 用进程池中的进程来处理这个URL
		pool.apply_async(func=CrawlInfo, args=(url, q))
		# 处理完之后，需要把这个url放入已爬队列中
		url = q.get()
		crawled_queue.append(url)
	pool.close()
	pool.join()

	# 去重
	cache = list(set(cache))
	cache.sort()
	# print(cache)
	
	# 写入
	for index, item in enumerate(cache):
		if index == 0:
			save_file('created by: ' + str(datetime.datetime.now()) + '\n', url_txt)
		save_file(item + '\n', url_txt)
		# print(item)
	print('End')