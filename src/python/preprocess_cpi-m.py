"""
  Produce files containing CPI and M{1, 3} from the raw OECD data.
"""
import pandas as pd
import numpy as np
import scipy
import statsmodels.formula.api as smf
import os

import qtm

# %%
cpi_path = "data/oecd/CPI.csv"
m1_path = "data/oecd/M1.csv"
m3_path = "data/oecd/M3.csv"

# %%
# Create output path
os.makedirs("data/preprocess/", exist_ok=True)


# %%
def read_df(path):
    df = pd.read_csv(path)
    df['TIME'] = pd.to_datetime(df['TIME'])
    return df


def df_to_ser(df, name, freq):
    tdf = df[df['FREQUENCY'] == freq].set_index(["LOCATION", "TIME"])
    tdf = tdf.sort_index()
    ser = tdf['Value']
    ser.name = name
    return ser


def read_ser(path, name, freq):
    df = read_df(path)
    return df_to_ser(df, name, freq)


def money_cpi_df(m_ser, cpi_ser, col, freq):
    m_df = pd.concat([m_ser, cpi_ser], axis=1)
    diff_m_df = 100 * m_df.diff() / m_df.shift(1)
    diff_m_df.columns = [f"c_{col}", "c_cpi"]
    if freq == 'M':
        diff_m_df = qtm.calc.pct_rate_to_yearly(diff_m_df, 12)
    elif freq == 'Q':
        diff_m_df = qtm.calc.pct_rate_to_yearly(diff_m_df, 4)
    m_df = m_df.join(diff_m_df).dropna()
    return m_df


def ols(df, x_col, y_col):
    lm = smf.ols(formula=f"{y_col} ~ {x_col}", data=df).fit()
    return lm


def money_cpi_reg_df(m_df, col):
    regs = []
    for lctn in m_df.index.levels[0]:
        try:
            tdf = m_df.loc[lctn, :]
            lm = ols(tdf, col, 'c_cpi')
            regs.append({"LOCATION": lctn, "r2": lm.rsquared, "slope": lm.params.loc[col]})
        except KeyError as e:
            pass


    reg_df = pd.DataFrame(regs).set_index("LOCATION")
    reg_df = reg_df.sort_values("r2", ascending=False)
    reg_df["r2cat"] = pd.qcut(reg_df['r2'], 4, False)
    return reg_df


# %%
cpi_df = read_df(cpi_path)
cpi_df = cpi_df[cpi_df['SUBJECT'] == "TOT"]
cpi_df = cpi_df[cpi_df['MEASURE'] == "IDX2015"]

m1_df = read_df(m1_path)
m3_df = read_df(m3_path)

# %%
cpi_a_ser = df_to_ser(cpi_df, "CPI", "A")
m1_a_ser = df_to_ser(m1_df, "M1", "A")
m1_a_df = money_cpi_df(m1_a_ser, cpi_a_ser, "m1", 'A')
m1_a_df.to_csv("data/preprocess/m1-cpi_a.csv")

# %%
m1_a_reg_df = money_cpi_reg_df(m1_a_df, "c_m1")
m1_a_reg_df.to_csv("data/preprocess/m1-cpi_a_reg.csv")


# %%
cpi_m_ser = df_to_ser(cpi_df, "CPI", "M")
m1_m_ser = df_to_ser(m1_df, "M1", "M")
m1_m_df = money_cpi_df(m1_m_ser, cpi_m_ser, "m1", "M")
m1_m_df.to_csv("data/preprocess/m1-cpi_m.csv")

# %%
m1_m_reg_df = money_cpi_reg_df(m1_m_df, "c_m1")
m1_m_reg_df.to_csv("data/preprocess/m1-cpi_m_reg.csv")

# %%
m3_a_ser = df_to_ser(m3_df, "M3", "A")
m3_a_df = money_cpi_df(m3_a_ser, cpi_a_ser, "m3", "A")
m3_a_df.to_csv("data/preprocess/m3-cpi_a.csv")
m3_a_reg_df = money_cpi_reg_df(m3_a_df, "c_m3")
m3_a_reg_df.to_csv("data/preprocess/m3-cpi_a_reg.csv")

# %%
m3_m_ser = df_to_ser(m3_df, "M3", "M")
m3_m_df = money_cpi_df(m3_m_ser, cpi_m_ser, "m3", "M")
m3_m_df.to_csv("data/preprocess/m3-cpi_m.csv")
m3_m_reg_df = money_cpi_reg_df(m3_m_df, "c_m3")
m3_m_reg_df.to_csv("data/preprocess/m3-cpi_m_reg.csv")
