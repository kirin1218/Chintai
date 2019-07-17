# %% [markdown]
import matplotlib.pyplot as plt
import matplotlib as mpl
from pandas.plotting import scatter_matrix
import os
import sys
import pathlib
import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import pandas as pd
import pickle

API_KEY = 'AIzaSyByqaMi26ibhryMtUE5e6JygDj0yEJ2Vys'
# -*- coding: utf-8 -*-
import requests
import json
from time import sleep

wait_time = 0.3 # (sec)

class chintai_area_data:
    def __init__(self, csv_path ):
        self.csv_path = pathlib.Path(csv_path)
        self.csv_fname = self.csv_path.name
        self.fname_no_ext = str(self.csv_fname).split('.')[0]
        # suumo_12345みたいな感じ
        self.area_id = self.fname_no_ext.split('_')[1]
        self.convert_phase = 0
        self.df = None
        self.address_to_geocode = {}

        self.load()

    def load(self):
        pkl_fname = self.fname_no_ext + '.pkl'
        # 0 -> 1st csvをdfにしただけ
        first_phase_path = '1phase_data/' + pkl_fname
        # 1st -> 2nd csvをdfにしただけ
        second_phase_path = '2phase_data/' + pkl_fname
        third_phase_path = '3phase_data/' + pkl_fname

        if os.path.exists(third_phase_path) == True:
            self.df = pd.read_pickle(third_phase_path)
            self.convert_phase =3 
        elif os.path.exists(second_phase_path) == True:
            self.df = pd.read_pickle(second_phase_path)
            self.convert_phase =2 
        elif os.path.exists(first_phase_path) == True:
            self.df = pd.read_pickle(first_phase_path)
            self.convert_phase = 1
        else:
            self.df = pd.read_csv(str(datafile), sep='\t')
            self.df.to_pickle(first_phase_path)
            self.convert_phase = 1 
        # self.df = self.df.sample(10)

    def convert1to2(self):
        # ### 1列目のカラム名を変更する 
        self.df.rename(columns={'Unnamed: 0':'No'}, inplace=True)

        # %% [markdown]
        # ### No列のindex列に指定し、resetする 
        self.df.set_index('No',inplace=True)
        self.df = self.df.reset_index(drop=True)

        # ### 階列にある余計な\rや\nや\tを消す 
        self.df['階'] = self.df['階'].apply((lambda x:x.replace('\r','').replace('\n','').replace('\t','')))

        self.df['経度'] = 0.0
        self.df['緯度'] = 0.0
        self.df['x'] = 0.0
        self.df['y'] = 0.0
        self.df['pt'] = 0.0

        pkl_fname = self.fname_no_ext + '.pkl'
        second_phase_path = '2phase_data/' + pkl_fname

        self.df.to_pickle(second_phase_path)
        self.convert_phase = 2 

    def convert_areastr_to_areaint(self,area_str):
        ret_area = 0
        if 'm' in area_str:
            ret_area = float(area_str.split('m')[0])  
        else:
            ret_area = float(area_str)
        return ret_area

    def convert_princestr_to_priceint(self,price_str):
        ret_price = 0
        if '万円' in price_str:
            ret_price = int(float(price_str.split('万円')[0]) * 10000)  
        elif '円' in price_str:
            ret_price = int(price_str.split('円')[0])  
        elif price_str == '-':
            ret_price = 0  
        else:
            ret_price = int(price_str)
        return ret_price


    # 家賃を9万円→90000にする
    def convert2to3(self):
        self.df['price_int'] = self.df['賃料'].apply(self.convert_princestr_to_priceint)
        self.df['mgr_fee_int'] = self.df['管理費'].apply(self.convert_princestr_to_priceint)
        self.df['area_int'] = self.df['専有面積'].apply(self.convert_areastr_to_areaint)

        pkl_fname = self.fname_no_ext + '.pkl'
        phase_path = '3phase_data/' + pkl_fname

        self.df.to_pickle(phase_path)
        self.convert_phase = 3 

    def get_lat_lon_from_address(self,address):
        if not address in self.address_to_geocode:
            base_url = 'https://maps.googleapis.com/maps/api/geocode/json?language=ja&address={}&key=' + API_KEY
            headers = {'content-type': 'application/json'}

            url = base_url.format(address)
            r = requests.get(url, headers=headers)
            data = r.json()

            lat = None
            lon = None
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                if 'geometry' in result and len(result['geometry']) > 0:
                    geometry = result['geometry']
                    if 'location' in geometry and len(geometry['location']) > 0:
                        location = geometry['location']

                        lat = float(location['lat'])
                        lon = float(location['lng'])

            self.address_to_geocode[address] = pd.Series ([lon,lat])
            time.sleep(1)

        return self.address_to_geocode[address]
        
        '''
        sleep(wait_time)
        url = 'http://www.geocoding.jp/api/'
        payload = {"v": 1.1, 'q': address}
        r = requests.get(url, params=payload)
        ret = BeautifulSoup(r.content,'lxml')
        if ret.find('error'):
            pass
        else:
            lat = float(ret.find('lat').string)
            lon = float(ret.find('lng').string)
        time.sleep(1)
        return pd.Series ([lat,lon])
        '''

    def update_lat_lon(self):
        # 予め住所一覧を作成しておく
        # 0じゃないものの一覧を作成する
        lon_zero = (self.df['経度'] == 0.0)
        zero_count = lon_zero.sum()
        if zero_count > 0:
            if zero_count == len(self.df):
                # 取得できたら、キャッシュを更新する
                self.df[['経度','緯度']] = self.df['住所'].apply(self.get_lat_lon_from_address)

                print(self.df['経度'] == 0.0)

                pkl_fname = self.fname_no_ext + '.pkl'
                third_phase_path = '3phase_data/' + pkl_fname

                self.df.to_pickle(third_phase_path)
            else:
                # 大体とれてると信じて、一個一個確認
                for row in self.df:
                    if row['経度'] == 0.0:
                        pass
        else:
            err_data = (self.df['経度'] < 100 )
            if err_data.sum() > 0:
                for index, row in self.df.iterrows():
                    if row['経度'] < row['緯度']:
                        lon = row['緯度']
                        lat = row['経度']
                        self.df.at[index,'経度'] = lon
                        self.df.at[index,'緯度'] = lat

                pkl_fname = self.fname_no_ext + '.pkl'
                third_phase_path = '3phase_data/' + pkl_fname

                self.df.to_pickle(third_phase_path)



