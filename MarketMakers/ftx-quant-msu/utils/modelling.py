import numpy as np
from scipy.optimize import curve_fit


def normalize_amounts(amounts):
    max_cumulative_amount = amounts.cumsum().max()
    amounts_normalized = amounts.cumsum() / max_cumulative_amount
    # amounts_normalized = (amounts.cumsum() / max_cumulative_amount).to_numpy().astype(float)
    return amounts_normalized, max_cumulative_amount

def normalize_prices(prices):
    lowest_price = prices.min()
    prices_normalized = prices - lowest_price
    # prices_normalized = prices.to_numpy().astype(float) - lowest_price
    return prices_normalized, lowest_price

def exponential(t, m, k, b):
    return m * np.exp(t * k) + b


class ExpLOBEstimate:
    def __init__(self, orderbook_levels, max_iterations=1000, method='trf',
                 loss="soft_l1", f_scale=0.1):
        self.initial_params = {'asks': (2.0, 0.01, 0.),
                               'bids': (2.0, -0.01, 0.)}
        self.params = self.initial_params
        self.orderbook_levels = orderbook_levels
        self.max_iterations = max_iterations
        self.method = method
        self.loss = loss
        self.f_scale = f_scale
        self.normalized_book = {'bids': np.zeros((self.orderbook_levels, 2)),
                                'asks': np.zeros((self.orderbook_levels, 2))}
        self.min_prices = {'bids': None, 'asks': None}
        self.total_amounts = {'bids': None, 'asks': None}

        self.book = None
        self.LO_estimates = {'bids': None, 'asks': None}
        self.estimated_delta_amounts = {'bids': None, 'asks': None}

    '''
    def set_incoming_book(self, book):
        self.book = book
    '''

    def normalize_book(self, side, book):
        self.normalized_book[side][:, 0], self.min_prices[side] = \
            normalize_prices(book[:, 0])
        self.normalized_book[side][:, 1], self.total_amounts[side] = \
            normalize_amounts(book[:, 1])

    def normalize_and_fit_exponential(self, book):
        self.normalize_book('bids', book.bids)
        self.normalize_book('asks', book.asks)

        for side in ['bids', 'asks']:
            self.fit_exponential(side, self.normalized_book[side])

    def fit_exponential(self, side, side_book):
        bounds = {'bids': {'min': [0.0, -0.5, -0.001],
                          'max': [4.0, 0.0, 0.001]},
                  'asks': {'min': [0.0, 0.0, -0.001],
                           'max': [4.0, 0.5, 0.001]}}
        try:
            self.params[side], cv = curve_fit(
                exponential,
                side_book[:self.orderbook_levels, 0],
                side_book[:self.orderbook_levels, 1],
                self.params[side],
                max_nfev=self.max_iterations,
                method=self.method,
                loss=self.loss,
                bounds=(bounds[side]['min'],bounds[side]['max']),
                f_scale=self.f_scale)

        except RuntimeError:
            self.params[side] = self.initial_params[side]
            cv = None

    def get_estimated_LO_depth(self, mid_price):
        self.LO_estimates['asks'] = round(mid_price + (1 / self.params['asks'][1]),
                                          1)
        self.LO_estimates['bids'] = round(mid_price - (-1 / self.params['bids'][1]),
                                          1)

        return self.LO_estimates

    def get_estimated_delta_amoutns(self,LO_estimates):
        pass
        # self.estimated_delta_amounts['bids'] = (self.total_amounts['bids'] * '])
# class OffsetPredictions:
#     def __init__(self,orderbook_levels):
#         self.offsetEstimates = {'bids':None,'asks':None}
#         self.normalized_book = {'bids': np.zeros((self.orderbook_levels, 2)),
#                                 'asks': np.zeros((self.orderbook_levels, 2))}

#     def normalize_book(self, side, book):
#         self.normalized_book[side][:, 0], self.min_prices[side] = \
#             normalize_prices(book[:, 0])
#         self.normalized_book[side][:, 1], self.total_amounts[side] = \
#             normalize_amounts(book[:, 1])



