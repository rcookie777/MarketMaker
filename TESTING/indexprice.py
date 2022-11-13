
from dtypes import ExchangeState

class IndexPriceCalc(object):
    def __init__(self) -> None:
        self.is_done = False
        self.price = None
    def is_ready(self):
        return self.is_done
    def get_price(self):
        return self.price
    def update_price(self, exchange_state: ExchangeState):
        try:
            self.price = exchange_state.index_values[exchange_state.index_symbol]
            print(self.price)
        except:
            self.price = None
            self.is_done = False