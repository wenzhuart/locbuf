# -*- coding: utf-8 -*-
# Created by Bamboo - 06 Feb 2020 (Thu)


import re
import numpy
from pathlib import Path
import pandas as pd
from functools import wraps
from datetime import datetime, timedelta, date
import logging
logger = logging.getLogger('localizer')


class Buffer(object):
    def __init__(self, tmp_folder='loc_tmp', overtime_days=3):
        self.overtime_days = overtime_days
        self.tmp_path = self._ensure_folder(tmp_folder)
        self.date_format = "%Y%m%d"

    def _ensure_folder(self, folder):
        path = Path(folder)
        if not path.exists():
            logger.info('creating {}'.format(folder))
            path.mkdir(parents=True)
        return path

    def _save_csv(self, df, path):
        if not isinstance(df, pd.DataFrame):
            return
        self._ensure_folder(path.parent)
        df.to_csv(path)

    def _is_overtimed(self, stockfile):
        days_before = date.today() - timedelta(days=self.overtime_days)
        mtime = stockfile.stat().st_mtime
        file_time = date.fromtimestamp(mtime)
        if file_time < days_before:
            return True
        return False

    def _get_dtobj_date(self, datearg):
        if isinstance(datearg, (int, numpy.int64)):
            datearg = str(datearg)
        if isinstance(datearg, datetime):
            return datearg
        try:
            dt_date = datetime.strptime(datearg, self.date_format)
        except Exception as e:
            raise e
        return dt_date

    def _get_str_date(self, dt):
        if isinstance(dt, datetime):
            str_date = dt.strftime(self.date_format)
            return str_date
        else:
            return dt

    def _get_csv_timespan(self, csvdf):
        csv_early_dt = self._get_dtobj_date(csvdf.index.min())
        csv_last_dt = self._get_dtobj_date(csvdf.index.max())
        return csv_early_dt, csv_last_dt

    def _normalize_date_format(self, date):
        '''
        input: int or str, 4-2-2 char - '2012/09/09' or '2012-09-09' etc ...
        output: str - '20120909'
        '''
        date_re = re.match(r"(\d{4})[-/\.\\\s]*(\d{2})[-/\.\\\s]*(\d{2})", str(date))
        if date_re:
            date_re.groups()
            date_re = ''.join(date_re.groups())
            return date_re
        logger.warning('date cannot be formated: {}'.format(date))
        return date

    def _normalize_df(self, df, date_colname):
        # --- if df emtpy or None ---
        if not isinstance(df, pd.DataFrame):
            return None
        if df.empty:
            return None
        if df.index.name == date_colname:
            # --- already normalized ---
            return df
        # --- ensure date-order of df ---
        df[date_colname] = df[date_colname].apply(self._normalize_date_format)
        df_start_dt = datetime.strptime(df.iloc[0][date_colname], self.date_format)
        df_end_dt = datetime.strptime(df.iloc[-1][date_colname], self.date_format)
        if df_start_dt > df_end_dt:
            # --- org-func was date-reversed, change to upright ---
            df = df.iloc[::-1]
        # --- set index ---
        df = df.set_index(date_colname)
        return df

    # --- decorate method ---
    def csv_buffer(self, tag=None, dfdt_arg=None, strt_arg=None, end_arg=None):
        def decorate(func, *args):
            @wraps(func)            
            def wrapper(instance, *args, **kwargs):
                funcname = func.__qualname__
                filename = '{}.csv'.format(kwargs.get(tag) or funcname)
                stockfile = list((self.tmp_path / funcname).glob(filename))
                # --- no tmp file yet, request and save ---
                if not stockfile:
                    logger.info('new file {}.csv'.format(filename))
                    reqdf = func(instance, *args, **kwargs)
                    drydf = self._normalize_df(reqdf, dfdt_arg)
                    self._save_csv(drydf, self.tmp_path / funcname / filename)
                    return drydf
                stockfile = stockfile.pop()
                csv_df = self._normalize_df(pd.read_csv(stockfile), dfdt_arg)
                # --- func has no date-arg, use ctime ---
                if not strt_arg or not end_arg:
                    logger.info('func has no date-args, use mtime method')
                    if self._is_overtimed(stockfile):
                        # --- update csv file ---
                        logger.info('{} overtimed, renew'.format(stockfile))
                        df = func(instance, *args, **kwargs)
                        redf = self._normalize_df(df, dfdt_arg)
                        self._save_csv(redf, self.tmp_path / funcname / filename)
                        return redf
                    return csv_df
                # --- try to expand df by date-args ---
                csv_early_dt, csv_last_dt = self._get_csv_timespan(csv_df)
                arg_start = kwargs.get(strt_arg) or self._get_str_date(csv_early_dt)
                arg_start = self._normalize_date_format(arg_start)
                arg_end = kwargs.get(end_arg) or self._get_str_date(datetime.today())
                arg_end = self._normalize_date_format(arg_end)
                exdf = csv_df
                if self._get_dtobj_date(arg_start) + timedelta(days=1) < csv_early_dt:
                    logger.info('out of csv early')
                    reseted_end = self._get_str_date(csv_early_dt - timedelta(days=1))
                    rstkw_end = kwargs.copy()
                    rstkw_end.update({strt_arg: arg_start, end_arg: reseted_end})
                    logger.info('ext-requesting {} -> {}'.format(arg_start, reseted_end))
                    df = func(instance, *args, **rstkw_end)
                    erldf = self._normalize_df(df, dfdt_arg)
                    exdf = pd.concat([erldf, exdf])
                if self._get_dtobj_date(arg_end) - timedelta(days=1) > csv_last_dt:
                    logger.info('out of csv last')
                    reseted_start = self._get_str_date(csv_last_dt + timedelta(days=1))
                    rstkw_strt = kwargs.copy()
                    rstkw_strt.update({strt_arg: reseted_start, end_arg: arg_end})
                    logger.info('ext-requesting {} -> {}'.format(reseted_start, arg_end))
                    df = func(instance, *args, **rstkw_strt)
                    ltdf = self._normalize_df(df, dfdt_arg)
                    exdf = pd.concat([exdf, ltdf])
                if not exdf.equals(csv_df):
                    logger.info('saving new csv {}'.format(filename))
                    self._save_csv(exdf, self.tmp_path / funcname / filename)
                return exdf.loc[arg_start:arg_end]
            return wrapper
        return decorate







