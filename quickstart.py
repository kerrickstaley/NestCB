#!/usr/bin/env python3
import subprocess
from pathlib import Path
import textwrap
import venv
import sys


def main():
    setup_venv()
    setup_config()
    initial_run()
    remove_dummy_configs()


def setup_venv():
    venvdir = Path('venv')
    if venvdir.exists():
        print('venv dir already exists; skipping venv setup', file=sys.stderr)
        return

    venv.create(venvdir, with_pip=True)
    subprocess.check_call(['venv/bin/pip', 'install', '-r', 'requirements.in'])
    subprocess.check_call(['venv/bin/jupytext-config', 'set-default-viewer'])


def setup_config():
    confdir = Path('config')
    if confdir.exists():
        print('config dir already exists; skipping config setup', file=sys.stderr)
        return

    confdir.mkdir()
    subprocess.check_call(['git', 'init'], cwd=confdir)
    subprocess.check_call(
        ['git', 'commit', '--allow-empty', '-m', 'Initial commit'], cwd=confdir
    )

    with open('config/factor_modules.yaml', 'w') as f:
        f.write(
            textwrap.dedent(
                """\
                - housing
                - climate
                """
            )
        )

    with open('config/locs.yaml', 'w') as f:
        f.write(
            textwrap.dedent(
                """\
                new_york: [40.74864922773491, -73.98997143018362]
                san_francisco: [37.77354825453357, -122.44098309231866]
                seattle: [47.60743693357695, -122.33797497331248]
                """
            )
        )

    # Write dummy values so we can do an initial run.
    with open('config/value_of_good_weather_day.yaml', 'w') as f:
        f.write('0')

    with open('config/housing_marginal_utility_per_month.yaml', 'w') as f:
        f.write('{1: 0, 2: 0, 3: 0, 4: 0, 5: 0}')


def initial_run():
    subprocess.check_call(['./main.sh', 'summary'])


def remove_dummy_configs():
    Path('config/value_of_good_weather_day.yaml').unlink()
    Path('config/housing_marginal_utility_per_month.yaml').unlink()


if __name__ == '__main__':
    main()
