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

    buuildinginfos = [] 

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
            # ページ構成
            bs_detail = cassetteitems[i].find('div', class_="cassetteitem-detail")
            bs_roomlist = cassetteitems[i].find('div', class_="cassetteitem-item")

            if bs_detail is not None and bs_roomlist is not None:
                buildinfo = BuildingInfo()

                #各建物から売りに出ている部屋数を取得
                tbodies = bs_detail.find_all('tbody')
                
                #マンション名取得
                subtitle = bs_detail.find_all("div",{
                    'class':'cassetteitem_content-title'})
                subtitle = str(subtitle)
                subtitle_rep = subtitle.replace(
                    '[<div class="cassetteitem_content-title">', '')
                subtitle_rep2 = subtitle_rep.replace(
                    '</div>]', '')

                #住所取得
                subaddress = bs_detail.find_all("li",{
                    'class':'cassetteitem_detail-col1'})
                subaddress = str(subaddress)
                subaddress_rep = subaddress.replace(
                    '[<li class="cassetteitem_detail-col1">', '')
                subaddress_rep2 = subaddress_rep.replace(
                    '</li>]', '')
                
                #部屋数だけ、マンション名と住所を繰り返しリストに格納（部屋情報と数を合致させるため）
                buildinfo.name = subtitle_rep2
                buildinfo.address = subaddress_rep2
                '''
                for y in range(len(tbodies)):
                    name.append(subtitle_rep2)
                    address.append(subaddress_rep2)
                '''

                #立地を取得
                sublocations = bs_detail.find('li', class_="cassetteitem_detail-col2")
                
                #立地は、1つ目から3つ目までを取得（4つ目以降は無視）
                if sublocations is not None:
                    cols = sublocations.find_all('div')
                    for i in range(len(cols)):
                        text = cols[i].find(text=True)
                        if buildinfo.locations0 == "":
                            buildinfo.locations0 = text
                        elif buildinfo.locations1 == "":
                            buildinfo.locations1 = text
                        elif buildinfo.locations2 == "":
                            buildinfo.locations2 = text
                        else:
                            break
                                
                #築年数と建物高さを取得
                col3 = bs_detail.find('li', class_="cassetteitem_detail-col3")
                if col3 is not None:
                    cols = col3.find_all('div')
                    for i in range(len(cols)):
                        text = cols[i].find(text=True)
                        if buildinfo.age == "":
                            buildinfo.age = text 
                        elif buildinfo.height == "":
                            buildinfo.height = text 
                        else:
                            break

            #階、賃料、管理費、敷/礼/保証/敷引,償却、間取り、専有面積が入っているtableを全て抜き出し
            rooms_table = bs_roomlist.find('table','cassetteitem_other' )
            rows = rooms_table.find_all('tbody')

            #各部屋に対して、tableに入っているtext情報を取得し、dataリストに格納
            data = []
            for row in rows:

                floor_val = ""
                rent_val = ""
                admin_val = ""
                deposit_val = ""
                keymoney_val = ""
                floor_plan_val = ""
                area_val = ""

                tr = row.find('tr')
                if tr is not None:
                    cols = tr.find_all('td')
                    for td in cols:
                        text = td.find(text=True)
                        # 階数
                        if '階' in text:
                            floor_val = text
                        # 賃料 
                        if td.select('span.cassetteitem_price--rent'):
                            price_item = td.select('span.cassetteitem_price--rent')
                            rent_val = price_item[0].find(text=True)
                        # 管理費 
                        if td.select('span.cassetteitem_price--administration'):
                            adminprice_item = td.select('span.cassetteitem_price--administration')
                            admin_val = adminprice_item[0].find(text=True)
                        # 敷金 
                        if td.select('span.cassetteitem_price--deposit'):
                            deposit_item = td.select('span.cassetteitem_price--deposit')
                            deposit_val = deposit_item[0].find(text=True)
                        # 礼金 
                        if td.select('span.cassetteitem_price--gratuity'):
                            keymoney_item = td.select('span.cassetteitem_price--gratuity')
                            keymoney_val = keymoney_item[0].find(text=True)
                        # 間取り 
                        if td.select('span.cassetteitem_madori'):
                            madori_item = td.select('span.cassetteitem_madori')
                            floor_plan_val = madori_item[0].find(text=True)
                        # 面積 
                        if td.select('span.cassetteitem_menseki'):
                            menseki_item = td.select('span.cassetteitem_menseki')
                            area_val = menseki_item[0].find(text=True)

                if floor_val != "":
                    room_info = RoomInfo()
                    room_info.floor = floor_val
                    room_info.rent = rent_val
                    room_info.mgr_fee = admin_val
                    room_info.deposit = deposit_val
                    room_info.keymoney = keymoney_val
                    room_info.floor_plan = floor_plan_val
                    room_info.area = area_val

                    buildinfo.room_info.append(room_info)
                
            buuildinginfos.append(buildinfo)
        #プログラムを10秒間停止する（スクレイピングマナー）
        time.sleep(10)

    name = [] #マンション名
    address = [] #住所
    locations0 = [] #立地1つ目（最寄駅/徒歩~分）
    locations1 = [] #立地2つ目（最寄駅/徒歩~分）
    locations2 = [] #立地3つ目（最寄駅/徒歩~分）
    age = [] #築年数
    height = [] #建物高さ
    floor = [] #階
    rent = [] #賃料
    admin = [] #管理費
    deposit = [] #敷金
    keymoney = [] #礼金
    floor_plan = [] #間取り
    area = [] #専有面積

    for i in range(len(buuildinginfos)):
        buildinfo = buuildinginfos[i]
        room_infos = buildinfo.room_info
        for j in range(len(room_infos)):
            roominfo  = room_infos[j]

            name.append(buildinfo.name)
            address.append(buildinfo.address)
            locations0.append(buildinfo.locations0)
            locations1.append(buildinfo.locations1)
            locations2.append(buildinfo.locations2)
            age.append(buildinfo.age)
            height.append(buildinfo.height)
            floor.append( roominfo.floor)
            rent.append(roominfo.rent)
            admin.append(roominfo.mgr_fee)
            deposit.append(roominfo.deposit)
            keymoney.append(roominfo.keymoney)
            floor_plan.append(roominfo.floor_plan)
            area.append(roominfo.area)

    #各リストをシリーズ化
    name = Series(name)
    address = Series(address)
    locations0 = Series(locations0)
    locations1 = Series(locations1)
    locations2 = Series(locations2)
    age = Series(age)
    height = Series(height)
    floor = Series(floor)
    rent = Series(rent)
    admin = Series(admin)
    deposit = Series(deposit)
    keymoney = Series(keymoney)
    floor_plan = Series(floor_plan)
    area = Series(area)

    #各シリーズをデータフレーム化
    suumo_df = pd.concat([name, address, locations0, locations1, locations2, age, height, floor, rent, admin, deposit, keymoney, floor_plan, area], axis=1)

    #カラム名
    suumo_df.columns=['マンション名','住所','立地1','立地2','立地3','築年数','建物高さ','階','賃料','管理費', '敷金', '礼金', '間取り','専有面積']

    #csvファイルとして保存
    suumo_df.to_csv(outputpath, sep = '\t',encoding='utf-8')
