import yfinance as yf
from fredapi import Fred
import pandas as pd
from config import FRED_API_KEY

fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

def fetch_macro_layer():
    """1. 總體環境 (Macro) + 2. 市場氛圍 (Market Sentiment)"""
    data = {}
    
    # 總經：美元指數 (DXY)
    try:
        dxy = yf.Ticker("DX-Y.NYB").history(period="5d")
        data['dxy'] = dxy['Close'].iloc[-1] if not dxy.empty else 104.5
    except Exception:
        data['dxy'] = 104.5

    # 總經：FRED 數據 (殖利率曲線、基準利率、通膨 CPI)
    if fred:
        try:
            data['yield_spread'] = fred.get_series('T10Y2Y').dropna().iloc[-1]
            data['fed_rate'] = fred.get_series('FEDFUNDS').dropna().iloc[-1]
            cpi_series = fred.get_series('CPIAUCSL').dropna()
            data['cpi_yoy'] = ((cpi_series.iloc[-1] - cpi_series.iloc[-13]) / cpi_series.iloc[-13]) * 100
        except Exception:
            data['yield_spread'], data['fed_rate'], data['cpi_yoy'] = 0.15, 5.25, 3.1
    else:
        data['yield_spread'], data['fed_rate'], data['cpi_yoy'] = 0.15, 5.25, 3.1

    # 市場氛圍：VIX 恐慌指數、S&P500、恆生指數
    for key, ticker in [('vix', '^VIX'), ('sp500', '^GSPC'), ('hsi', '^HSI')]:
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            data[key] = hist['Close'].iloc[-1] if not hist.empty else 0.0
            data[f'{key}_change'] = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100 if len(hist) > 1 else 0.0
        except Exception:
            data[key], data[f'{key}_change'] = 0.0, 0.0

    return data

def fetch_stock_full_profile(ticker_symbol: str, peer_symbols: list = None):
    """3. 產業同業 + 4. 個股基本面 + 5. 技術面歷史 + 6. 分析師與機構籌碼"""
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="1y")
    info = stock.info
    
    # 4 & 6. 基本面與籌碼數據整理
    fundamentals = {
        'pe_trailing': info.get('trailingPE', 'N/A'),
        'pe_forward': info.get('forwardPE', 'N/A'),
        'gross_margin': (info.get('grossMargins', 0) or 0) * 100,
        'operating_margin': (info.get('operatingMargins', 0) or 0) * 100,
        'roe': (info.get('returnOnEquity', 0) or 0) * 100,
        'debt_to_equity': info.get('debtToEquity', 'N/A'),
        'fcf': info.get('freeCashflow', 0),
        'revenue_growth': (info.get('revenueGrowth', 0) or 0) * 100,
        # 籌碼與分析師
        'target_median': info.get('targetMedianPrice', None),
        'target_high': info.get('targetHighPrice', None),
        'target_low': info.get('targetLowPrice', None),
        'recommendation': info.get('recommendationKey', 'N/A'),
        'institution_pct': (info.get('heldPercentInstitutions', 0) or 0) * 100,
        'short_ratio': info.get('shortRatio', 'N/A')
    }

    # 3. 產業同儕數據橫向比較
    peers_data = []
    if peer_symbols:
        for peer in peer_symbols:
            try:
                p_info = yf.Ticker(peer).info
                peers_data.append({
                    "代碼": peer,
                    "歷史本益比 (P/E)": round(p_info.get('trailingPE', 0) or 0, 2),
                    "預估本益比 (F-P/E)": round(p_info.get('forwardPE', 0) or 0, 2),
                    "毛利率 (%)": round((p_info.get('grossMargins', 0) or 0) * 100, 2),
                    "ROE (%)": round((p_info.get('returnOnEquity', 0) or 0) * 100, 2),
                    "營收成長 (%)": round((p_info.get('revenueGrowth', 0) or 0) * 100, 2)
                })
            except Exception:
                continue
    peers_df = pd.DataFrame(peers_data)

    return df, fundamentals, peers_df