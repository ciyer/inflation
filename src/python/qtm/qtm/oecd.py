"""
  Module for working with the OECD data
"""

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels.api as sm
lowess = sm.nonparametric.lowess

from . import calc
from . import viz

country_code_map = {
    "AUS": "Australia",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CHE": "Switzerland",
    "CHL": "Chile",
    "CHN": "China",
    "COL": "Colombia",
    "CRI": "Costa Rica",
    "CZE": "Czechia",
    "DNK": "Denmark",
    "EA19": "Eurozone",
    "GBR": "United Kingdom",
    "HUN": "Hungary",
    "IDN": "Indonesia",
    "IND": "India",
    "ISL": "Iceland",
    "ISR": "Israel",
    "JPN": "Japan",
    "KOR": "South Korea",
    "MEX": "Mexico",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "POL": "Poland",
    "RUS": "Russia",
    "SWE": "Sweden",
    "TUR": "Turkey",
    "USA": "United States",
    "ZAF": "South Africa"
}

def read_data(path):
    df = pd.read_csv(path)
    df['TIME'] = pd.to_datetime(df['TIME'])
    df = df.set_index(['LOCATION', "TIME"])
    df = df.drop(['OECDE', 'OECD'])
    return df


def read_reg_data(path):
    df = pd.read_csv(path)
    df = df.set_index('LOCATION')
    df = df.drop(['OECDE', 'OECD'])
    return df


def summary_df(df, xcol):
    change_idx = []
    m_change = []
    cpi_change = []
    years= []
    for c, c_df in df.groupby(level=0):
        cr = calc.change_rate(df, c, xcol)
        if cr[0] < 1:
            continue
        years.append(cr[0])
        m_change.append(cr[1])
        cpi_change.append(calc.change_rate(df, c, "CPI")[1])
        change_idx.append(c)

    summary_df = pd.DataFrame({xcol: m_change, "CPI": cpi_change, "years": years}, change_idx)
    return summary_df


def summary_fig(ax, df, xlabel, ylabel, labeled_points, xcol="M1", ycol="CPI"):
    palette = sns.color_palette()
    lin_reg = viz.LinReg(df, xcol, ycol)
    lin_reg.fit()
    viz.xy_plot(ax, df, lin_reg, palette[0], palette[3], palette[4], palette[1], labeled_points, xcol, ycol)
    ax.set_xlabel(xlabel)
    ax.xaxis.set_label_coords(0.2, -0.1)
    ax.set_ylabel(ylabel)
    _ = ax.legend()
    return


def year_summary_df(df):
    idx = []
    start_years = []
    end_years = []
    for c, c_df in df.groupby(level=0):
        start_year = c_df.iloc[0].name[1].year
        end_year = c_df.iloc[-1].name[1].year
        start_years.append(start_year)
        end_years.append(end_year)
        idx.append(c)

    summary_df = pd.DataFrame({"start": start_years, "end": end_years}, idx)
    return summary_df



def to_loc_quantile_df(df, xcol, ycol, numq, name):
    tdf = pd.concat([pd.qcut(df[xcol], numq, range(1, numq + 1)), 
                 pd.qcut(df[ycol], numq, range(1, numq + 1))], axis=1)
    return tdf


def to_quantile_df(df, xcol, ycol, num_quantiles):
    qdfs = []
    qdfs = [to_loc_quantile_df(ldf, xcol, ycol, num_quantiles, name) 
            for name, ldf in df.groupby(level="LOCATION")]

    return pd.concat(qdfs)


def quantile_ts_plot_df(df, cat_col, other_col, tperiod):
    result_dfs = []
    for name, ldf in df.groupby(level='LOCATION'):
        cc = ldf[cat_col].reset_index(level=0, drop=True)
        cc.name = "cat"
        rdf = pd.DataFrame(cc)
        rdf['LOCATION'] = name
        for i in range(0, tperiod):
            rdf.loc[:, f"Year_{i}"] = ldf[other_col].shift(-1*i).reset_index(level=0, drop=True)
        result_dfs.append(rdf)
    result_df = pd.concat(result_dfs).set_index('LOCATION', append=True)
    return result_df.reorder_levels([1, 0]).sort_index().set_index('cat', append=True)


