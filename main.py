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


def get_lat_lon_from_address(address):
    url = 'http://www.geocoding.jp/api/'
    payload = {"v": 1.1, 'q': address}
    r = requests.get(url, params=payload)
    ret = BeautifulSoup(r.content,'lxml')
    lat = None
    lon = None
    if ret.find('error'):
        pass
    else:
        lat = float(ret.find('lat').string)
        lon = float(ret.find('lng').string)
    time.sleep(1)
    return pd.Series ([lat,lon])

# %% [markdown]
# ### csvファイルの一覧を作成
data_path = pathlib.Path('data')
flist = data_path.glob('*.csv')

# %% [markdown]
# ### csvファイル毎にデータを読み込む
tintai_info_df = None
for datafile in flist:
    if tintai_info_df is None:
        tintai_info_df = pd.read_csv(str(datafile), sep='\t')
    else:
        df = pd.read_csv(str(datafile), sep='\t')
        tintai_info_df = pd.concat([tintai_info_df,df])


# %% [markdown]
# ### サンプルキャッシュがあればそれを使う 
sample_data100 = None
if os.path.exists('sample.pkl') == True:
    sample_data100 = pd.read_pickle('sample.pkl')

# %% [markdown]
# ### 実験中は20個のサンプルに絞って行う 
if sample_data100 is None:
    sample_data100 = df.sample(10)

    # %% [markdown]
    # ### 1列目のカラム名を変更する 
    sample_data100.rename(columns={'Unnamed: 0':'No'}, inplace=True)
    print(sample_data100['No'].head(30))

    # %% [markdown]
    # ### No列のindex列に指定し、resetする 
    sample_data100.set_index('No',inplace=True)
    sample_data100 = sample_data100.reset_index(drop=True)

    # ### 階列にある余計な\rや\nや\tを消す 
    sample_data100['階'] = sample_data100['階'].apply((lambda x:x.replace('\r','').replace('\n','').replace('\t','')))
    print(sample_data100.head())

    # %% [markdown]
    # ## 住所列から緯度経度を取得 
    sample_data100[['緯度','経度']] = sample_data100['住所'].apply(get_lat_lon_from_address)

    sample_data100.to_pickle('sample.pkl')

# %% [markdown]
# ## 経度、緯度が0.0のものがあれば再取得を試みる 
lon_zero = (sample_data100['経度'] == 0.0)
zero_count = lon_zero.sum()
print(zero_count)
if zero_count > 0:
    # 取得できたら、キャッシュを更新する
    zero_list = sample_data100[lon_zero]
    print(zero_list)
    sample_data100[lon_zero] = zero_list.apply(get_lat_lon_from_address)
# %% [markdown]
# ## 経度、緯度が0.0のものは除外する 
sample_data100 = sample_data100[sample_data100['経度'] != 0.0]

# %% [markdown]
# ## 経度、緯度のmax,minから座標に変換する 
lat_max = sample_data100['緯度'].max()
lat_min = sample_data100['緯度'].min()
lon_max = sample_data100['経度'].max()
lon_min = sample_data100['経度'].min()

print(lat_min,lat_max,lon_min,lon_max)

# %% [markdown]
# ## 経度と緯度を座標に変換 
# ## メモリは400x400とする
sample_data100['x'] = sample_data100['経度'].apply((lambda lon: (lon - lon_min)*400 / (lon_max-lon_min)))
sample_data100['y'] = sample_data100['緯度'].apply((lambda lat: (lat - lat_min)*400 / (lat_max-lat_min)))

# ## pt の計算
# ## まずはフィルター
# %% [markdown]
# 住所をもとに散布図に表示
# ptによって色を変える
sc = plt.scatter(sample_data100['x'], sample_data100['y'], vmin=-1, vmax=1, c=y, cmap=cm.seismic)
plt.colorbar(sc)
plt.ylabel('緯度')
plt.xlabel('経度')
# 大きな駅名は目印としてグラフに記入する
plt.show()

#%%
