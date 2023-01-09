from freqtrade.strategy import IntParameter, IStrategy, DecimalParameter
from pandas import DataFrame
import pandas_ta as pta
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class LiamStrat(IStrategy):
    INTERFACE_VERSION: int = 3

    # ROI table:
    minimal_roi = {
        "10": 100
    }

    # Stoploss:
    stoploss = -0.1
    
    #use_exit_signal = False
    
    trailing_stop = True

    # Optimal timeframe
    timeframe = '15m'

    startup_candle_count: int = 16
    
    
    st_candles = IntParameter(3, 50, default=10, space="buy") # Wie viele Candles
    st_multipl = DecimalParameter(0.1, 10.0, default=3.0, space="buy") # Multiplikator
    
    macd_fast = IntParameter(4, 35, default=12, space="buy") # Schnelle Periode
    macd_slow = IntParameter(5, 50, default=26, space="buy") # Langsame Periode
    macd_sign = IntParameter(3, 20, default=9, space="buy") # Signal Smoothing (Signal)
    
    macd_buy = DecimalParameter(0.1, 20.0, default=1.2, space="buy") # Wie hoch macd um buy
    

    def populate_indicators(s, dataframe: DataFrame, metadata: dict) -> DataFrame:
        st = pta.supertrend(dataframe['high'], dataframe['low'], dataframe['close'], length=s.st_candles.value, multiplier=s.st_multipl.value)
        st_suffix = f"_{s.st_candles.value}_{s.st_multipl.value}"
        dataframe['st'] = st['SUPERT' + st_suffix]
        dataframe['st_d'] = st['SUPERTd' + st_suffix]
        dataframe['st_s'] = st['SUPERTs' + st_suffix]
        dataframe['st_l'] = st['SUPERTl' + st_suffix]

        macd = pta.macd(dataframe['close'], s.macd_fast.value, s.macd_slow.value, s.macd_sign.value)
        macd_suffix = f"_{s.macd_fast.value}_{s.macd_slow.value}_{s.macd_sign.value}"
        dataframe['macd'] = macd['MACD' + macd_suffix]    # macd signal difference (relevant)
        dataframe['macd_h'] = macd['MACDh' + macd_suffix] # macd value
        dataframe['macd_s'] = macd['MACDs' + macd_suffix] # signal value
        return dataframe

    def populate_entry_trend(s, dataframe: DataFrame, metadata: dict) -> DataFrame:
        #dataframe.loc[(True), 'enter_long'] = 0
        #dataframe.loc[
        #    (
        #        (qtpylib.crossed_above(dataframe['ema5'], dataframe['ema15']))
        #    ),
        #    'enter_long'] = 1
        dataframe.loc[(
                (dataframe['st_d'] == 1) &
                (dataframe['st_d'].shift() == -1) &
                (dataframe['macd'] >= s.macd_buy.value)
            ), ['enter_long', 'enter_tag']] = (1, 'st_macd')
        return dataframe

    def populate_exit_trend(s, dataframe: DataFrame, metadata: dict) -> DataFrame:
        #dataframe.loc[
        #    (
        #        (qtpylib.crossed_below(dataframe['ema5'], dataframe['ema15'])) |
        #        (dataframe['ema5'].values[-1] < dataframe['ema5'].values[-2])
        #    ),
        #    'exit_long'] = 1
        dataframe.loc[(
                (dataframe['st_d'] == -1) | #&
                (dataframe['macd'] < 0)
                #(dataframe['supertrend_direction'].shift() == 1)
            ), ['exit_long', 'exit_tag']] = (1, 'st_macd_change')
        return dataframe