def quantile_ts_summary_df(qts_df, threshold):
    summary_rows = []
    for c, cdf in qts_df.groupby(level="LOCATION"):
        ttdf = cdf.loc[(True if i[2] > threshold else False for i in cdf.index)]
        for i, r in ttdf.iterrows():
            summary_rows.append({"LOCATION": c, "index": i[0], "cat": i[1], "percentage": len(r[r > threshold]) / len(r)})
    return pd.DataFrame(summary_rows)


def ts_a_scatterplot(ax, df_a, col, color, label, frac):
    ax.scatter(df_a.index, df_a[col], alpha=0.7, s=30, color=color, label=label)
    smoothed = lowess(df_a[col], df_a.index, frac=frac, return_sorted=False)
    ax.plot(df_a.index, smoothed, alpha=0.7, lw=3, color=color)


def ts_a_plot(ax, df, loc, start_date, marker_date, years_frac, i_color=None, m_color=None, a_color=None, money="M1"):
    palette = sns.color_palette()
    if i_color is None:
        i_color = palette[5]
    if m_color is None:
        m_color = palette[3]
    if a_color is None:
        a_color = palette[4]
    xcol = f"c_{money.lower()}"
    ycol = "c_cpi"
    tdf = df.loc[loc]
    frac = years_frac/len(tdf)
    ts_a_scatterplot(ax, tdf, xcol, m_color, f"{money} Change", frac)
    ts_a_scatterplot(ax, tdf, ycol, i_color, f"CPI Change", frac)
    # ax.plot(tdf.index, tdf[xcol], alpha=0.7, lw=3, color=palette[0], label=f"{money} Change (%)")
    # ax.plot(tdf.index, tdf[xcol].shift(2), alpha=0.3, lw=2, color=palette[0], label="M1 Change (%) + 2y")
    # ax.plot(tdf.index, tdf[ycol], alpha=0.7, lw=3, color=palette[1], label="CPI Change (%)")
    ax.set_ylabel("% Change")
    if start_date:
        ax.axvspan(pd.to_datetime(start_date), pd.to_datetime("1972"), color=a_color, alpha=0.3, label="Gold Era")
    if marker_date:
        ax.axvline(pd.to_datetime(marker_date), color=palette[4], lw=2, alpha=0.5, label=marker_date)


def facet_ts_plot_label(df, loc):
    tdf = df.loc[loc, :].reset_index()
    dr = tdf['TIME'].agg([np.min, np.max]).dt.year
    # r2 = ue_cpi_r2_df[ue_cpi_r2_df['LOCATION'] == loc]['R2'].iloc[0]
    # title = f"{loc} | {dr['amin']} – {dr['amax']}\n$r^2 = {r2:.2f}$"
    title = f"{loc} | {dr['amin']} – {dr['amax']}"
    return title


def facet_ts_a_plot(xname, yname, color, **kwargs):
    data = kwargs['data']
    loc = data.iloc[0]['LOCATION']
    df = kwargs['df']
    ax = plt.gca()
    money = kwargs['money']
    start_date = kwargs['start_date']
    marker_date = kwargs['marker_date']
    years_frac = kwargs['years_frac']
    i_color = kwargs['i_color']
    m_color = kwargs['m_color']
    a_color = kwargs['a_color']
    ts_a_plot(ax, df, loc, start_date, marker_date, years_frac, i_color, m_color, a_color, money)
    
    
def quantile_ts_scatter(ax, df, color, highlight_color, threshold, alpha=0.025, highlight_alpha=0.1, label=None):
    cats = [i[1] for i in df.index]
    subset = [True if cat > threshold else False for cat in cats]
    tdf = df.loc[subset]
    for i, col in enumerate(tdf.columns):
        l = label if (i == 0) else None
        ax.scatter(np.full(len(tdf), i), tdf[col], color=highlight_color, alpha=highlight_alpha, label=l)


