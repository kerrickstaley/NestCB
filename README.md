# NestCB
This is a tool that can help you decide where the best place for you to live is. It helps you run a *cost/benefit analysis* comparing different locations on multiple *factors*. The benefits are *monetized*, i.e. converted into annual dollar terms, so that you can sum them to get an overall annual value for a location.

For example, how much would you pay to live in a city that is identical to New York City, except that it has the weather of San Francisco? SF has better weather than NYC, so it should be a positive value. Would you pay $100 a year? $1,000? $10,000? To do a cost/benefit analysis, you need to answer this question for all the major factors that go into the desirability of a location.

This project is incomplete. I'm putting it out into the world because I think it's already useful for getting a rough sense of where you might want to live, and hopefully others will use and contribute to it :)

## Quick start
1. Run `./quickstart.py`. This will initialize the "config" folder with a skeleton `config/` that compares 3 cities (San Francisco, New York, Seattle) on 2 factors (cost of housing and weather). It'll do an initial run with a dummy config to download some data. This will take about 2 minutes.
2. Run `./main.sh summary`. It will ask you to fill out *configvars* (configuration variables), which are files in the `config/` folder. These have information like how much you'd pay to experience a nice-weather day vs a bad-weather day and how much you'd pay monthly to live in a 3-bedroom home vs a 2-bedroom home.

After doing this, you'll see some output like:
```
All numbers annual benefit (higher is better). Best city first
SEATTLE
Housing:          -27,160
Climate:            4,356
Total:            -22,804

SAN_FRANCISCO
Housing:          -33,624
Climate:            6,888
Total:            -26,736

NEW_YORK
Housing:          -46,786
Climate:            4,288
Total:            -42,498
```

In this example, based on just cost of housing and weather, Seattle is the best choice for you. San Francisco is the runner up. For San Francisco to win out, it'd need to have about $4k / year of other reasons motivating you to live there over Seattle. New York has bad weather and pricey housing. Who would want to live there? :)

## Next steps
After the quick start, you can do a more extensive analysis by adding more locations and enabling more factors. To add more locations, edit `config/locs.yaml`. To enable more factors, edit `config/factor_modules.yaml`. Here are the current factor modules:
- housing
- housing_manual
- climate
- climate_change
- walkability
- bikeability
- transit

After that, maybe consider writing one of your own factor modules! `walkability.py` is a good example to replicate.

## Current limitations
- A lot of the data sources are USA-centric. Pull requests are appreciated to add support for other countries!
- There are many major factors that are currently not accounted for. For example:
  - The people that live near a location (including your friends) and the general "vibe". I think this is the most important factor (i.e. it has the highest annual dollar stddev), but is also hard to quantify/monetize.
  - What jobs are available near a location and how much they pay. I'm hoping to retire early, and I'm doing this analysis to decide where to live once I'm no longer working. So job availability is less important to me, but if someone wants to contribute support for this factor I'll happily review a PR.
  - Taxes (including income and property taxes).
  - Cost of living ex housing.
  - Quality of nearby schools.
  - Ameneties like parks, arts institutions, and restaruants.
  - Crime.
  - Natural disaster and severe weather risk.
- This project currently only supports Linux and macOS. I would like to add support for Windows so more people can use it, but I don't own any Windows computers so it's hard for me to test on Windows. If you'd like to contribute Windows support I'd appreciate it!

## Hacking on the code
This project takes the somewhat experimental approach of keeping all code in Jupyter notebooks that are written to .py files using [Jupytext](https://jupytext.readthedocs.io/en/latest/). To work on the code, you can launch Jupyter with `./start_jupyter.sh`. Then, click one of the `.py` files to open it as a notebook. You can also just edit the `.py` files in a regular text editor.
