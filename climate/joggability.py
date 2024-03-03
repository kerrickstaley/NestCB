# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from climate.noaa_best import daily_noaa_dfs
from climate._util import parse_since_until_n
import builtins
import datetime
import collections
import copy
import geo
import more_itertools
import requests
import suntime
import util

# %%
# This dumb hack seems necessary when tethering on my phone.
# https://stackoverflow.com/a/46972341/785404
requests.packages.urllib3.util.connection.HAS_IPV6 = False


# %%
def _sunrises_sunsets(loc, since, until):
    """
    Given a city and year, return a list of 365 or 366 pairs giving the sunrise and sunset times for that city and year.

    Sunrises and sunsets are returned in local time.
    """
    sun = suntime.Sun(*loc)
    tz = geo.city_timezone(loc)

    ret = []
    date = since
    while date <= until:
        sunrise = sun.get_local_sunrise_time(date, local_time_zone=tz)
        sunset = sun.get_local_sunset_time(date, local_time_zone=tz)
        # TODO replace suntime with a better library; it has old unfixed bugs e.g.
        # https://github.com/SatAgro/suntime/pull/19
        if sunset < sunrise:
            sunset += datetime.timedelta(days=1)
        if sunrise.date() > date:
            sunrise -= datetime.timedelta(days=1)
        if sunset.date() > date:
            sunset -= datetime.timedelta(days=1)
        assert sunrise.date() == date
        assert sunset.date() == date
        ret.append((sunrise, sunset))
        date += datetime.timedelta(days=1)

    return ret


# %% tags=["active-ipynb"]
# _sunrises_sunsets(locs.berkeley, datetime.date(2021, 1, 1), datetime.date(2022, 1, 1))

# %%
YES = 'YES'  # weather suitable for jogging
TOO_EARLY = 'TOO_EARLY'  # time is before sunrise
TOO_LATE = 'TOO_LATE'  # time is after sunset
TOO_COLD = 'TOO_COLD'  # too cold to jog
TOO_HOT = 'TOO_HOT'  # too hot to jog
TOO_MUCH_RAIN = 'TOO_MUCH_RAIN'  # too much rain to jog
MISSING_TEMP = 'MISSING_TEMP'
MISSING_PRECIP_1HR = 'MISSING_PRECIP_1HR'
MISSING_HOUR = 'MISSING_HOUR'
# TODO compute "heat index" so we can take into account humidity
# https://www.weather.gov/ama/heatindex
NO_REASONS = {TOO_EARLY, TOO_LATE, TOO_COLD, TOO_HOT, TOO_MUCH_RAIN}
UNKNOWN_REASONS = {MISSING_TEMP, MISSING_PRECIP_1HR, MISSING_HOUR}


class CanJogResult:
    @classmethod
    def yes(cls):
        return cls(num_yes=1)

    @classmethod
    def no(cls, reason):
        return cls(no_reasons={reason: 1})

    @classmethod
    def unknown(cls, reason):
        return cls(unknown_reasons={reason: 1})

    @property
    def num_no(self):
        return sum(self.no_reasons.values())

    @property
    def num_unknown(self):
        return sum(self.unknown_reasons.values())

    @property
    def num(self):
        return self.num_yes + self.num_no + self.num_unknown

    def __init__(self, num_yes=0, no_reasons=None, unknown_reasons=None):
        self.num_yes = num_yes
        self.no_reasons = collections.Counter(no_reasons or {})
        self.unknown_reasons = collections.Counter(unknown_reasons or {})

    def __add__(self, other):
        # This is bad style, TODO add a .sum classmethod
        if isinstance(other, int) and other == 0:
            return self

        return self.__class__(
            num_yes=self.num_yes + other.num_yes,
            no_reasons=self.no_reasons + other.no_reasons,
            unknown_reasons=self.unknown_reasons + other.unknown_reasons,
        )

    def __radd__(self, other):
        return self.__add__(other)

    def __repr__(self):
        attrs = ['num_yes', 'no_reasons', 'unknown_reasons']
        pieces = ['{}={}'.format(attr, repr(getattr(self, attr))) for attr in attrs]
        return '{}({})'.format(self.__class__.__name__, ', '.join(pieces))

    def normalized(self, round=None, scale=None):
        def scale_and_round(x):
            if scale is not None:
                x *= scale

            if round is not None:
                x = builtins.round(x, round)

            return x

        num = self.num
        ret = copy.deepcopy(self)
        ret.num_yes = scale_and_round(ret.num_yes / num)

        for d in [ret.no_reasons, ret.unknown_reasons]:
            for k in d:
                d[k] = scale_and_round(d[k] / num)

        return ret


