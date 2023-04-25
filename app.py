from flask import Flask, render_template, jsonify, request
import pandas as pd
import datetime

app = Flask(__name__)


## 데이터 불러오기 (데이터베이스 대신 로컬로 대체)
df_corp_infos = pd.read_csv('./data/corp_infos.csv', index_col=0, dtype=str) #df_corp_infos.columns = corp_code, stock_code, corp_cls, corp_name, sector, product
df_corp_infos['product'] = df_corp_infos['product'].fillna('내용없음')
df_market = pd.read_csv('./data/markets.csv', index_col=0, dtype=str) #df_market.columns = 티커,종가,시가총액,거래량,거래대금,상장주식수,날짜,BPS,PER,PBR,EPS,DIV,DPS
bookmarks = [] #북마크용


## 페이지 라우팅
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def get_result(df_corp_infos=df_corp_infos, df_market=df_market):
    search_date = request.form.get('searchDate')
    search_date = search_date.replace('-', '')
    search_keyword = request.form.get('searchKeyword')
    
    df_market = df_market.loc[df_market['날짜'] == search_date]
    df_market = df_market[['날짜', '티커', '시가총액', 'PER', 'PBR']]
    df_market.columns = ['date', 'stock_code', 'market_cap', 'PER', 'PBR']

    if search_keyword == '':
        df_searched = df_corp_infos
    else:
        df_searched = df_corp_infos.loc[df_corp_infos['product'].str.contains(search_keyword)]
    
    df_main = pd.merge(df_searched, df_market, on='stock_code', how='left')
    search_result = df_main.to_dict('records')

    return render_template('result.html', search_result=search_result)

@app.route('/bookmark', methods=['POST'])
def bookmark():
    stock_code = request.json['stock_code']
    if stock_code in bookmarks:
        bookmarks.remove(stock_code)
        message = '북마크에서 제거되었습니다.'
    else:
        bookmarks.append(stock_code)
        message = '북마크에 추가되었습니다.'
    return jsonify({'message': message, 'bookmarks': bookmarks})

@app.route('/bookmarks', methods=['GET'])
def show_bookmarks(df_corp_infos=df_corp_infos, df_market=df_market, bookmarks=bookmarks):
    
    search_date = str(datetime.date.today())
    search_date = '20230424' # test code
    df_market = df_market.loc[df_market['날짜'] == search_date]
    df_market = df_market[['날짜', '티커', '시가총액', 'PER', 'PBR']]
    df_market.columns = ['date', 'stock_code', 'market_cap', 'PER', 'PBR']
    
    if bookmarks:
        df_searched = pd.DataFrame()
        for stock_code in bookmarks:
            df_temp = df_corp_infos.loc[df_corp_infos['stock_code'] == stock_code]
            df_searched = pd.concat([df_searched, df_temp], ignore_index=True)
        df_main = pd.merge(df_searched, df_market, on='stock_code', how='left')
        search_result = df_main.to_dict('records')
    else:
        search_result = [{'stock_code': '_', 'corp_name': '_', 'market_cap': 1000000000,
                         'PER': '_', 'PBR': '_', 'sector': '북마크가 비었습니다', 'product': '_'}]
    
    return render_template('bookmarks.html', search_result=search_result)

@app.route('/readme', methods=['GET'])
def show_readme():
    return render_template('readme.html')


## 실행
if __name__ == '__main__':
    app.run(port=5001, debug=True)