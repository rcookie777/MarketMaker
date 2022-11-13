from utils.orderbook import Orderbook


class ExchangeState:
    def __init__(self, exchange):
        self.exchange = exchange
        self.balances = {}
        self.positions = {}
        self.open_orders = {}
        self.orderbooks = {}
        self.mark_prices = {}
        self.price_tickers = {}
        self.is_authenticated = False

    def to_dict(self):
        return {
            'positions': self.positions,
            'open_orders': self.open_orders,
            'balances': self.balances,
            'mark_prices': self.mark_prices,
            'price_tickers': self.price_tickers,
            'orderbooks': self.orderbooks,
            'is_authenticated': self.is_authenticated,
        }



    def get_open_orders(self, market):
        # this is way to slow, it will be important to track open orders but
        # must solve a different way, maybe only check every once in while?
        # or since we track the best bid and ask, we should now when an order
        # would come near getting filled, so check then? Or just have more
        # leeway in allowing multiple orders to be placed? like check every
        # once and a while and as longs as there's not more than 3 orders on
        # each side or something? or run another thread that just constantly
        # checks but doesn't block? Idk

        # or maybe FTX's REST API is way faster and we could use that?
        # let's try this, maybe ccxt is just slower, idk

        # actually maybe we will get messages through the websocket about
        # changes to our orders, that would be best as not have to wait for a
        # round trip. Should see if the "orders" message channel will have the
        # info we want, this would solve our problem
        self.open_orders[market] = self.exchange.fetchOpenOrders(symbol=market)



    '''
    def update_orderbook(self, market):
        if market not in self.orderbooks:
            self.orderbooks[market] = Orderbook(market)
        self.orderbooks[market].update(
            self.get_orderbook(market=market))
        # TODO add time stamp from message




    def generate_orders(self, market):
        # check position and open orders

        # if there is no open order, generate an order (perhaps initial
        # strategy will just try and maintain 1 order on each side)
        open_order_by_side = {'buy': [], 'sell': []}
        new_orders = []

        for side in sides:
            open_order_by_side[side] = [order for order in self.open_orders if
                                        order['side'] == side]
            if len(open_order_by_side[side]) == 0:
                # create new order, not tested and probably not correct yet,
                # just an outline
                new_order = Order(
                    market,
                    side,
                    'limit-order'
                    amount=self.estimators[market].LO_estimates['bids' if side == 'buy' else 'asks'][0],
                ) # TODO need to finish this

        return new_orders

    def execute_orders(self, new_orders):
        for order in new_orders:
            # execute the order, needs to be completed
            self.exchange.createOrder()     # TODO create order for each
    '''
