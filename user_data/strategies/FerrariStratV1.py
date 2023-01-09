from pandas import DataFrame
import pandas_ta as pta

from freqtrade.strategy import (
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IStrategy,
    IntParameter,
)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This class is a sample. Feel free to customize it.
class FerrariStratV1(IStrategy):
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {"60": 0.01, "30": 0.02, "0": 0.04}

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.99

    # Trailing stoploss
    trailing_stop = False
    trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.025  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = "5m"

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Hyperoptable parameters
    st_candles = IntParameter(3, 50, default=10, space="buy")  # Wie viele Candles
    st_multipl = DecimalParameter(0.1, 10.0, default=3.0, space="buy")  # Multiplikator

    macd_fast = IntParameter(4, 35, default=12, space="buy")  # Schnelle Periode
    macd_slow = IntParameter(5, 50, default=26, space="buy")  # Langsame Periode
    macd_sign = IntParameter(3, 20, default=9, space="buy")  # Signal Smoothing (Signal)

    macd_buy = DecimalParameter(
        0.1, 20.0, default=1.2, space="buy"
    )  # Wie hoch macd um buy

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    def leverage(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag,
        side: str,
        **kwargs,
    ) -> float:
        return 5

    def populate_indicators(s, dataframe: DataFrame, metadata: dict) -> DataFrame:
        st = pta.supertrend(
            dataframe["high"],
            dataframe["low"],
            dataframe["close"],
            length=s.st_candles.value,
            multiplier=s.st_multipl.value,
        )
        st_suffix = f"_{s.st_candles.value}_{s.st_multipl.value}"
        dataframe["st"] = st["SUPERT" + st_suffix]
        dataframe["st_d"] = st[
            "SUPERTd" + st_suffix
        ]  # supertrend direction (1 oder -1)
        dataframe["st_s"] = st["SUPERTs" + st_suffix]
        dataframe["st_l"] = st["SUPERTl" + st_suffix]

        macd = pta.macd(
            dataframe["close"], s.macd_fast.value, s.macd_slow.value, s.macd_sign.value
        )
        macd_suffix = f"_{s.macd_fast.value}_{s.macd_slow.value}_{s.macd_sign.value}"
        dataframe["macd"] = macd[
            "MACD" + macd_suffix
        ]  # macd signal difference (relevant)
        dataframe["macd_h"] = macd["MACDh" + macd_suffix]  # macd value
        dataframe["macd_s"] = macd["MACDs" + macd_suffix]  # signal value
        return dataframe

    def populate_entry_trend(s, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # dataframe.loc[(True), 'enter_long'] = 0
        # dataframe.loc[
        #    (
        #        (qtpylib.crossed_above(dataframe['ema5'], dataframe['ema15']))
        #    ),
        #    'enter_long'] = 1
        dataframe.loc[
            (
                (dataframe["st_d"] == 1)
                & (dataframe["st_d"].shift() == -1)
                & (dataframe["macd"] >= s.macd_buy.value)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "st_macd")
        return dataframe

    def populate_exit_trend(s, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # dataframe.loc[
        #    (
        #        (qtpylib.crossed_below(dataframe['ema5'], dataframe['ema15'])) |
        #        (dataframe['ema5'].values[-1] < dataframe['ema5'].values[-2])
        #    ),
        #    'exit_long'] = 1
        dataframe.loc[
            (
                (dataframe["st_d"] == -1)
                | (dataframe["macd"] < 0)  # &
                # (dataframe['supertrend_direction'].shift() == 1)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "st_macd_change")
        return dataframe