def quantile_ts_lines(ax, df, color, highlight_color, threshold, alpha=0.025, highlight_alpha=0.1,
                    normal_label=None, top_label=None):
    for i, r in df.iterrows():
        c = highlight_color if i[1] > threshold else color
        a = highlight_alpha if i[1] > threshold else alpha
        ax.plot(range(len(r)), r, color=c, alpha=a)

def quantile_ts_threshold(ax, threshold, maxy, a_color, alpha):
    ax.axhspan(threshold, maxy, color=a_color, alpha=alpha)
    
    
def quantile_ts_plot(ax, df, color, highlight_color, threshold, alpha, highlight_alpha, 
                     normal_label, top_label, num_q, threshold_color, threshold_alpha):
    quantile_ts_lines(ax, df, color, highlight_color, threshold, alpha, highlight_alpha,
                        normal_label, top_label)
    quantile_ts_scatter(ax, df, color, highlight_color, threshold, alpha, highlight_alpha, top_label)
    quantile_ts_threshold(ax, threshold, num_q, threshold_color, highlight_alpha)    


def facet_quantile_ts_plot(money, cpi, color, **kwargs):
    palette = sns.color_palette()
    data = kwargs['data']
    loc = data.iloc[0]['LOCATION']
    num_q = kwargs['num_q']
    threshold = kwargs['threshold']
    top_label = kwargs['top_label']
    normal_label = "other year"
    df = kwargs['df']
    alpha = kwargs['alpha']
    highlight_alpha = kwargs['highlight_alpha']
    ax = plt.gca()
    quantile_ts_plot(ax, df.loc[loc], palette[4], palette[1], threshold, alpha, highlight_alpha, 
                     normal_label, top_label, num_q, palette[4], 0.3)
#     quantile_ts_lines(ax, df.loc[loc], palette[4], palette[1], threshold, alpha, highlight_alpha,
#                         normal_label, top_label)
#     quantile_ts_scatter(ax, df.loc[loc], palette[4], palette[1], threshold, alpha, highlight_alpha, top_label)
#     quantile_ts_threshold(ax, threshold, num_q, palette[4], 0.3)


