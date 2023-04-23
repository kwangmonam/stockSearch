from flask import Flask, render_template, redirect, jsonify, request
import pandas as pd
import requests
import xmltodict
import dart_fss
from pykrx import stock


app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/main/', methods=['POST'])
def search_by_keyword():
    global api_key
    global search_date
    global search_keyword
    api_key = request.form['api_key']
    search_date = request.form['search_date']
    search_keyword = request.form['search_keyword']
    return render_template('main.html')


@app.route('/search_keyword/', methods=['GET'])
def get_search_keyword():
    return_keyword = search_keyword
    return jsonify({'return_keyword': return_keyword})


@app.route('/searched_corps/', methods=['GET'])
def get_searched_corps():
    # dart_fss 세팅
    dart_fss.set_api_key(api_key=api_key) #api_key 들어오고

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

    df_market_cap = stock.get_market_cap(search_date) #search_date 들어오고
    df_market_cap = df_market_cap.reset_index()
    df_market_cap = df_market_cap[['티커', '시가총액']]
    df_market_cap.columns = ['stock_code', 'market_cap']

    df_main = pd.merge(df_corp_infos, df_market_cap, on='stock_code')

    # listed_corps = df_main.to_dict('records')

    # 검색된 키워드 입력
    df_searched = df_main.loc[df_main['product'].str.contains(search_keyword)] #search_keyword 들어오고

    # 검색된 기업의 corp_codes를 리스트로 만듦
    corp_codes = list(df_searched['corp_code'])

    # dart api 사용 준비
    api = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.xml'
    crtfc_key = api_key

    # dart api에 재무정보 요청 (금융업 제외)
    responses = []
    for corp_code in corp_codes:
        response = requests.get(api, params={'crtfc_key': crtfc_key,  
                                            'corp_code': corp_code,
                                            'bsns_year': '2022',
                                            'reprt_code': '11011'})
        responses.append(response)

    # 재무정보가 담길 데이터프레임 생성 -> df_financials
    df_financials = pd.DataFrame()

    # dart api에서 받은 responses를 돌면서 df_financials에 행 추가
    for response in responses:
        # response에서 데이터 파싱
        data = xmltodict.parse(response.text)
        data = data.get('result').get('list')
        
        # 파싱 데이터 -> df_data로 변환
        df_data = pd.DataFrame(data)

        # 필요한 칼럼만 선택
        df_data = df_data[['stock_code', 'fs_div', 'account_nm', 'thstrm_amount']]
        df_data['thstrm_amount'] = df_data['thstrm_amount'].str.replace(',','').astype(int) # Y2022
            
        if 'CFS' in df_data['fs_div'].values:
            df_temp = df_data.loc[df_data['fs_div'] == 'CFS']
        else:
            df_temp = df_data.loc[df_data['fs_div'] == 'OFS']
        
        bv = df_temp.loc[df_temp['account_nm'] == '자본총계'].iloc[0,3]
        rv = df_temp.loc[df_temp['account_nm'] == '매출액'].iloc[0,3]
        try:    
            op = df_temp.loc[df_temp['account_nm'] == '영업이익'].iloc[0,3]
        except:
            op = 0
        ni = df_temp.loc[df_temp['account_nm'] == '당기순이익'].iloc[0,3]

        doc = {
            'stock_code': df_data['stock_code'].iloc[0],
            'book_value': bv,
            'revenue': rv,
            'operating_income': op,
            'net_income': ni,
        }

        df_financials = pd.concat([df_financials, pd.DataFrame(doc, index=[0])], ignore_index=True)

        df_result = pd.merge(df_searched, df_financials, on='stock_code')
        # 각종 멀티플 계산해서 열 추가
        df_result['PBR'] = df_result['market_cap'] / df_result['book_value']
        df_result['PSR'] = df_result['market_cap'] / df_result['revenue']
        df_result['POPR'] = df_result['market_cap'] / df_result['operating_income']
        df_result['PER'] = df_result['market_cap'] / df_result['net_income']

    searched_corps = df_result.to_dict('records')

    return jsonify({'searched_corps': searched_corps})

if __name__ == '__main__':
    app.run(port=5001, debug=True)