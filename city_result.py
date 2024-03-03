from common import UnsupportedCityException, MissingConfigVarException, configvar, locs
import functools
import pandas as pd


class Imputed(float):
    def __repr__(self):
        return f'{self.__class__.__name__}({float(self)})'


class Proxy(float):
    def __repr__(self):
        return f'{self.__class__.__name__}({float(self)})'


@configvar
def proxies():
    """
    Allows using the value of one location as a proxy for another.

    For example, the config

        climate_change:
            squamish: seattle

    means that the location "squamish" will borrow its "Climate Change" factor value from the location "seattle" (climate_change.py currently only works for US locations).
    """


@functools.total_ordering
class CityResult:
    UNSUPPORTED = 'UNSUPPORTED'

    def __init__(self, loc, value_modules):
        self.loc = loc
        self.value_modules = value_modules
        self.annual_values = {}
        self.total_annual_value = 0

    def _get_proxy_value(self, module):
        try:
            proxy_loc_name = proxies()[module.__name__][self.loc.name]
        except (MissingConfigVarException, KeyError):
            return None

        proxy_loc = locs.__dict__[proxy_loc_name]
        return Proxy(module.annual_value(proxy_loc))

    def compute(self):
        annual_values = {}
        for module in self.value_modules:
            annual_value = self._get_proxy_value(module)
            if annual_value is None:
                try:
                    annual_value = module.annual_value(self.loc)
                except UnsupportedCityException:
                    annual_value = self.UNSUPPORTED

            annual_values.setdefault(module.FACTOR_NAME, []).append(annual_value)

        for k in annual_values:
            if len(annual_values[k]) == 1:
                # If it's a Proxy preserve it
                annual_value = annual_values[k][0]
            else:
                annual_values_k = [
                    v for v in annual_values[k] if v is not self.UNSUPPORTED
                ]
                if annual_values_k:
                    annual_value = sum(annual_values_k) / len(annual_values_k)
                else:
                    annual_value = self.UNSUPPORTED

            self.annual_values[k] = annual_value
            if annual_value is not self.UNSUPPORTED:
                self.total_annual_value += annual_value

    def print(self):
        print(self.loc.name.upper())
        for value_name, annual_value in self.annual_values.items():
            print(f'{value_name + ":":16} ', end='')
            if annual_value == self.UNSUPPORTED:
                print('UNSUPPORTED (total will be inaccurate)')
                continue
            print(f'{annual_value:8,.0f}', end='')
            if isinstance(annual_value, Imputed):
                print(' (IMPUTED)')
            elif isinstance(annual_value, Proxy):
                print(' (PROXY)')
            else:
                print()

        print(f'{"Total:":16} {self.total_annual_value:8,.0f}')
        print()

    def __le__(self, other):
        return self.total_annual_value < other.total_annual_value

    def __eq__(self, other):
        return self.total_annual_value == other.total_annual_value

    def to_pandas(self):
        d = self.annual_values.copy()
        d['Total'] = self.total_annual_value
        for key in d:
            if d[key] is self.UNSUPPORTED:
                d[key] = float('nan')
        return pd.DataFrame(d, index=[self.loc.name.upper()])


# TODO maybe it's better to do this using Pandas?
def impute_missing_values_with_mean(city_results):
    sums = {}
    counts = {}
    for city_result in city_results:
        for key, value in city_result.annual_values.items():
            if value is CityResult.UNSUPPORTED:
                continue
            if isinstance(value, Imputed):
                raise ValueError('Should not re-impute on already imputed results')

            sums.setdefault(key, 0)
            counts.setdefault(key, 0)
            sums[key] += value
            counts[key] += 1

    for city_result in city_results:
        for key, value in city_result.annual_values.items():
            if value is CityResult.UNSUPPORTED:
                mean = sums[key] / counts[key]
                city_result.annual_values[key] = Imputed(mean)
                city_result.total_annual_value += mean


def to_pandas(city_results: list[CityResult]):
    return pd.concat(r.to_pandas() for r in city_results)
