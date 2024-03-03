# Having this startup file is equivalent to running
#   %load_ext autoreload
#   %autoreload 2
# at the beginning of every Jupyter notebook and IPython session
from IPython import get_ipython

ipython = get_ipython()
ipython.run_line_magic('load_ext', 'autoreload')
ipython.run_line_magic('autoreload', '2')
