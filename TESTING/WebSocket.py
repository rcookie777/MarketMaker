import websocket
import json
import time
import hmac




class WebsocketManager:
    _ENDPOINT = 'wss://ftx.us/ws/'

    def __init__(self) -> None:
        self.ws = None
        self.api_key = 'wnlJ4SB2RmU3hqoLlqdU8KU-k6lF1JutERFDP8of'  # TODO: Place your API key here
        self.private_key = 'FoI3rhWXxCoFwlU9vnuXmet2hMnNTqLeglMo3uGd'  # TODO: Place your API secret here
    
    def _get_url(self) -> str:
        return self._ENDPOINT
    
    def on_open(ws):
        data = json.dumps({"op": "subscribe",
                        "channel": "ticker",
                        "market": "BTC/USD"})
        ws.send(data)
        print("Connected")

    
    def on_message(ws, message):
        print(message)


    def on_error(ws, error):
        print(f"Error: {error}")
        

    def on_close(ws, close_msg):
        print(f"Connection close")

    def _login(self) -> None:
        ts = int(time.time() * 1000)
        self.send_json({'op': 'login', 'args': {
            'key': self.api_key,
            'sign': hmac.new(
                self.private_key.encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
            'time': ts,
        }})
        self._logged_in = True

    def send(self, data) -> None:
        self._connect()
        self.ws.send(data)
    
    def send_json(self, data) -> None:
        self.send(json.dumps(data))

    def _connect(self):
        self.ws = websocket.WebSocketApp(self._get_url(),
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        self.ws.run_forever()

    def _wrap_callback(self, f):
        def wrapped_f(ws, *args, **kwargs):
            if ws is self.ws:
                try:
                    f(ws, *args, **kwargs)
                except Exception as e:
                    raise Exception(f'Error running websocket callback: {e}')
        return wrapped_f

    def connect(self):
        pass


if __name__ == "__main__":
    ws = WebsocketManager()
    ws._connect()
    print("Done")

        