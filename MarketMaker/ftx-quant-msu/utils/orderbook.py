import numpy as np

from time import time
class Orderbook:
    def __init__(self, market, orderbook_levels=25):
        self.market = market
        self.orderbook_levels = orderbook_levels
        self.bids = np.zeros((orderbook_levels, 2))
        self.asks = np.zeros((orderbook_levels, 2))
        self.mid_price = None

    def update(self, bids_and_asks):
        # print(f"Orderbook bids and asks {bids_and_asks}")
        # print(f"Bids {bids_and_asks['bids']}")
        start_time = time()
        for ii in range(self.orderbook_levels):
            self.bids[ii, :] = bids_and_asks['bids'][ii]
            self.asks[ii, :] = bids_and_asks['asks'][ii]
        self.mid_price = (self.bids[0, 0] + self.asks[0, 0]) / 2.
        # print(f"Bid {self.bids[0,0]} /  Ask {self.asks[0,0]} = {self.mid_price}")
        # print(f"Got midprice {self.mid_price} in {time() - start_time} seconds")

class Order:
    def __init__(self, market, order_type, side, amount, price):
        self.market = market
        self.order_type = order_type
        self.side = side
        self.amount = amount
        self.price = price

        # TODO probably more stuff we want here, not sure
