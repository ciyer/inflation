"""
  Module for working with the Barro data
"""
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

from .calc import rate_to_end_value_continuous
from . import viz


def read_barro_data(path="data/barro/barro-data-set.csv"):
    df = pd.read_csv(path)
    df["Growth rate of velocity"] = df["Inflation rate"] + df["Growth rate of real GDP"] - df["Growth rate of currency"]
    df = df.drop('1980-2000 Inflation rate', axis=1)
    df.columns = ["country", "c_cpi_rate", "c_m1_rate", "c_m1_real_rate", "c_t_rate", "c_v_rate"]
    df['cpi'] = rate_to_end_value_continuous(df['c_cpi_rate'], 40)
    df['m1'] = rate_to_end_value_continuous(df['c_m1_rate'], 40)
    df['t'] = rate_to_end_value_continuous(df['c_t_rate'], 40)
    df['v'] = rate_to_end_value_continuous(df['c_v_rate'], 40)
    df['mv'] = df['m1'] * df['v']
    df['pt'] = df['cpi'] * df['t']
    df['c_pt_rate'] = df['c_cpi_rate'] + df['c_t_rate']
    df['c_mv_rate'] = df['c_m1_rate'] + df['c_v_rate']
    return df.set_index("country")


def xy_plot(ax, df, xlabel, ylabel, labeled_points, palette, xcol, ycol):
    lin_reg = viz.LinReg(df, xcol, ycol)
    lin_reg.fit()
    viz.xy_plot(ax, df, lin_reg,  palette[0], palette[3], palette[4], palette[1], labeled_points, xcol, ycol)
    
    ax.set_xlim([-0.05, 1])
    ax.set_ylim([-0.05, 1])
    ax.set_xlabel(xlabel)
    ax.xaxis.set_label_coords(0.2, -0.1)
    ax.set_ylabel(ylabel)
    
    _ = ax.legend()
    return lin_reg
    


def xy_fig(df, xlabel, ylabel, labeled_points, xcol="c_m1_rate", ycol="c_cpi_rate", figsize=(6, 6)):
    palette = sns.color_palette()
    fig, ax = plt.subplots(figsize=figsize)
    xy_plot(ax, df, xlabel, ylabel, labeled_points, palette, xcol, ycol)
    viz.cite_source(ax, "Barro Marcoeconomics: A Modern Approach, 2008")
    plt.tight_layout()
    return fig


def xy_fig_with_error(df, xlabel, ylabel, labeled_points, xcol="c_m1_rate", ycol="c_cpi_rate", figsize=(12, 6)):
    palette = sns.color_palette()
    fig, axs = plt.subplots(1, 2, sharex=True, sharey=False, figsize=figsize)
    lin_reg = xy_plot(axs[0], df, xlabel, ylabel, labeled_points, palette, xcol, ycol)

    viz.xy_reg_diff_plot(axs[1], df, lin_reg, palette[0], palette[1], labeled_points, xcol, ycol)
    viz.cite_source(axs[1], "Barro Marcoeconomics: A Modern Approach, 2008")
    axs[1].set_ylabel("Regression Error")
    plt.tight_layout()
    return fig
