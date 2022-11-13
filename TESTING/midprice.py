from dtypes import ExchangeState

class MidPriceCalc(object):
    def __init__(self) -> None:
        self.is_done = False
        self.price = None
    def is_ready(self):
        return self.is_done
    def get_price(self):
        return self.price
    def update_price(self, exchange_state: ExchangeState):
        try:
            if exchange_state and exchange_state.orderbooks:
                orderbook = exchange_state.orderbooks[exchange_state.symbol]
                self.price = (orderbook['bid'][0]['price'] + orderbook['ask'][0]['price']) / 2
                self.is_done = True
        except Exception as e:
            self.is_done = False