# %%
MIN_TEMP_C = 12
MAX_TEMP_C = 28
MAX_PRECIP_1HR_MM = 1
MIN_CONSEC_HOURS = 3


# %%
def _can_jog(
    df,
    sunrise,
    sunset,
    min_temp_c=MIN_TEMP_C,
    max_temp_c=MAX_TEMP_C,
    max_precip_1hr_mm=MAX_PRECIP_1HR_MM,
    # Note: max_relative_humidity is only used if the dataframe does not have precip_1hr data. See
    # _find_can_jog_humidity_threshold below.
    # TODO max_relative_humidity=87 only gets an F1 score of 0.28 when predicting
    # precip_1hr > max_precip_1hr_mm. We can probably do better.
    max_relative_humidity=87,
    min_consec_hours=MIN_CONSEC_HOURS,
):
    # Note: mutates day_noaa_df
    df['can_jog'] = YES

    use_precip_1hr = df.precip_1hr.isna().mean() < 0.05

    df.loc[df.temp.isna(), 'can_jog'] = MISSING_TEMP
    df.loc[df.precip_1hr.isna() & use_precip_1hr, 'can_jog'] = MISSING_PRECIP_1HR

    df.loc[df.temp < min_temp_c, 'can_jog'] = TOO_COLD
    df.loc[df.temp > max_temp_c, 'can_jog'] = TOO_HOT

    df.loc[(df.precip_1hr > max_precip_1hr_mm) & use_precip_1hr, 'can_jog'] = (
        TOO_MUCH_RAIN
    )
    df.loc[
        (df.relative_humidity > max_relative_humidity) & ~use_precip_1hr, 'can_jog'
    ] = TOO_MUCH_RAIN

    df.loc[df.dt_utc < sunrise, 'can_jog'] = TOO_EARLY
    df.loc[df.dt_utc > sunset, 'can_jog'] = TOO_LATE

    if len(df) < min_consec_hours:
        return CanJogResult.unknown(MISSING_HOUR)

    # Add Nones in place of missing rows
    in_rows = list(df.itertuples())
    rows = in_rows[:1]
    for row in in_rows[1:]:
        gap_hrs = int(
            round((row.dt_utc - rows[-1].dt_utc) / datetime.timedelta(hours=1))
        )
        rows += [None] * (gap_hrs - 1)
        rows.append(row)

    def counter_max(counter):
        try:
            return max(counter, key=lambda k: counter[k])
        except ValueError:
            return None

    # Check each window to see if can jog in that window
    no_cnt = collections.Counter()
    unknown_cnt = collections.Counter()
    for window in more_itertools.sliding_window(rows, min_consec_hours):
        if all(row is not None and row.can_jog == YES for row in window):
            return CanJogResult.yes()

        window_no_cnt = collections.Counter(
            row.can_jog
            for row in window
            if row is not None and row.can_jog in NO_REASONS
        )

        if window_no_cnt:
            # Don't count these as reasons for no's unless there is nothing else
            window_no_cnt[TOO_EARLY] -= 100
            window_no_cnt[TOO_LATE] -= 100
            no_cnt[counter_max(window_no_cnt)] += 1
            continue

        window_unknown_cnt = collections.Counter(
            MISSING_HOUR if row is None else row.can_jog
            for row in window
            if row is None or row.can_jog in UNKNOWN_REASONS
        )

        assert window_unknown_cnt
        unknown_cnt[counter_max(window_unknown_cnt)] += 1

    if unknown_cnt:
        return CanJogResult.unknown(counter_max(unknown_cnt))

    # TODO handle unknown because e.g. there is only one row for the day

    assert no_cnt
    # Don't count these as reasons for no's unless there is nothing else
    no_cnt[TOO_EARLY] -= 100
    no_cnt[TOO_LATE] -= 100
    return CanJogResult.no(counter_max(no_cnt))


