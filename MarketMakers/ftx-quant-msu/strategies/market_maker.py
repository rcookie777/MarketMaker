import time
import yaml
import json
from scipy.optimize import curve_fit
from utils.modelling import normalize_amounts, normalize_prices
from typing import Dict
from ftx_websocket.client import FtxWebsocketClient
from ftx_rest.rest_client import FtxRestClient
from utils.orderbook import Orderbook, Order
from utils.modelling import ExpLOBEstimate
from utils.exchange_state import ExchangeState
from dateutil import tz
from time import time
# import ccxt

sides = ['buy', 'sell']

class MarketMaker(FtxWebsocketClient):
    def __init__(self, conf, orderbook_levels=25, api_key=None,
                 api_secret=None,_subaccount_name= None):
        super(MarketMaker, self).__init__()
        self._subaccount_name = conf['subaccount']
        self.dry_run = conf['dry_run']
        self.max_half_spread_depth_bps = conf['max_half_spread_depth_bps']
        self.order_size = conf['order_size']
        self.offset = conf['offset_pct']
        self.strat = conf['strat']
        self.relist_tolerance = conf['relist_tolerance']
        self.last_order_time = time()
        self.min_sec_between_orders = conf['min_sec_between_orders']
        self.order_en_route = {'sell': False, 'buy': False}
        self.offset_prices = {'buy':None,
                        'sell':None}
        self.conf = conf

        if (not (api_key == None)) & (not (api_secret == None)):
            self._api_key = api_key
            self._api_secret = api_secret
            self._login()
            self.rest = FtxRestClient(self._api_key, self._api_secret,self._subaccount_name)

        self.exchange_state = ExchangeState("Ftx")

        self.estimators = {}
        self.symbols = ['BTC/USD']

        for symbol in self.symbols:
            self.exchange_state.open_orders[symbol] = {'sell': {},
                                                       'buy': {}}
                                                     
        self.update_state()
        print('balances: ', self.exchange_state.balances)
        # ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BTC/USDT']

    def get_open_orders(self, market):
        return self.exchange_state.get_open_orders(market)

    def _handle_trades_message(self, message: Dict) -> None:
        self._trades[message['market']].append(message['data'])

    def _handle_ticker_message(self, message: Dict) -> None:
        self._tickers[message['market']] = message['data']

    def _handle_fills_message(self, message: Dict) -> None:
        self._fills.append(message['data'])

        # when an order gets filled, adjust our balances accordingly
        data = message['data']
        order_side = data['side']
        order_id = data['orderId']

        if order_side == 'sell':
            self.exchange_state.balances[data['baseCurrency']]['total'] -= data['size']
            self.exchange_state.balances[data['quoteCurrency']]['total'] += \
                (data['size'] * data['price'] - data['fee'])
        elif order_side == 'buy':
            self.exchange_state.balances[data['baseCurrency']]['total'] += data['size']
            self.exchange_state.balances[data['quoteCurrency']]['total'] -= \
                (data['size'] * data['price'] + data['fee'])

    def _handle_orders_message(self, message: Dict) -> None:
        data = message['data']
        self._orders.update({data['id']: data})

        # if we get an order message if it's open, add it, otherwise remove
        order_side = data['side']
       
        if data['status'] in ['new', 'open']:
            self.exchange_state.open_orders[data['market']][order_side][data['id']] = data
            self.order_en_route[order_side] = False
            # print('\norder added: ', self.exchange_state.open_orders[data['market']][order_side])
        elif data['status'] == 'closed':
            # print('\norder closed: ', self.exchange_state.open_orders[data['market']][order_side])
            try:
                # print(f"deleted order {[data['id']]}")
                del self.exchange_state.open_orders[data['market']][order_side][data['id']]
            except:
                print("Cannot remove order, order already gone")
            print('len open_order: ', len(self.exchange_state.open_orders[data['market']][order_side]))

    def message_debug(self, message):
        channel = message['channel']
        if self.conf['debug']['messages']['all']:
            print('message: ', message)
        else:
            for channel_type in ['fills', 'orders', 'orderbook']:
                if (self.conf['debug']['messages'][channel_type] &
                        (channel == channel_type)):
                    print(f'{channel_type} message: ', message)

    def print_current_mid_price(self, message, start_time):

        cur_time = time()

        # to clear with blank spaces
        print(100 * ' ', end="\r")
        print('our bid: {}, mid: {}, our ask: {}, msg_time: {:.3f}, OB delay: {:.3g}'
              .format(self.estimators[message['market']].LO_estimates['bids'],
                      self.exchange_state.orderbooks[message['market']].mid_price,
                      self.estimators[message['market']].LO_estimates['asks'],
                      cur_time - start_time,
                      cur_time - self.get_orderbook_timestamp(message['market'])),
                    #   len(self.exchange_state.open_orders[message['market']]['buy']) + len(self.exchange_state.open_orders[message['market']]['sell']),
              end="\r")

    def _on_message(self, ws, raw_message: str) -> None:
        start_time = time()

        message = json.loads(raw_message)
        message_type = message['type']
        if message_type in {'subscribed', 'unsubscribed'}:
            return
        elif message_type == 'info':
            if message['code'] == 20001:
                return self.reconnect()
        elif message_type == 'error':
            raise Exception(message)

        self.message_debug(message)

        channel = message['channel']
        message_handler_start = time()
        if channel == 'orderbook':
            self._handle_orderbook_message(message)
        elif channel == 'fills':
            self._handle_fills_message(message)
        elif channel == 'orders':
            # print(f"Order Message {message}")
            self._handle_orders_message(message)
        message_handler_time = time() - message_handler_start

        # new code here to get orderbook how we want for estimation, etc
        if channel == 'orderbook':
            update_orderbook_start = time()
            self.update_orderbook(message['market'])
            update_orderbook_time = time() - update_orderbook_start

            # cancel if price has drifted too far
            cancel_start = time()
            self.cancel_open_orders(message['market'])
            cancel_time = time() - cancel_start

            update_predictions_start = time()
            self.update_lo_depth_predictions(message['market'])
            update_predictions_time = time() - update_predictions_start

            self.update_offset_predictions(message['market'])
            # generate orders
            self.generate_orders_start = time()
            if (self.generate_orders_start - self.last_order_time) > self.min_sec_between_orders:
                self.generate_and_place_orders(message['market'])
                self.last_order_time = self.generate_orders_start
            self.generate_orders_time = time() - self.generate_orders_start

            debug_start = time()
            if self.conf['debug']['orderbook']:
                self.print_current_mid_price(message, start_time)
            debug_time = time() - debug_start

            on_message_end = time()
            if self.conf['debug']['message_time']:
                full_message_time = on_message_end-start_time
                print('\n\nTiming.....')
                print('{:<22} {:.5f} {:.1%}'.format('Message handler:',
                                                    message_handler_time,
                                                    message_handler_time / full_message_time))
                print('{:<22} {:.5f} {:.1%}'.format('Update orderbook:',
                                                    update_orderbook_time,
                                                    update_orderbook_time/full_message_time))
                print('{:<22} {:.5f} {:.1%}'.format('Cancel orders:',
                                                    cancel_time,
                                                    cancel_time/full_message_time))
                print('{:<22} {:.5f} {:.1%}'.format('Update predictions:',
                                                    update_predictions_time,
                                                    update_predictions_time/full_message_time))
                print('{:<22} {:.5f} {:.1%}'.format('Generate orders:',
                                                    self.generate_orders_time,
                                                    self.generate_orders_time/full_message_time))
                print('{:<22} {:.5f} {:.1%}'.format('Debug:',
                                                    debug_time,
                                                    debug_time/full_message_time))
                print('{:<22} {:.5f}'.format('On message', full_message_time))

    def cancel_open_orders(self, market):
        sell_orders_outside_tolerance = [order_id for order_id, order_info in
                                         self.exchange_state.open_orders[market]['sell'].items() if
                                         order_info['price'] > self.exchange_state.orderbooks[market].mid_price * (1 + self.relist_tolerance)]
        buy_orders_outside_tolerance = [order_id for order_id, order_info in
                                        self.exchange_state.open_orders[market]['buy'].items() if
                                        order_info['price'] < self.exchange_state.orderbooks[market].mid_price * (1 - self.relist_tolerance)]

        for sell_order_id in sell_orders_outside_tolerance:
            try:
                self.rest.cancel_order(sell_order_id)
                print(f"Canceling Order {sell_order_id}")
                if self.conf['debug']['cancel_order']:
                    print('\ncancelling: ', self.exchange_state.open_orders[market]['sell'][sell_order_id])
                if self.exchange_state.open_orders[market]['sell'][sell_order_id]: 
                    del self.exchange_state.open_orders[market]['sell'][sell_order_id]
                # if self.exchange_state.open_orders[market]['buy']:
                #     self.rest.cancel_order(self.exchange_state.open_orders[market]['buy'].keys()[0])
                #     print(f"Cancelling Buy Order - {self.exchange_state.open_orders[market]['buy'].keys()[0]}")
                # print(self.exchange_state.open_orders[market])
                if ((len(self.exchange_state.open_orders[market]['sell']) < 1) &
                (not self.order_en_route['sell'])) & (self.exchange_state.open_orders[market]['buy'] < 1):
                    self.generate_and_place_orders(market)
                    self.order_en_route['sell'] = True
                    self.order_en_route['buy'] = True
            except:
                print("Order already queued for cancellation")
        for buy_order_id in buy_orders_outside_tolerance:
            try:
                self.rest.cancel_order(buy_order_id)
                print(f"Canceling Order Buy Order - {buy_order_id}")
                if self.conf['debug']['cancel_order']:
                    print('\ncancelling: ', self.exchange_state.open_orders[market]['buy'][buy_order_id])
                if self.exchange_state.open_orders[market]['buy'][buy_order_id]: 
                    del self.exchange_state.open_orders[market]['buy'][buy_order_id]
                # if self.exchange_state.open_orders[market]['sell']:
                #     self.rest.cancel_order(self.exchange_state.open_orders[market]['sell'].keys()[0])
                #     print(f"Cancelling Sell Order - {self.exchange_state.open_orders[market]['sell'].keys()[0]}")
                print(self.exchange_state.open_orders[market])
                if ((len(self.exchange_state.open_orders[market]['buy']) < 1) &
                (not self.order_en_route['sell'])) & (self.exchange_state.open_orders[market]['sell'] < 1):
                    self.generate_and_place_orders(market)
                    self.order_en_route['sell'] = True
                    self.order_en_route['buy'] = True
            except:
                print("Order already queued for cancellation")
        # print(self.exchange_state.open_orders[market])

    def generate_and_place_orders(self, market):
        if ((len(self.exchange_state.open_orders[market]['sell']) < 1) &
            (len(self.exchange_state.open_orders[market]['buy']) < 1) &
            (not self.order_en_route['buy']) & (not self.order_en_route['sell'])):
             if (self.strat == "LOB"):
                    self.generate_orders_start = time()
                    if (self.generate_orders_start - self.last_order_time) > self.min_sec_between_orders:
                        self.place_order(market,
                                    'buy',
                                    self.estimators[market].LO_estimates['bids'],
                                    self.order_size)
                        self.place_order(market,
                                    'sell',
                                    self.estimators[market].LO_estimates['asks'],
                                    self.order_size)
                        self.order_en_route['sell'] = True
                        self.order_en_route['buy'] = True
                        self.last_order_time = self.generate_orders_start
                    self.generate_orders_time = time() - self.generate_orders_start
             if (self.strat == "Offset"):
                    self.place_order(market,
                                    'buy',
                                    self.offset_prices['buy'],
                                    self.order_size)
                    self.place_order(market,
                                    'sell',
                                    self.offset_prices['sell'],
                                    self.order_size)
                    self.order_en_route['sell'] = True
                    self.order_en_route['buy'] = True

    def parse_balances(self, balances):
        for asset_info in balances:
            self.exchange_state.balances[asset_info['coin']] = asset_info

    def parse_open_orders(self, orders):
        print('orders: ', orders)
        for order_info in orders:
            order_id = order_info['id']
            order_side = order_info['side']
            self.exchange_state.open_orders[order_info['market']][order_side][order_id] = order_info

    def update_state(self):
        self.parse_balances(self.rest.get_balances())
        self.parse_open_orders(self.rest.get_open_orders())

    def update_orderbook(self, market):
        if market not in self.exchange_state.orderbooks:
            self.exchange_state.orderbooks[market] = Orderbook(market)
        self.exchange_state.orderbooks[market].update(
            self.get_orderbook(market=market))

    def update_offset_predictions(self,market):

        self.offset_ask = self.exchange_state.orderbooks[market].mid_price * (1 + self.offset)
        self.offset_bid = self.exchange_state.orderbooks[market].mid_price * (1 - self.offset)
        self.offset_prices['buy'] = self.offset_bid
        self.offset_prices['sell'] = self.offset_ask

    def update_lo_depth_predictions(self, market):
        if market not in self.estimators:
            self.estimators[market] = ExpLOBEstimate(
                self.exchange_state.orderbooks[market].orderbook_levels,
                max_iterations=100
            )

        self.estimators[market].normalize_and_fit_exponential(
            self.exchange_state.orderbooks[market])

        self.estimators[market].get_estimated_LO_depth(
            self.exchange_state.orderbooks[market].mid_price)

        if self.estimators[market].LO_estimates['bids'] < (
            self.exchange_state.orderbooks[market].mid_price -
            self.max_half_spread_depth_bps) or (
                self.estimators[market].LO_estimates['bids'] >
                self.exchange_state.orderbooks[market].mid_price):
            self.estimators[market].LO_estimates['bids'] = round(
                self.exchange_state.orderbooks[market].mid_price * (1 - self.max_half_spread_depth_bps), 1)

        if self.estimators[market].LO_estimates['asks'] > (
            self.exchange_state.orderbooks[market].mid_price +
            self.max_half_spread_depth_bps) or (
                self.estimators[market].LO_estimates['asks'] <
                self.exchange_state.orderbooks[market].mid_price):
            self.estimators[market].LO_estimates['asks'] = round(
                self.exchange_state.orderbooks[market].mid_price * (1 + self.max_half_spread_depth_bps), 1)

    def place_order(self, market, side, price, size, order_type='limit'):

        if self.conf['debug']['place_order']:
            print(f'\nPlacing limit order for {size} {side} at {price} on '
                f'{market}')
        if not self.conf['dry_run']:
            self.rest.place_order(market, side, price, size, order_type,
                                  post_only=True)

    def run(self):
        #Run the market making algorithm on each market.
        run_time = time()
        for symbol in self.symbols:
            print(f'Getting orderbook for {symbol}')
            t = time()
            mm.get_orderbook(market=symbol)
            mm.get_orders()
            mm.get_fills()
            print(f"Updated orderbook from websocket in {time() - t} seconds")

if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    with open("api/api_real_keys.yaml") as f:
        api_keys = yaml.load(f, Loader=yaml.FullLoader)
    mm = MarketMaker(config,
                     api_key=api_keys['api_key'],
                     api_secret=api_keys['api_secret'],
                     _subaccount_name=config['subaccount'])
    mm.connect()
    mm.run()
