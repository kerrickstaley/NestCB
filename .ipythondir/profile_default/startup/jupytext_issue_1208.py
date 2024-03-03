try:
    _is_notebook = get_ipython().__class__.__name__ == 'ZMQInteractiveShell'
except NameError:
    _is_notebook = False

if __name__ == '__main__' and _is_notebook:
    import ipynbname as _ipynbname
    import os as _os
    import sys as _sys

    _modulename = (
        str(_ipynbname.path())
        .removeprefix(_os.environ['PYTHONPATH'])
        .removesuffix('/__init__.py')
        .strip('/')
        .replace('/', '.')
    )

    _sys.modules[__name__].__path__ = [_os.getcwd()]
    _sys.modules[__name__].__file__ = str(_ipynbname.path())
    _sys.modules[_modulename] = _sys.modules[__name__]