class Data:
    def __init__(self, folder_path, monetary_aggregate):
        """Utility class for working with a given monetary aggregate"""
        self.folder_path = folder_path
        self.monetary_aggregate = monetary_aggregate
        ma = monetary_aggregate.lower()
        self.annual_path = os.path.join(folder_path, f"{ma}-cpi_a.csv")
        self.annual_reg_path = os.path.join(folder_path, f"{ma}-cpi_a_reg.csv")
        self.monthly_path = os.path.join(folder_path, f"{ma}-cpi_m.csv")
        self.monthly_reg_path = os.path.join(folder_path, f"{ma}-cpi_m_reg.csv")
        palette = sns.color_palette()
        self.inflation_color = palette[3]
        self.money_color = palette[2]
        self.annot_color = palette[4]
        self.annual_df = None
        self.annual_df_full = None   # include the US 2020 data
        self.annual_reg_df = None
        self.monthly_df = None
        self.monthly_df_full = None  # include May 2020 for the US
        self.monthly_reg_df = None
        self.max_inflation_df = None
        
    def read(self):
        self.annual_df_full = read_data(self.annual_path)
        df = self.annual_df_full
        df = df.drop(index=df.loc[("USA", "2020"), :].index[0])
        isl_start_year = df.loc["ISL"].index[0].year
        df = df.drop(index=df.loc[("ISL", slice(str(isl_start_year), "1976")), :].index)
        self.annual_df = df
        self.annual_reg_df = read_reg_data(self.annual_reg_path)
        self.monthly_df_full = read_data(self.monthly_path)
        df = self.monthly_df_full
        df = df.drop(index=df.loc[("USA", "2020-05"), :].index[0])
        isl_start_year = df.loc["ISL"].index[0].year
        df = df.drop(index=df.loc[("ISL", slice(str(isl_start_year), "1976")), :].index)
        self.monthly_df = df
        self.monthly_reg_df = read_reg_data(self.monthly_reg_path)
        max_inflation_df = pd.DataFrame(
            self.annual_df.groupby(level="LOCATION").max()['c_cpi'].sort_values(ascending=False))
        max_inflation_df['quantile'] = pd.qcut(max_inflation_df['c_cpi'], 4, labels=range(1, 5))
        self.max_inflation_df = max_inflation_df
        
    def money_col(self):
        return f"c_{self.monetary_aggregate.lower()}"

    
    def plot_summary(self, ax, countries_to_label):
        ma = self.monetary_aggregate
        sdf = summary_df(self.annual_df, ma)
        summary_fig(ax, sdf, f"{ma} growth rate", "Inflation rate", countries_to_label, ma)
        
    def annual_ts_fig(self, marker_date=None, years_frac=3, subset=None, sharey=False, df=None, ylabel="% Change", 
                      citex=0.93, citey=0.07, show_title=False):
        if df is None:
            df = self.annual_df
        if subset is None:
            tdf = df.reset_index()
            col_order = self.max_inflation_df.index
        else:
            tdf = df.loc[subset].reset_index()
            col_order = self.max_inflation_df.loc[subset].index
        g = sns.FacetGrid(tdf, col="LOCATION", col_wrap=4, col_order=col_order, sharey=sharey, height=3, aspect=1.5)
        start_date = tdf['TIME'].min()
        g.map_dataframe(facet_ts_a_plot, "Year", ylabel, df=df, 
                        start_date=start_date, marker_date=marker_date,
                        money=self.monetary_aggregate,
                        years_frac=years_frac,
                        i_color=self.inflation_color, m_color=self.money_color,
                        a_color=self.annot_color)
        for l in tdf['LOCATION'].values:
            ax = g.axes_dict[l]
            ax.set_title(facet_ts_plot_label(self.annual_df, l))
        if subset is None:
            g.axes[3].legend()
        if show_title:
            tdf = df.loc[subset].groupby(level='LOCATION').max()
            max_vals = tdf.agg([np.max, np.min])['c_cpi']
            plt.gcf().suptitle(f"Year over Year Changes in CPI and M1 | Max Inflation {max_vals['amax']:.0f}% — {max_vals['amin']:.0f}%")    
        viz.cite_fig_source(plt.gcf(), "OECD", citex, citey)
        plt.tight_layout()        
        
    def quantile_subset(self, q):
        return self.max_inflation_df.index[self.max_inflation_df['quantile'] == q]
    
    def quantile_ts_df(self, num_q, num_y, label_column=None):
        if label_column is None:
            cat_col = self.money_col()
            other_col = "c_cpi"
        if label_column == "CPI":
            cat_col = "c_cpi"
            other_col = self.money_col()     
        q_df = to_quantile_df(self.annual_df, cat_col, other_col, num_q)
        return quantile_ts_plot_df(q_df, cat_col, other_col, num_y)
    
    def quantile_ts_fig(self, threshold_frac, num_q=20, num_y=6, pp_df=None):
        if pp_df is None:
            pp_df = self.quantile_ts_df(num_q, num_y)
        max_pct = pp_df.max().max()
        threshold = (1 - threshold_frac) * max_pct - 1
        tdf = pp_df.reset_index()
        pp_summary_df = quantile_ts_summary_df(pp_df, threshold)
        pp_summary_ser = pp_summary_df.groupby("LOCATION").mean()['percentage'].sort_values(ascending=False)
        col_order = pp_summary_ser.index
        # top_label = f"top {threshold_frac*100:.0f}% year"
        top_label = None
        g = sns.FacetGrid(tdf, col="LOCATION", col_wrap=4, col_order=col_order, height=3, aspect=1.2)
        g.map_dataframe(facet_quantile_ts_plot, "Years Out", "Inflation Rank", df=pp_df, alpha=0.2, 
                        highlight_alpha=0.3, num_q=num_q,
                        threshold=threshold, top_label=top_label)
        for l in tdf['LOCATION'].values:
            ax = g.axes_dict[l]
            label_base = facet_ts_plot_label(self.annual_df, l)
            title = f"{label_base} | {pp_summary_ser.loc[l]*100:.0f}%"
            ax.set_title(title)
        # g.axes[3].legend();
    

