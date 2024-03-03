#!/usr/bin/env python3
import argparse
import cProfile
import sys
import pdb
import pstats

from common import configvar, locs
import city_result

parser = argparse.ArgumentParser()
parser.add_argument(
    '--pdb', action='store_true', help='drop into a debugger upon exception'
)
parser.add_argument(
    '--profile', action='store_true', help='print out performance profile after run'
)
subparsers = parser.add_subparsers()

ALL_MODULES = [
    'housing',
    'housing_manual',
    'climate',
    'climate_change',
    'walkability',
    'bikeability',
    'transit',
]


@configvar(return_doc=True, type=lambda x: x)
def factor_modules():
    return f"""
        Which factors to use in the analysis.

        The value is a list of names of Python modules.

        Example config:

            - housing
            - climate

        The full list of supported modules is: {ALL_MODULES}.
        """


def compute_results(locs=locs.__dict__.values(), impute=False):
    """
    Compute CityResult with the values for each given city * module.

    Results are returned sorted from lowest to highest value.
    """
    modules = [__import__(name) for name in factor_modules()]
    city_results = []
    for loc in locs:
        result = city_result.CityResult(loc, modules)
        result.compute()
        city_results.append(result)

    if impute:
        city_result.impute_missing_values_with_mean(city_results)

    city_results.sort()
    return city_results


def compute_results_pd(*args, **kwargs):
    """
    Similar to compute_results but return results as a Pandas DataFrame.
    """
    return city_result.to_pandas(compute_results(*args, **kwargs))


def value_summary(args):
    if args.cities == []:
        # Hardcoded list of cities that we fully support
        cities = locs.__dict__.values()
    else:
        cities = args.cities

    city_results = compute_results(cities, impute=args.impute)

    print('All numbers annual benefit (higher is better). Best city first')
    for result in reversed(city_results):
        result.print()


subparser = subparsers.add_parser(
    'summary',
    description='Print a summary of the costs of living in the given cities',
)
subparser.set_defaults(func=value_summary)
subparser.add_argument('cities', nargs='*')
subparser.add_argument(
    '--impute',
    action='store_true',
    help='Impute missing/unknown data using the mean of other cities',
)


def main(args):
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__' and not hasattr(sys, 'ps1'):
    args = parser.parse_args()
    try:
        if args.profile:
            with cProfile.Profile() as pr:
                main(args)
            p = pstats.Stats(pr)
            p.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(50)
        else:
            main(args)
    except:  # noqa: E722
        if args.pdb:
            pdb.post_mortem()
        else:
            raise
