from flask import Flask, render_template, redirect, jsonify, request
import pandas as pd


app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return render_template('main.html')


@app.route('/main/', methods=['POST'])
def get_result():
    search_date = request.form.get('searchDate')
    search_date = search_date.replace('-', '')
    search_keyword = request.form.get('searchKeyword')

    df_corp_infos = pd.read_csv('./data/corp_infos.csv', index_col=0, dtype=str)
    df_market = pd.read_csv('./data/markets.csv', index_col=0, dtype=str)

    df_corp_infos['product'] = df_corp_infos['product'].fillna('내용없음')
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


if __name__ == '__main__':
    app.run(port=5001, debug=True)