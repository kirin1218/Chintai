# -*- coding:utf-8 -*-
# %% [markdown]
# ## 必要なライブラリをインポート
#必要なライブラリをインポート
from bs4 import BeautifulSoup
import requests
import pandas as pd
from pandas import Series, DataFrame
import time
import os, sys
from fudosan_detail import get_fudosan_detail

class RoomInfo:
    def __init__(self):
        self.floor = ""      #階
        self.rent  = ""      #賃料
        self.mgr_fee  = ""   #管理費
        self.deposit  = ""   #敷金
        self.keymoney  = ""  #礼金
        self.floor_plan  = ""#間取り
        self.area  = ""      #専有面積
    '''
    @property
    def floor(self):
        return self._val
    @floor.setter
    def floor(self,value):
        self._val = value
    '''

class BuildingInfo:
    def __init__(self):
        self.name = ""      #マンション名
        self.address = ""   #住所
        self.height  = ""   #建物の階数
        self.age = ""       #築年数
        self.locations0 = "" #立地1つ目（最寄駅/徒歩~分）
        self.locations1 = "" #立地2つ目（最寄駅/徒歩~分）
        self.locations2 = "" #立地3つ目（最寄駅/徒歩~分）
        self.room_info = []
#URL（東京都足立区の賃貸住宅情報 検索結果の1ページ目）
url_head = 'http://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc='
url_foot = '&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1'
city_ids = ['13101','13102','13103' ,'13104' ,'13105' ,'13113' ,'13106' ,'13107' \
,'13108' ,'13118' ,'13121' ,'13122' ,'13123' ,'13109' ,'13110' ,'13111' \
,'13112' ,'13114' ,'13115' ,'13120' ,'13116' ,'13117' ,'13119']

for cityid in city_ids:
    outputpath  ='alldata/suumo_' + cityid + '.csv'
    if os.path.exists(outputpath) == True:
        continue

    url = url_head + cityid + url_foot
    #データ取得
    result = requests.get(url)
    c = result.content

    #HTMLを元に、オブジェクトを作る
    soup = BeautifulSoup(c)

    #物件リストの部分を切り出し
    summary = soup.find("div",{'id':'js-bukkenList'})
    #ページ数を取得
    body = soup.find("body")
    pages = body.find_all("div",{'class':'pagination pagination_set-nav'})
    pages_text = str(pages)
    pages_split = pages_text.split('</a></li>\n</ol>')
    pages_split0 = pages_split[0]
    pages_split1 = pages_split0[-3:]
    pages_split2 = pages_split1.replace('>','')
    pages_split3 = int(pages_split2)
    #URLを入れるリスト
    urls = []

    #1ページ目を格納
    urls.append(url)

    #2ページ目から最後のページまでを格納
    for i in range(pages_split3-1):
        pg = str(i+2)
        url_page = url + '&pn=' + pg
        urls.append(url_page)


    fudosan_df = None
    fudosan_detail_infos =[]

    #各ページで以下の動作をループ
    for url in urls:
        print(url)
        #物件リストを切り出し
        result = requests.get(url)
        c = result.content
        soup = BeautifulSoup(c)
        summary = soup.find("div",{'id':'js-bukkenList'})
        
        #マンション名、住所、立地（最寄駅/徒歩~分）、築年数、建物高さが入っているcassetteitemを全て抜き出し
        cassetteitems = summary.find_all("div",{'class':'cassetteitem'})

        #各cassetteitemsに対し、以下の動作をループ
        for i in range(len(cassetteitems)):
            bs_roomlist = cassetteitems[i].find('div', class_="cassetteitem-item")

            #階、賃料、管理費、敷/礼/保証/敷引,償却、間取り、専有面積が入っているtableを全て抜き出し
            rooms_table = bs_roomlist.find('table','cassetteitem_other' )
            rows = rooms_table.find_all('tbody')

            #各部屋に対して、tableに入っているtext情報を取得し、dataリストに格納
            data = []
            for row in rows:
                tr = row.find('tr')
                if tr is not None:
                    detail_anchor = tr.find('a',{'class':'js-cassette_link_href'})
                    if detail_anchor is not None:
                        detail_url = detail_anchor.get('href')
                        d_url = 'https://suumo.jp' + detail_url
                        detailinfo = get_fudosan_detail(d_url)
                        detailinfo['URL'] = d_url

                        df = pd.io.json.json_normalize(detailinfo)
                        if fudosan_df is None:
                            fudosan_df = df
                        else:
                            fudosan_df = pd.concat([fudosan_df,df])

                        fudosan_detail_infos.append(detailinfo)

                        time.sleep(5)
                        pass
                
        #プログラムを5秒間停止する（スクレイピングマナー）
        time.sleep(5)

        if len(fudosan_df) > 20:
            break

    #csvファイルとして保存
    fudosan_df.to_csv(outputpath, sep = '\t',encoding='utf-8')
