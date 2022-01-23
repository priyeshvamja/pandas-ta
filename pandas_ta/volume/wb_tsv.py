# -*- coding: utf-8 -*-
from pandas import DataFrame, Series
from pandas_ta.overlap import ma
from pandas_ta.utils import get_drift, get_offset, verify_series, signed_series, zero


def wb_tsv(close: Series, volume: Series, length: int = None, signal: int = None, mamode: str = None,
           drift: int = None, offset: int = None, **kwargs) -> DataFrame:
    """Time Segmented Value (TSV)

    TSV is a proprietary technical indicator developed by Worden Brothers Inc.,
    classified as an oscillator. It compares various time segments of both price
    and volume. It measures the amount money flowing at various time segments
    for price and time; similar to On Balance Volume. The zero line is called
    the baseline. Entry and exit points are commonly determined when crossing
    the baseline.

    Sources:
        https://www.tradingview.com/script/6GR4ht9X-Time-Segmented-Volume/
        https://help.tc2000.com/m/69404/l/747088-time-segmented-volume
        https://usethinkscript.com/threads/time-segmented-volume-for-thinkorswim.519/

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): It's period. Default: 18
        signal (int): It's avg period. Default: 10
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: tsv, signal, ratio
    """
    # Validate Arguments
    length = int(length) if length and length > 0 else 18
    signal = int(signal) if signal and signal > 0 else 10
    mamode = mamode if isinstance(mamode, str) else "sma"
    drift = get_drift(drift)
    offset = get_offset(offset)

    # Calculate Result
    signed_volume = volume * signed_series(close, 1)     # > 0
    signed_volume[signed_volume < 0] = -signed_volume   # < 0
    signed_volume.apply(zero)                            # ~ 0
    cvd = signed_volume * close.diff(drift)

    tsv = cvd.rolling(length).sum()
    signal_ = ma(mamode, tsv, length=signal)
    ratio = tsv / signal_

    # Offset
    if offset != 0:
        tsv = tsv.shift(offset)
        signal_ = signal.shift(offset)
        ratio = ratio.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        tsv.fillna(kwargs["fillna"], inplace=True)
        signal_.fillna(kwargs["fillna"], inplace=True)
        ratio.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        tsv.fillna(method=kwargs["fill_method"], inplace=True)
        signal_.fillna(method=kwargs["fill_method"], inplace=True)
        ratio.fillna(method=kwargs["fill_method"], inplace=True)

    # Name and Categorize
    _props = f"_{length}_{signal}"
    tsv.name = f"TSV{_props}"
    signal_.name = f"TSVs{_props}"
    ratio.name = f"TSVr{_props}"
    tsv.category = signal_.category = ratio.category = "volume"

    # Prepare DataFrame to return
    data = {tsv.name: tsv, signal_.name: signal_, ratio.name: ratio}
    df = DataFrame(data)
    df.name = f"TSV{_props}"
    df.category = tsv.category

    return df