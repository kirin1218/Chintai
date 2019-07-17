# -*- coding:utf-8 -*-
# %% [markdown]
from bs4 import BeautifulSoup
import requests

def get_fudosan_detail(url):
	result = requests.get(url)
	c = result.content

	print(c)
	#HTMLを元に、オブジェクトを作る
	soup = BeautifulSoup(c)

	#物件リストの部分を切り出し
	summary_area = soup.find("div",{'class':'section_h1'})
	detail_area = soup.find("div",{'id':'contents'})

	fudosan_info = {}
	# 物件概要
	# 物件名
	fudosan_info['物件名'] = summary_area.find('h1', class_="section_h1-header-title").text.strip()

	# 概要一覧
	summary_tbl = summary_area.find('table',{'class':'property_view_table'})
	summary_infos = summary_tbl.find_all('tr') 
	for summary_info in summary_infos:
		thtds = summary_info.find_all(['th','td'],recursive=False) 
		i = 0
		while i < len(thtds):
			if thtds[i].name == 'th':
				if thtds[i+1].name == 'td':
					fudosan_info[thtds[i].text.strip()] = thtds[i+1].text.strip()
					i+=1
			i+=1
		pass

	fudosan_info['設備情報'] = detail_area.find('div',{'class':'section l-space_small'}).text.strip()

	detail_tbl = detail_area.find('table',{'class':'data_table table_gaiyou'})
	detail_infos = detail_tbl.find_all('tr') 
	for detail_info in detail_infos:
		thtds = detail_info.find_all(['th','td'],recursive=False) 
		i = 0
		while i < len(thtds):
			if thtds[i].name == 'th':
				if thtds[i+1].name == 'td':
					fudosan_info[thtds[i].text.strip()] = thtds[i+1].text.strip()
					i+=1
			i+=1
		pass

	return fudosan_info

if __name__ == '__main__':
	url = 'https://suumo.jp/chintai/jnc_000049951749/?bc=100159591932'

	ret = get_fudosan_detail(url)
	pass
		





#%%