# Triage -- not sure we need this stuff
    
def clipped_monthly_df(df_a, df_m):
    limit_max = df_a.max().max() * 1.1
    limit_min = abs(df_a.min().min()) * -1.1
    clipped_df = df_m.copy()
    clipped_df[clipped_df > limit_max] = limit_max
    clipped_df[clipped_df < limit_min] = limit_min
    return clipped_df


def ts_am_scatterplot(ax, df_a, df_m, col, m_offset, color, label, frac):
    ax.scatter(df_a.index, df_a[col], alpha=0.7, s=30, color=color, label=label)
    x_loc = pd.to_datetime(df_m.index.year, format="%Y")
    ax.scatter(x_loc, df_m[col], alpha=0.05, s=15, color=color)
    smoothed = lowess(df_m[col], df_m.index, frac=frac, return_sorted=False)
    ax.plot(df_m.index, smoothed, alpha=0.7, lw=3, color=color)


def ts_am_plot(ax, df_a, df_m, loc, start_date, marker_date, money="M1"):
    palette = sns.color_palette()
    xcol = f"c_{money.lower()}"
    ycol = "c_cpi"
    tdf_a = df_a.loc[loc, [xcol, ycol]]
    try:    
        tdf_m = df_m.loc[loc, [xcol, ycol]]    
        tdf_m_clipped = clipped_monthly_df(tdf_a, tdf_m)
        frac = 24/len(tdf_m)
        ts_am_scatterplot(ax, tdf_a, tdf_m_clipped, xcol, pd.to_timedelta("0W"), palette[0], label=f"{money} Change (%)", frac=frac)
        ts_am_scatterplot(ax, tdf_a, tdf_m_clipped, ycol, pd.to_timedelta("25W"), palette[1], label="CPI Change (%)", frac=frac)
    except KeyError as e:
        frac = 2/len(tdf_a)
        ts_am_scatterplot(ax, tdf_a, tdf_a, xcol, pd.to_timedelta("0W"), palette[0], label=f"{money} Change (%)", frac=frac)
        ts_am_scatterplot(ax, tdf_a, tdf_a, ycol, pd.to_timedelta("0W"), palette[1], label="CPI Change (%)", frac=frac)
        
    ax.set_ylabel("% Change")
    if start_date:
        ax.axvspan(pd.to_datetime(start_date), pd.to_datetime("1972"), color=palette[4], alpha=0.3, label="Gold Era")
    if marker_date:
        ax.axvline(pd.to_datetime(marker_date), color=palette[4], lw=2, alpha=0.5, label=marker_date)
        
def facet_ts_am_plot(money, ycol, color, **kwargs):
    data = kwargs['data']
    loc = data.iloc[0]['LOCATION']
    df_a = kwargs['df_a']
    df_m = kwargs['df_m']
    ax = plt.gca()
    start_date = kwargs['start_date']
    marker_date = kwargs['marker_date']
    ts_am_plot(ax, df_a, df_m, loc, start_date, marker_date, money)
        
        
def ts_am_fig(self, marker_date, sharey=False):
    tdf = self.annual_df.reset_index()
    g = sns.FacetGrid(tdf, col="LOCATION", col_wrap=3, col_order=self.annual_reg_df.index, sharey=sharey, aspect=1.5)
    start_date = tdf['TIME'].min()
    g.map_dataframe(facet_ts_am_plot, "M1", "CPI", 
                    df_a=self.annual_df, df_m=self.monthly_df, 
                    start_date=start_date, marker_date=marker_date)
    for l in tdf['LOCATION'].values:
        ax = g.axes_dict[l]
        ax.set_title(facet_ts_plot_label(self.annual_df, l))
    g.axes[2].legend()


