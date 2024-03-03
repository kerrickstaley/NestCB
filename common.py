import logging
from ruamel.yaml import YAML
import io

logger = logging.getLogger('where_to_live')
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setLevel(logging.DEBUG)
logger.addHandler(_handler)


class UnsupportedCityException(Exception):
    pass


class MissingConfigVarException(Exception):
    pass


# https://stackoverflow.com/a/47130538
def _exec_and_eval(script, filename_for_debug, globals=None, locals=None):
    """Execute a script and return the value of the last expression"""
    import ast

    stmts = list(ast.iter_child_nodes(ast.parse(script)))
    if not stmts:
        raise ValueError(f'{filename_for_debug} is empty or only contains comments.')

    if not isinstance(stmts[-1], ast.Expr):
        raise ValueError(
            f'Last line of {filename_for_debug} file was not an expression.'
        )

    exec(
        compile(
            ast.Module(body=stmts[:-1], type_ignores=[]),
            filename=filename_for_debug,
            mode='exec',
        ),
        globals,
        locals,
    )
    return eval(
        compile(
            ast.Expression(body=stmts[-1].value),
            filename=filename_for_debug,
            mode='eval',
        ),
        globals,
        locals,
    )


def _yaml_dumps(v):
    yaml = YAML(typ='safe')
    sio = io.StringIO()

    # https://stackoverflow.com/questions/56950391/yaml-end-always-dumped-even-if-yaml-explicit-end-false
    def strip_document_end_marker(s):
        return s.removesuffix('...\n')

    yaml.dump(v, sio, transform=strip_document_end_marker)
    return sio.getvalue()


_NO_DEFAULT = 'NO_DEFAULT'


def _config(
    name,
    *,
    type=lambda x: x,
    default=_NO_DEFAULT,
    globals=None,
    doc_fn=lambda: '(no docs given)',
):
    """
    Evaluate a configvar.
    """
    from pathlib import Path
    import inspect

    globals = globals or {}

    yaml_path = Path(__file__).parent / 'config' / (name + '.yaml')
    py_path = yaml_path.with_suffix('.py')

    yaml_path_exists = yaml_path.exists()
    py_path_exists = py_path.exists()

    if not yaml_path_exists and not py_path_exists and default is not _NO_DEFAULT:
        with open(yaml_path, 'w') as h:
            h.write(_yaml_dumps(default))

        yaml_path_exists = True

    if not yaml_path_exists and not py_path_exists:
        doc = doc_fn()
        doc = inspect.cleandoc(doc)

        raise MissingConfigVarException(
            f'Missing {name} config var. Help for this config var:\n\n{doc}'
            f'\n\nPlease put the config in the file {yaml_path} or {py_path} .'
        )

    if yaml_path_exists and py_path_exists:
        raise RuntimeError(
            f'Both {yaml_path} and {py_path} exist; only one or the other is allowed.'
        )

    if yaml_path_exists:
        with open(yaml_path) as handle:
            contents = handle.read()
            return type(YAML(typ='safe').load(contents))

    assert py_path_exists
    with open(py_path) as handle:
        contents = handle.read()
        return type(
            _exec_and_eval(
                contents, str(py_path), globals=globals | {'config': _config}
            )
        )


def configvar(
    *args,
    type=lambda x: x,
    return_doc=False,
    default=_NO_DEFAULT,
    globals=None,
    eager=False,
):
    '''
    Define a config variable.

    Example usage:
    @configvar(type=str)
    def foo_api_key():
        """The API key for the foo service."""

    This configvar will be loaded from either <repo_root>/config/foo_api_key.yaml or from
    <repo_root>/config/foo_api_key.py, whichever exists. If the YAML file exists, its contents
    will be used as the value of the configvar. If the .py file exists, it will be executed and
    the value of the last line of the file (which must be an expression, not a statement) will be
    used as the value of the configvar.

    Args:
        type: A function (defaults to float) that will be called to convert the config var to the
            appropriate type.
        return_doc: If True (default is False), the function will be called and the return value
            will be used as the doc for the config var, instead of the docstring.
        default: If passed, will be used as the default value if the user does not supply one,
            and this default will be written into the user's config dir. type(str(default))
            (where type() is the argument, not the builtin) must return a value equal to default.
        globals: Optional dict of {str: value} that will be made available if the config is a
            .py file.
        eager: If False (the default), the configvar is a function that must be called to get the
            value, so you should write e.g. foo_api_key(). If True, the configvar directly
            represents the value, so you should write e.g. foo_api_key. With eager=True the module
            won't load unless the config var is populated, so this should be used sparingly.
    '''
    import functools

    globals = globals or {}

    def decorator(f):
        @functools.wraps(f)
        @functools.lru_cache()
        def decorated():
            def doc_fn():
                if return_doc:
                    return f()
                else:
                    return f.__doc__

            return _config(
                f.__name__, doc_fn=doc_fn, type=type, default=default, globals=globals
            )

        if eager:
            return decorated()
        else:
            return decorated

    if args:
        # This case happens when you do
        #   @configvar
        #   def my_config_var():
        return decorator(args[0])
    else:
        # This case happens when you do
        #   @configvar(type=some_type)
        #   def my_config_var():
        return decorator


def _process_locations(locations_dict):
    import types
    import location

    ret = types.SimpleNamespace()
    for name, (lat, lon) in locations_dict.items():
        setattr(ret, name, location.Location(name, lat, lon))
    return ret


@configvar(type=_process_locations, eager=True)
def locs():
    """
    Set of locations that you want to consider, as (lat, lon) pairs.

    Example config value:

        des_moines: [41.58512155948215, -93.63531744348033]
        seattle: [47.60743693357695, -122.33797497331248]

    The dictionary will be processed and turned into a Namespace. In this example, you would be able to write

        loc.seattle

    in code to represent the lat/lng for Seattle.
    """


__all__ = [
    'logger',
    'UnsupportedCityException',
    'MissingConfigVarException',
    'configvar',
    'locs',
]