class infos_per_address:
    def __init__(self):
        self.chintai_info = None 
        self.rent_avg = 0
        self.mgr_fee_avg = 0
        self.area_avg = 0

    def additem(self,info):
        if self.chintai_info is None:
            self.chintai_info = info 
        else:
            self.chintai_info = pd.concat([self.chintai_info,info])

    def calc_average(self):
        self.rent_avg = self.chintai_info['price_int'].mean()
        self.mgrfee_avg = self.chintai_info['mgr_fee_int'].mean()
        self.area_avg = self.chintai_info['area_int'].mean()
        pass


chintai_area_data_list = []

# %% [markdown]
# ### csvファイルの一覧を作成
data_path = pathlib.Path('original_data')
flist = data_path.glob('*.csv')

# %% [markdown]
# ### csvファイル毎にデータを読み込む
chintai_info_df = None
for datafile in flist:
    chintai_area_data_list.append(chintai_area_data(datafile))

for area_data in chintai_area_data_list:
    if area_data.convert_phase < 2:
        area_data.convert1to2()

for area_data in chintai_area_data_list:
    if area_data.convert_phase < 3:
        area_data.convert2to3()

# 住所から緯度経度を取得する
for area_data in chintai_area_data_list:
    area_data.update_lat_lon()

view_list = None
#view_list = [13107,13108,13123]
#view_list = [13101]
# areaのフィルターをする場合はここで行う
for area_data in chintai_area_data_list:
    id = int(area_data.area_id)
    if (view_list is None) or (id in view_list):
        # まずは、pklがないか確認
        if chintai_info_df is None:
            chintai_info_df = area_data.df
        else:
            chintai_info_df = pd.concat([chintai_info_df,area_data.df])

chintai_info_df = chintai_info_df.reset_index(drop=True)

#print(len(chintai_info_df))
#chintai_info_df = chintai_info_df.query('40.0 < area_int and area_int < 60.0')
#print(len(chintai_info_df))
#chintai_info_df = chintai_info_df.sample(int(len(chintai_info_df)/10))

