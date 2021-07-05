import numpy as np


def rate_to_end_value(rate, dur):
    return np.power(rate + 1, dur)


def end_value_to_rate(ev, dur):
    return np.power(ev, 1/dur) - 1


def rate_to_end_value_continuous(rate, dur):
    return np.exp(rate * dur)


def end_value_to_rate_continuous(ev, dur):
    return np.log(ev) / dur


def pct_rate_to_yearly(rate, periods):
    return (rate_to_end_value(rate/100, periods) - 1) * 100

def change_rate(df, loc, col):
    tdf = df.loc[loc]
    var_diff = tdf.iloc[-1][col] / tdf.iloc[0][col]
    num_years = tdf.iloc[-1].name.year - tdf.iloc[0].name.year
    if num_years < 1:
        return 0, 0
    inf_rate = (np.power(var_diff, 1/num_years) - 1) * 100
    return num_years, inf_rate
