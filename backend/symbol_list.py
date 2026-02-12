"""
Indian Stock Symbol List Manager
Supports NSE, BSE, and major indices
"""

class StockSymbols:
    
    # NIFTY 50 Stocks (NSE)
    NIFTY_50 = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
        'BAJFINANCE.NS', 'LT.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'MARUTI.NS',
        'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'WIPRO.NS',
        'HCLTECH.NS', 'TATAMOTORS.NS', 'BAJAJFINSV.NS', 'POWERGRID.NS', 'NTPC.NS',
        'ONGC.NS', 'M&M.NS', 'TECHM.NS', 'TATASTEEL.NS', 'ADANIENT.NS',
        'COALINDIA.NS', 'JSWSTEEL.NS', 'INDUSINDBK.NS', 'GRASIM.NS', 'BRITANNIA.NS',
        'APOLLOHOSP.NS', 'EICHERMOT.NS', 'DRREDDY.NS', 'CIPLA.NS', 'ADANIPORTS.NS',
        'DIVISLAB.NS', 'BPCL.NS', 'HINDALCO.NS', 'HEROMOTOCO.NS', 'TATACONSUM.NS',
        'SBILIFE.NS', 'BAJAJ-AUTO.NS', 'UPL.NS', 'HDFCLIFE.NS', 'LTIM.NS'
    ]
    
    # BANK NIFTY Stocks
    BANK_NIFTY = [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
        'INDUSINDBK.NS', 'AUBANK.NS', 'BANDHANBNK.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS',
        'PNB.NS', 'BANKBARODA.NS'
    ]
    
    # Popular NSE Stocks
    POPULAR_NSE = [
        'ADANIGREEN.NS', 'ADANIPOWER.NS', 'AMBUJACEM.NS', 'ACC.NS', 'DABUR.NS',
        'GODREJCP.NS', 'GAIL.NS', 'HAVELLS.NS', 'ICICIGI.NS', 'ICICIPRULI.NS',
        'INDIGO.NS', 'JUBLFOOD.NS', 'LUPIN.NS', 'MARICO.NS', 'MCDOWELL-N.NS',
        'NAUKRI.NS', 'NMDC.NS', 'PAGEIND.NS', 'PIDILITIND.NS', 'PIIND.NS',
        'PVR.NS', 'SIEMENS.NS', 'TRENT.NS', 'VEDL.NS', 'ZEEL.NS',
        'ZOMATO.NS', 'PAYTM.NS', 'IRCTC.NS', 'DMART.NS', 'POLICYBZR.NS'
    ]
    
    # Indices
    INDICES = {
        'NIFTY 50': '^NSEI',
        'BANK NIFTY': '^NSEBANK',
        'NIFTY IT': '^CNXIT',
        'NIFTY AUTO': '^CNXAUTO',
        'NIFTY PHARMA': '^CNXPHARMA',
        'NIFTY FMCG': '^CNXFMCG',
        'NIFTY MIDCAP': '^NSEMDCP50',
        'BSE SENSEX': '^BSESN'
    }
    
    @staticmethod
    def get_all_nse_symbols():
        """Get all NSE symbols"""
        return list(set(StockSymbols.NIFTY_50 + StockSymbols.BANK_NIFTY + StockSymbols.POPULAR_NSE))
    
    @staticmethod
    def search_symbol(query):
        """Search for a stock symbol by ticker or company name"""
        query = query.upper().strip()
        if not query:
            return []

        all_symbols = StockSymbols.get_all_nse_symbols()
        compact_query = query.replace(' ', '').replace('-', '')

        ranked_results = []
        seen = set()

        def add_result(symbol, name, exchange, score):
            key = (symbol, exchange)
            if key in seen or score <= 0:
                return
            seen.add(key)
            ranked_results.append({
                'score': score,
                'symbol': symbol,
                'name': name,
                'exchange': exchange
            })

        for symbol in all_symbols:
            base_name = symbol.replace('.NS', '').replace('.BO', '')
            company_name = STOCK_NAMES.get(symbol, base_name)

            symbol_upper = symbol.upper()
            base_upper = base_name.upper()
            company_upper = company_name.upper()
            base_compact = base_upper.replace(' ', '').replace('-', '')
            company_compact = company_upper.replace(' ', '').replace('-', '')

            score = 0
            if symbol_upper.startswith(query) or base_upper.startswith(query):
                score += 5
            if query in symbol_upper or query in base_upper:
                score += 3
            if query in company_upper:
                score += 2
            if compact_query and (compact_query in base_compact or compact_query in company_compact):
                score += 1

            add_result(
                symbol=symbol,
                name=company_name,
                exchange='NSE' if '.NS' in symbol else 'BSE',
                score=score
            )

        for index_name, index_symbol in StockSymbols.INDICES.items():
            index_name_upper = index_name.upper()
            index_compact = index_name_upper.replace(' ', '').replace('-', '')

            score = 0
            if index_name_upper.startswith(query):
                score += 5
            if query in index_name_upper:
                score += 3
            if compact_query and compact_query in index_compact:
                score += 1

            add_result(
                symbol=index_symbol,
                name=index_name,
                exchange='INDEX',
                score=score
            )

        ranked_results.sort(key=lambda item: item['score'], reverse=True)

        return [
            {
                'symbol': item['symbol'],
                'name': item['name'],
                'exchange': item['exchange']
            }
            for item in ranked_results[:10]
        ]
    
    @staticmethod
    def format_symbol(symbol):
        """Format symbol for Yahoo Finance"""
        symbol = symbol.upper().strip()
        
        # If already formatted
        if '.NS' in symbol or '.BO' in symbol or symbol.startswith('^'):
            return symbol
        
        # Default to NSE
        return f"{symbol}.NS"
    
    @staticmethod
    def validate_symbol(symbol):
        """Validate if symbol exists"""
        all_symbols = StockSymbols.get_all_nse_symbols()
        indices = list(StockSymbols.INDICES.values())
        
        return symbol in all_symbols or symbol in indices