@util.cache_on_disk
def can_jog_summary(
    loc,
    since=None,
    until=None,
    n=None,
    min_temp_c=12,
    max_temp_c=25,
    max_precip_1hr_mm=0.5,
    max_relative_humidity=87,
    min_consec_hours=3,
):
    since, until = parse_since_until_n(since, until, n, n_buffer=7)

    ret = []
    for day_noaa_df, (sunrise, sunset) in zip(
        daily_noaa_dfs(loc, since, until), _sunrises_sunsets(loc, since, until)
    ):
        ret.append(
            _can_jog(
                day_noaa_df,
                sunrise,
                sunset,
                min_temp_c=min_temp_c,
                max_temp_c=max_temp_c,
                max_precip_1hr_mm=max_precip_1hr_mm,
                max_relative_humidity=max_relative_humidity,
                min_consec_hours=min_consec_hours,
            )
        )

    return sum(ret)


# %% tags=["active-ipynb"]
# def _find_can_jog_humidity_threshold(precip_1hr_mm_threshold=0.5, max_temp_c=25):
#     """Find a relative_humidity threshold that corresponds to the given max_precip_1hr_mm threshold.
#
#     For some cities (e.g. Taipei) there is no precip_1hr data. So instead we use relative_humidity
#     as a predictor of precip_1hr. Our model is that if
#         temp_c < max_temp_c
#     then
#         relative_humidity > relative_humidity_threshold
#     iff
#         precip_1hr > precip_1hr_mm_threshold
#
#     This function finds and returns the relative_humidity_threshold that maximizes the F1 score over
#     a sample of data from cities with both precip_1hr and relative_humidity.
#
#     We include the max_temp_c filter because above some temperature it's too uncomfortable to be outside
#     regardless of whether it's raining. (In practice I found that this threshold didn't matter).
#     """
#     df = pd.concat([
#         noaa_df(SEATTLE, 2015, 2022),
#         noaa_df(PORTLAND, 2015, 2022),
#         noaa_df(NEW_YORK, 2015, 2022),
#         # noaa_df(BOSTON, 2018, 2022),
#         noaa_df(SAN_FRANCISCO, 2018, 2022),
#     ])
#
#     df = df.dropna(subset=['precip_1hr', 'relative_humidity'])
#     df = df[df.temp < max_temp_c].copy()
#
#     def precision_recall(df, max_relative_humidity):
#         is_raining = df.precip_1hr > precip_1hr_mm_threshold
#         is_humid = df.relative_humidity > max_relative_humidity
#
#         precision = (is_raining & is_humid).mean() / is_humid.mean()
#         recall = (is_raining & is_humid).mean() / is_raining.mean()
#
#         return precision, recall
#
#
#     def f1_score(df, max_relative_humidity):
#         precision, recall = precision_recall(df, max_relative_humidity)
#
#         return 2 / (1 / precision + 1 / recall)
#
#     f1_scores = pd.DataFrame({'max_relative_humidity': list(range(101))})
#     f1_scores['f1_score'] = f1_scores.max_relative_humidity.apply(functools.partial(f1_score, df))
#     return f1_scores

# %% tags=["active-ipynb"]
# f1_scores = _find_can_jog_humidity_threshold()
# print(f1_scores.iloc[f1_scores.f1_score.idxmax()])
