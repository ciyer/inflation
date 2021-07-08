"""
    viz.py

    Utilities for visualizations.
"""

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.formula.api as smf
import statsmodels.api as sm


def set_style():
    sns.set()
    if 'ciyer' in mpl.style.available:
        plt.style.use(['seaborn-darkgrid', 'ciyer'])
        font = {'family': 'sans-serif', 'size': 18}
    else:
        plt.style.use(['seaborn-darkgrid'])
        p = sns.color_palette()
        sns.set_palette([p[0], p[3], p[8], p[2], p[7], p[4]])
        font = {'size': 18}
    mpl.rc('font', **font)
    mpl.rc('figure', dpi=300)
    
    
def annot_line(ax, line_loc, text, text_loc, a_color):
    ax.axvline(pd.to_datetime(line_loc), color=a_color, lw=3, alpha=0.5)
    ax.annotate(text, (pd.to_datetime(text_loc[0]), text_loc[1]), fontsize="x-small")


def plot_min_max_lims(tdf, xcol, ycol):
    mins = tdf.min()
    minmin = mins[[xcol, ycol]].min()
    minmin -= (abs(minmin) * 0.1)
    maxs = tdf.max()
    maxmax = maxs[[xcol, ycol]].max()
    maxmax += (abs(maxmax) * 0.1)
    return [minmin, maxmax]


def arrows(ax, df, x_col, y_col, color):
    for i in range(1, len(df.index) - 2):
        idx = df.index[i]
        idx_p1 = df.index[i+1]
        ax.annotate('',
                    xytext=(df.loc[idx, x_col], df.loc[idx, y_col]),
                    textcoords='data',
                    xy=(df.loc[idx_p1, x_col], df.loc[idx_p1, y_col]),
                    xycoords='data',
                    arrowprops=dict(arrowstyle="-|>", facecolor=color, alpha=0.3,
                        edgecolor=color),
                    color=color,
                    size=15)


def annotate_year(ax, year, df, x_col, y_col):
    y = str(year)
    try:
        ax.annotate(y, (df.loc[y, x_col], df.loc[y, y_col]))
    except:
        pass


def annotate_years(ax, df, xcol, ycol):
    """Annotate years in dataframes that are indexed by year (not month)"""

    start_year = df.index[0].year
    end_year = df.index[-1].year
    years_to_label = set([start_year, end_year])
    bp_year = start_year + 5 - (start_year % 5)
    for y in range(bp_year, 2021, 5):
        years_to_label.add(y)

    for y in years_to_label:
        annotate_year(ax, y, df, xcol, ycol)


def regression(ax, lin_reg, color, label="regression", x_offset=-2, y_offset=0.15):
    lm = lin_reg.lm
    pred_range = lin_reg.pred_range
    predictions = lin_reg.predictions
    ax.plot(pred_range, predictions, color=color, alpha=0.7, lw=3.0, label=label)
    ax.text(pred_range[1] + x_offset, predictions[1] + y_offset, "$r^2={:.2f}$".format(lm.rsquared))


def yeqx(ax, tdf, xcol, ycol, color, lims, label="y = x"):
    l = np.linspace(lims[0], lims[1])
    ax.plot(l, l, color=color, alpha=0.4, lw=3.0, label=label)


def cite_source(ax, source):
    source_header = "Source:"
    viz = "Visualization & Errors: @ciyer"
    ax.annotate(f"{source_header} {source}\n{viz}", (1, 0), (-2, -35), fontsize=8,
                xycoords='axes fraction', textcoords='offset points', va='bottom', ha='right')
    
    
def cite_fig_source(fig, source, x=0.93, y=0.07):
    source_header = "Source:"
    viz = "Visualization & Errors: @ciyer"
    fig.supxlabel(f"{source_header} {source}\n{viz}", x=x, y=y, fontsize=8, va='bottom', ha='right')


def xy_plot(ax, df, lin_reg, scatterc, linec, xeqyc, labelc, labeled_points, xcol, ycol):
    ax.scatter(df[xcol], df[ycol], alpha=0.4, color=scatterc)
    lims = plot_min_max_lims(df, xcol, ycol)
    yeqx(ax, df, xcol, ycol, xeqyc, lims)
    lm = lin_reg.lm
    pred_range = lin_reg.pred_range
    predictions = lin_reg.predictions
    slope = lm.params[xcol]
    label = "regression, $r^2={:.2f}$ ($slope={:.2f}$)".format(lm.rsquared, slope)
    ax.plot(pred_range, predictions, color=linec, alpha=0.7, lw=3.0, label=label)

    if labeled_points:
        ax.scatter(df.loc[labeled_points, xcol], df.loc[labeled_points, ycol], alpha=1, color=labelc)

    for c in labeled_points:
        ax.annotate(c, (df.loc[c, xcol], df.loc[c, ycol]))


def xy_reg_diff_plot(ax, df, lin_reg, scatterc, labelc, labeled_points, xcol, ycol):
    predictions = lin_reg.lm.predict(df)
    pred_diff = df[ycol] - predictions
    ax.scatter(df[xcol], pred_diff, alpha=0.5, color=scatterc)

    if labeled_points:
        ax.scatter(df.loc[labeled_points, xcol], pred_diff.loc[labeled_points], alpha=1, color=labelc)
        
    m = pred_diff.abs().max() + 0.05
    ax.set_ylim([-0.12, 0.12])


class LinReg:
    def __init__(self, df, xcol, ycol):
        self.df = df
        self.xcol = xcol
        self.ycol = ycol
        self.lm = None
        self.pred_range = None
        self.preds_input = None
        self.predictions = None

    def fit(self):
        df = self.df
        xcol= self.xcol
        lm = smf.ols(formula=f"{self.ycol} ~ {xcol}", data=df).fit()
        pred_range = (df[xcol].min(), df[xcol].max())
        preds_input = pd.DataFrame({xcol: pred_range})
        predictions = lm.predict(preds_input)
        self.lm = lm
        self.pred_range = pred_range
        self.preds_input = preds_input
        self.predictions = predictions