# Popular stock names mapping
STOCK_NAMES = {
    'RELIANCE.NS': 'Reliance Industries Ltd',
    'TCS.NS': 'Tata Consultancy Services Ltd',
    'HDFCBANK.NS': 'HDFC Bank Ltd',
    'INFY.NS': 'Infosys Ltd',
    'ICICIBANK.NS': 'ICICI Bank Ltd',
    'HINDUNILVR.NS': 'Hindustan Unilever Ltd',
    'ITC.NS': 'ITC Ltd',
    'SBIN.NS': 'State Bank of India',
    'BHARTIARTL.NS': 'Bharti Airtel Ltd',
    'KOTAKBANK.NS': 'Kotak Mahindra Bank Ltd',
    'BAJFINANCE.NS': 'Bajaj Finance Ltd',
    'LT.NS': 'Larsen & Toubro Ltd',
    'ASIANPAINT.NS': 'Asian Paints Ltd',
    'AXISBANK.NS': 'Axis Bank Ltd',
    'MARUTI.NS': 'Maruti Suzuki India Ltd',
    'TATAMOTORS.NS': 'Tata Motors Ltd',
    'ADANIGREEN.NS': 'Adani Green Energy Ltd',
    'ADANIPORTS.NS': 'Adani Ports and SEZ Ltd',
    'ZOMATO.NS': 'Zomato Ltd',
    'PAYTM.NS': 'Paytm (One97 Communications Ltd)',
    'IRCTC.NS': 'Indian Railway Catering & Tourism Corp Ltd',
}


def get_stock_name(symbol):
    """Get human-readable stock name"""
    return STOCK_NAMES.get(symbol, symbol.replace('.NS', '').replace('.BO', ''))

