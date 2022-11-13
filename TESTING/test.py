
import websocket
import json 
import time
import threading

class WebsocketManager():
    _ENDPOINT = 'wss://ftx.us/ws/'

    def __init__(self) -> None:
        self.ws = None
    
    def _get_url(self):
        return self._ENDPOINT

    def _on_message(self,ws,message):
        msg = json.loads(message)
        print("Message received")
        print(msg)
    
    def on_error(self, ws, error):
        print(error)
    
    def on_close(self, ws, close_msg):
        print("Connection close")

    def on_open(self,ws):
        print("Connected")

    def _connect(self):
        print("Connecting")
        self.ws = websocket.WebSocketApp(self._get_url(),
                                    on_message=self._on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        self.ws.on_open = self.on_open
        wst = threading.Thread(target=self.ws.run_forever)
        wst.start()

    def connect(self):
        if self.ws:
            print("Already connected")
            return
        else:
            self._connect()

    def send_json(self, data):
        self.send(json.dumps(data))

    def send(self, data):
        self.connect()
        self.ws.send(data)

    def sub_orderbook(self,market):
        print("Subscribing to orderbook")
        self.send_json({
            "op": "subscribe",
            "channel": "orderbook",
            "market": market
        })

    def sub_ticker(self,market):
        print("Subscribing to ticker")
        self.send_json({
            "op": "subscribe",
            "channel": "ticker",
            "market": market
        })

    def fetch_orderbook(self,market):
        print("Fetching orderbook")
        self.send_json({
            "op": "subscribed",
            "channel": "orderbook",
            "market": market
        })
    def fetch_ticker(self,market):
        print("Fetching ticker")
        self.send_json({
            "op": "subscribed",
            "channel": "ticker",
            "market": market
        })
if __name__ == '__main__':
    ws = WebsocketManager()
    print(ws._get_url())
    ws.connect()
    time.sleep(5)
    ws.sub_orderbook("BTC/USD")
    ws.sub_ticker("BTC/USD")


    