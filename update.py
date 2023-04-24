import pandas as pd
from datetime import date, timedelta
import dart_fss
from pykrx import stock

## 1. corp_infos 업데이트

# dart_api key 입력 및 세팅
api_key = 'e95ca384dcaf2c2d4af1015df1ac87c6c7c3c22e'
dart_fss.set_api_key(api_key=api_key)

# corp_list 불러오기
corp_list = dart_fss.get_corp_list()

# corp.info 불러와서 -> df_corp_infos
corp_infos = [corp.info for corp in corp_list.corps]
df_corp_infos = pd.DataFrame(corp_infos)

# 데이터 전처리
df_corp_infos = df_corp_infos.loc[df_corp_infos['corp_cls'].isin(['Y', 'K'])].copy()  # 상장사만 필터링
df_corp_infos = df_corp_infos.drop(df_corp_infos[df_corp_infos['issue'].notnull()].index).copy()  # 상장폐지사유 발생기업 드랍
df_corp_infos = df_corp_infos.sort_values(by='corp_name')  # 회사명 순으로 정렬
df_corp_infos = df_corp_infos.reset_index(drop=True)  # 리셋 인덱스
df_corp_infos = df_corp_infos[['corp_code', 'stock_code', 'corp_cls', 'corp_name', 'sector', 'product']] # 종목코드, 시장, 종목명, 섹터, 프로덕트
df_corp_infos['product'] = df_corp_infos['product'].fillna('내용없음')

df_corp_infos.to_csv('./data/corp_infos.csv', mode='w')

## 2. market 업데이트

# 수정할 날짜 지정
# last update = 2023-04-21
start_date = date(2023, 4, 22)
end_date = date(2023, 4, 21)

# 추가할 날짜 리스트 만들기
delta = timedelta(days=1)
dates = []
while start_date <= end_date:
    dates.append(start_date.strftime('%Y%m%d'))
    start_date += delta

print(dates)

# 개별 데이터 뽑기
caps = []
funds = []
for single_date in dates:
    cap = stock.get_market_cap(single_date).reset_index()
    cap['날짜'] = single_date
    caps.append(cap)
    kospi = stock.get_market_fundamental(single_date).reset_index()
    kosdaq = stock.get_market_fundamental(single_date, market='KOSDAQ').reset_index()
    fund = pd.concat([kospi, kosdaq], ignore_index=True)
#     fund['날짜'] = single_date
    funds.append(fund)

# 합치기
markets = pd.DataFrame()
for i in range(len(dates)):
    market = pd.merge(caps[i], funds[i], on='티커', how='left')
    markets = pd.concat([markets, market], ignore_index=True)

markets.to_csv('./data/markets.csv', mode='a')