# %% [markdown]
# ## 経度、緯度のmax,minから座標に変換する 
lat_max = chintai_info_df['緯度'].max()
lat_min = chintai_info_df['緯度'].min()
lon_max = chintai_info_df['経度'].max()
lon_min = chintai_info_df['経度'].min()

print(lat_min,lat_max,lon_min,lon_max)


# ユニークな住所の一覧を作成する
unique_address_list = chintai_info_df['住所']

address_list = []
price_avg_list = []
x_list = []
y_list = []

address_groupby_mean = chintai_info_df.groupby('住所').mean()
address_groupby_sum = chintai_info_df.groupby('住所').sum()

'''
for index, row in tqdm(address_groupby_sum.iterrows()):
    address = row.name 
    target_rows = chintai_info_df[chintai_info_df['住所']==address]
    target_rows = target_rows.reset_index(drop=True)
    lon = target_rows.at[0,'経度']
    lat = target_rows.at[0,'緯度']
    price_avg_list.append((row['price_int']+row['mgr_fee_int'])/row['area_int'])
    x = (lon - lon_min)*1000 / (lon_max-lon_min)
    y = (lat - lat_min)*700 / (lat_max-lat_min)
    x_list.append(x)
    y_list.append(y)
    pass
'''
for index, row in tqdm(address_groupby_mean.iterrows()):
    address = row.name 
    target_rows = chintai_info_df[chintai_info_df['住所']==address]
    target_rows = target_rows.reset_index(drop=True)
    lon = target_rows.at[0,'経度']
    lat = target_rows.at[0,'緯度']
    price_avg_list.append(row['area_int'])
    x = (lon - lon_min)*1000 / (lon_max-lon_min)
    y = (lat - lat_min)*700 / (lat_max-lat_min)
    x_list.append(x)
    y_list.append(y)
    pass
'''
for address in unique_address_list:
    address_list.append(address)
    sameaddr_list = (chintai_info_df['住所'] == address)
    rent_sum = chintai_info_df[sameaddr_list]['price_int'].sum()
    mgrfee_sum = chintai_info_df[sameaddr_list]['mgr_fee_int'].sum()
    area_sum = chintai_info_df[sameaddr_list]['area_int'].sum()
    price_avg_list.append((rent_sum+mgrfee_sum)/area_sum)
    lon = chintai_info_df[sameaddr_list]['経度'].mean()
    lat = chintai_info_df[sameaddr_list]['緯度'].mean()
    x = (lon - lon_min)*1000 / (lon_max-lon_min)
    y = (lat - lat_min)*700 / (lat_max-lat_min)
    x_list.append(x)
    y_list.append(y)
    pass
'''


# ## pt の計算
# ## まずはフィルター
# %% [markdown]
# 住所をもとに散布図に表示
# ptによって色を変える
#sc = plt.scatter(x_list, y_list, vmin=-1, vmax=1, c=y, cmap=cm.seismic)
sc = plt.scatter(x_list, y_list, c=price_avg_list, cmap='Blues')
#sc = plt.scatter(chintai_info_df['x'], chintai_info_df['y'])
plt.colorbar(sc)
plt.ylabel('緯度')
plt.xlabel('経度')
'''
x = (139.814003 - lon_min)*1000 / (lon_max-lon_min)
y = (35.695106 - lat_min)*700 / (lat_max-lat_min)
plt.text(x, y, r'Kinsi')
plt.plot(x,y,marker='.')

x = (139.87312 - lon_min)*1000 / (lon_max-lon_min)
y = (35.663405 - lat_min)*700 / (lat_max-lat_min)
plt.text(x, y, r'Kasai')
plt.plot(x,y,marker='.')

x = (139.816345 - lon_min)*1000 / (lon_max-lon_min)
y = (35.671669 - lat_min)*700 / (lat_max-lat_min)
plt.text(x, y, r'toyocho')
plt.plot(x,y,marker='.')


x = (139.700391 - lon_min)*1000 / (lon_max-lon_min)
y = ( 35.689738 - lat_min)*700 / (lat_max-lat_min)
plt.text(x, y, r'Shinjuku')
'''
x = (139.767125 - lon_min)*1000 / (lon_max-lon_min)
y = (35.681236 - lat_min)*700 / (lat_max-lat_min)
plt.text(x, y, r'Tokyo')
# 大きな駅名は目印としてグラフに記入する
plt.show()

#%%
