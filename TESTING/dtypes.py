
class ExchangeState(object):
    def __init__(self):
        self.positions = {}
        self.open_orders = {}
        self.balances = {}
        self.mark_prices = {}
        self.index_values = {}
        self.tradable_symbols = {}
        self.price_tickers = {}
        self.orderbooks = {}
        self.is_authenticated = False
        self.symbol = None
        self.index_symbol = None
    def to_dict(self):
        return {
            'positions': self.positions,
            'open_orders': self.open_orders,
            'balances': self.balances,
            'mark_prices': self.mark_prices,
            'index_values': self.index_values,
            'tradable_symbols': self.tradable_symbols,
            'price_tickers': self.price_tickers,
            'orderbooks': self.orderbooks,
            'is_authenticated': self.is_authenticated,
            'symbol': self.symbol,
            'index_symbol': self.index_symbol
        } 


