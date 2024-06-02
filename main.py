import pandas as pd
import yfinance as yf
from datetime import datetime
import altair as alt
import streamlit as st

st.title('米国株価可視化アプリ')
st.sidebar.write("""
# GAFA株価
こちらは株価可視化ツールです。以下のオプションから表示日数を指定してください。
""")

st.sidebar.write("""
##表示日数選択
""")
days = st.sidebar.slider('日数', 1, 50, 20)

st.write(f"""
### 過去**{days}日間**のGAFA株価
こちらは株価可視化ツールです。以下のオプションから表示日数を指定してください。
""")

@st.cache
def get_stock_close_data(ticker_symbol, days, new_column_name='Close', lookback_increment=30):
    """
    指定されたティッカーシンボルと営業日数に基づいて、'Close'カラムのみを取得する関数。
    データが存在しない場合は、さかのぼってデータを取得する。

    Parameters:
    ticker_symbol (str): ティッカーシンボル。
    days (int): 取得する営業日数。
    new_column_name (str): 新しいカラム名。
    lookback_increment (int): さかのぼる増分日数。

    Returns:
    pd.DataFrame: 取得したデータフレーム。
    """
    # Ticker symbol
    ticker = yf.Ticker(ticker_symbol)

    # 今日の日付
    end_date = datetime.today().date()
    
    # 初期の開始日
    start_date = (pd.Timestamp(end_date) - pd.tseries.offsets.BDay(days + lookback_increment)).date()

    # データの取得
    while True:
        try:
            data = ticker.history(start=start_date, end=end_date)
            
            if not data.empty:
                break
            
            # データが空の場合はさらにさかのぼる
            start_date = (pd.Timestamp(start_date) - pd.tseries.offsets.BDay(lookback_increment)).date()
        
        except Exception as e:
            print(f"Failed to get ticker '{ticker_symbol}' reason: {e}")
            return None

    # 必要な営業日数分のデータのみを取得
    data = data.tail(days)

    # 'Close'カラムのみを取得
    data = data[['Close']]

    # カラム名を変更
    data.columns = [new_column_name]

    # 日付フォーマットを変更
    data.index = data.index.strftime('%d %B %Y')

    return data

try:
    st.sidebar.write("""
    ## 株価の範囲指定
    """)
    ymin, ymax= st.sidebar.slider('範囲を指定してください。',0.0, 3500.0, (0.0,3500.0))

    tickers = {
        'apple': 'AAPL',
        'meta': 'META',
        'google': 'GOOGL',
        'microsoft': 'MSFT',
        'netflix': 'NFLX',
        'amazon': 'AMZN'
    }

    df = pd.DataFrame()
    for company in tickers:
        # 関数の使用例
        hist = get_stock_close_data(tickers[company], days, new_column_name=company)
        if hist is not None:
            hist = hist.T
            hist.index.name = 'Name'
            df = pd.concat([df, hist])

    companies = st.multiselect('会社名を選択してください。',
                list(df.index), 
                ['google','amazon','meta','apple']
    )

    if not companies:
        st.error('少なくとも一社は選んでください。')
    else:
        data = df.loc[companies]
        st.write('### 株価（USD）',data.sort_index())

        data = data.T.reset_index()
        data = pd.melt(data, id_vars=['Date']).rename(
            columns = {'value':'Stock Prices (USD)'}
            )

        chart = (
            alt.Chart(data)
            .mark_line(opacity=0.8, clip=True)
            .encode(
                x='Date:T',
                y=alt.Y('Stock Prices (USD):Q',stack=None, scale=alt.Scale(domain=[ymin,ymax])),
                color='Name:N'
            )
        )
        st.altair_chart(chart,use_container_width=True)
except:
    st.error("""
             'おっと！何かエラーが起きているようです。'
             """)
