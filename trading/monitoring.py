import pandas as pd
import pandas_ta as ta
import os

from binance import ThreadedWebsocketManager
from binance.client import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv

from bot.messages import send_message_to_telegram

load_dotenv()

api_key = os.environ["API_KEY_BINANCE"]
secret_key = os.environ["SECRET_KEY_BINANCE"]

client = Client(api_key=api_key,
                api_secret=secret_key,
                tld="com",
                testnet=True)


class MonitoringPrice:
    """
    A class for monitoring price movements and generating signals based on a simple trading strategy.

    Parameters:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').
    - timeframe (str): The timeframe for price data (e.g., '1h', '4h').
    - position (int): Initial trading position (0 for neutral, 1 for long, -1 for short).

    Methods:
    - start_monitoring(historical_days: int) -> None:
        Initiates the monitoring process by starting a threaded websocket connection for real-time price updates.

    - get_most_recent(days: int) -> None:
        Fetches historical price data for the specified number of days.

    - stream_candles(msg) -> None:
        Callback function to process and update real-time price data.

    - define_strategy() -> None:
        Applies a simple trading strategy based on Bollinger Bands to generate buy and sell signals.

    - execute_messages() -> None:
        Executes actions based on the generated signals, such as sending messages to a Telegram group.

    Attributes:
    - symbol (str): The trading pair symbol.
    - timeframe (str): The timeframe for price data.
    - available_intervals (list): List of available timeframe intervals.
    - position (int): Current trading position.
    - twm (ThreadedWebsocketManager): Binance ThreadedWebsocketManager instance.
    - data (pd.DataFrame): Historical price data.
    - prepared_data (pd.DataFrame): Processed data with signals.

    Example:
    ```
    monitor = MonitoringPrice(symbol='BTCUSDT', timeframe='1h', position=0)
    monitor.start_monitoring(historical_days=7)
    ```
    """

    def __init__(self, symbol: str, timeframe: str, position: int = 0) -> None:
        self.symbol = symbol
        self.timeframe = timeframe

        self.available_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']

        self.position = position
        self.twm = None
        self.data = None
        self.prepared_data = None

    def start_monitoring(self, historical_days: int) -> None:
        """
        Initiates the monitoring process by starting a threaded websocket connection for real-time price updates.

        Parameters:
        - historical_days (int): Number of days of historical data to fetch initially.
        """
        self.twm = ThreadedWebsocketManager()
        self.twm.start()

        if self.timeframe in self.available_intervals:
            self.get_most_recent(days=historical_days)

            self.twm.start_kline_socket(callback=self.stream_candles,
                                        symbol=self.symbol,
                                        interval=self.timeframe)

            self.twm.join()

    def get_most_recent(self, days: int) -> None:
        """
        Fetches historical price data for the specified number of days.

        Parameters:
        - days (int): Number of days of historical data to fetch.
        """
        now = datetime.utcnow()
        past = str(now - timedelta(days=days))

        bars = client.get_historical_klines(symbol=self.symbol,
                                            interval=self.timeframe,
                                            start_str=past,
                                            limit=1000)

        df = pd.DataFrame(bars)

        df['Date'] = pd.to_datetime(df.iloc[:, 0], unit="ms")

        df.columns = ['Open time', 'Open', 'High', 'Low', 'Close', 'Volume',
                      'Close time', 'Quote asset volume', 'Number of trades',
                      'Taker buy base asset volume', 'Taker buy quote asset volume',
                      'Ignore', 'Date']

        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()

        df.set_index('Date', inplace=True)

        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors='coerce')

        df['Complete'] = [True for _ in range(len(df) - 1)] + [False]

        self.data = df

    def stream_candles(self, msg) -> None:
        """
        Callback function to process and update real-time price data.

        Parameters:
        - msg (dict): Real-time price data received through the websocket.
        """
        event_time = pd.to_datetime(msg['E'], unit='ms')
        start_time = pd.to_datetime(msg['k']['t'], unit='ms')
        first = float(msg['k']['o'])
        high = float(msg['k']['h'])
        low = float(msg['k']['l'])
        close = float(msg['k']['c'])
        volume = float(msg['k']['v'])
        complete = msg['k']['x']

        print(".", end="", flush=True)

        self.data.loc[start_time] = [first, high, low, close, volume, complete]

        if complete:
            self.define_strategy()
            self.execute_messages()

    def define_strategy(self) -> None:
        """
        Applies a simple trading strategy based on Bollinger Bands to generate buy and sell signals.
        """
        df = self.data.copy()

        df['sma'] = ta.ema(df['Close'], length=20)
        df['std'] = ta.stdev(df['Close'], length=20)
        df['upper_band'] = df['sma'] + 2.5 * df['std']
        df['lower_band'] = df['sma'] - 2.5 * df['std']

        buy_condition = df['Close'] <= df['lower_band']
        sell_condition = df['Close'] >= df['upper_band']

        df['position'] = 0
        df.loc[buy_condition, 'position'] = 1
        df.loc[sell_condition, 'position'] = -1

        self.prepared_data = df.copy()

    def execute_messages(self) -> None:
        """
        Executes actions based on the generated signals, such as sending messages to a Telegram group.
        """
        try:
            last_row = self.prepared_data.iloc[-1]

            if last_row['position'] == 1 and self.position == 0:
                self.position = 1
                print(f"Um sinal de compra para {self.symbol} foi gerado!")
                send_message_to_telegram(f"Um sinal de compra para {self.symbol} foi gerado!")

            elif last_row['position'] == -1 and self.position == 1:
                self.position = 0
                print(f"Um sinal de venda para {self.symbol} foi gerado!")
                send_message_to_telegram(f"Um sinal de venda para {self.symbol} foi gerado!")

        except Exception as error:
            print("Error in send message")
            print(error)
            self.twm.stop()
