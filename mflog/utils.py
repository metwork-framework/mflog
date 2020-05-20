# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import fnmatch
import logging
import fcntl
import sys
import six
import importlib
import inspect
try:
    from rich.console import Console
    from rich.tabulate import tabulate_mapping
except ImportError:
    pass

OVERRIDE_LINES_CACHE = None
LEVEL_FROM_LOGGER_NAME_CACHE = {}


def write_with_lock(f, message):
    fcntl.flock(f, fcntl.LOCK_EX)
    f.write(message)


def flush_with_lock(f):
    f.flush()
    fcntl.flock(f, fcntl.LOCK_UN)


def __reset_level_from_logger_name_cache():
    global LEVEL_FROM_LOGGER_NAME_CACHE
    LEVEL_FROM_LOGGER_NAME_CACHE = {}


def get_func_by_path(func_path):
    func_name = func_path.split('.')[-1]
    module_path = ".".join(func_path.split('.')[0:-1])
    if module_path == "":
        print("ERROR: %s must follow 'pkg.function_name'" % func_path,
              file=sys.stderr)
        sys.exit(1)
    if func_path.endswith(')'):
        print("ERROR: %s must follow 'pkg.function_name'" % func_path,
              file=sys.stderr)
        print("=> EXIT", file=sys.stderr)
        sys.exit(1)
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        print("ERROR: can't import %s" % module_path, file=sys.stderr)
        print("=> EXIT", file=sys.stderr)
        sys.exit(1)
    try:
        return getattr(mod, func_name)
    except Exception:
        print("ERROR: can't get %s on %s" % (func_name, module_path),
              file=sys.stderr)
        print("=> EXIT", file=sys.stderr)
        sys.exit(1)


class classproperty(object):

    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class Config(object):

    _instance = None
    _minimal_level = None
    _json_minimal_level = None
    _json_file = None
    _override_files = None
    _override_dict = None
    _extra_context_func = None
    _json_only_keys = None
    _syslog_address = None
    _syslog_format = None
    _syslog_minimal_level = None
    _fancy_output = None
    _auto_dump_locals = True

    def __init__(self, minimal_level=None, json_minimal_level=None,
                 json_file=None, override_files=None,
                 thread_local_context=False,
                 extra_context_func=None, json_only_keys=None,
                 override_dict={}, syslog_address=None, syslog_format=None,
                 syslog_minimal_level=None,
                 fancy_output=None,
                 auto_dump_locals=True):
        global LEVEL_FROM_LOGGER_NAME_CACHE, OVERRIDE_LINES_CACHE
        OVERRIDE_LINES_CACHE = {}
        LEVEL_FROM_LOGGER_NAME_CACHE = {}
        if minimal_level is not None:
            self._minimal_level = minimal_level
        else:
            self._minimal_level = os.environ.get('MFLOG_MINIMAL_LEVEL', 'INFO')
        if json_minimal_level is not None:
            self._json_minimal_level = json_minimal_level
        else:
            self._json_minimal_level = \
                os.environ.get('MFLOG_JSON_MINIMAL_LEVEL', 'WARNING')
        if syslog_minimal_level is not None:
            self._syslog_minimal_level = syslog_minimal_level
        else:
            self._syslog_minimal_level = \
                os.environ.get('MFLOG_SYSLOG_MINIMAL_LEVEL', 'WARNING')
        if syslog_format is not None:
            self._syslog_format = syslog_format
        else:
            self._syslog_format = \
                os.environ.get('MFLOG_SYSLOG_FORMAT', 'null')
        if self._syslog_format not in ('null', 'msg_only', 'json'):
            raise Exception("unknown syslog format: %s => must be null, "
                            "msg_only or json")
        if self._syslog_format == "null":
            self._syslog_format = None
        if json_file is not None:
            self._json_file = json_file
        else:
            self._json_file = os.environ.get("MFLOG_JSON_FILE", None)
            if self._json_file == "null":
                self._json_file = None
        if syslog_address is not None:
            tmpsyslog = syslog_address
        else:
            tmpsyslog = os.environ.get("MFLOG_SYSLOG_ADDRESS", None)
            if tmpsyslog == "null":
                tmpsyslog = None
        if isinstance(tmpsyslog, six.string_types):
            tmpsyslog2 = tmpsyslog.split(':')
            if len(tmpsyslog2) == 1:
                self._syslog_address = (tmpsyslog2[0], 514)
            elif len(tmpsyslog2) == 2:
                self._syslog_address = (tmpsyslog2[0], int(tmpsyslog2[1]))
            else:
                raise Exception("wrong syslog_address type: %s" % tmpsyslog)
        if override_files is not None:
            self._override_files = override_files
        else:
            self._override_files = \
                [x.strip() for x in os.environ.get(
                    "MFLOG_MINIMAL_LEVEL_OVERRIDE_FILES", "").split(';')]
        if extra_context_func is not None:
            self._extra_context_func = extra_context_func
        else:
            if "MFLOG_EXTRA_CONTEXT_FUNC" in os.environ:
                self._extra_context_func = \
                    get_func_by_path(os.environ['MFLOG_EXTRA_CONTEXT_FUNC'])
            else:
                self._extra_context_func = None
        if self._extra_context_func and not callable(self._extra_context_func):
            print("ERROR: extra_context_func must be a python callable",
                  file=sys.stderr)
            print("=> EXIT", file=sys.stderr)
            sys.exit(1)
        if json_only_keys is not None:
            self._json_only_keys = json_only_keys
        else:
            if "MFLOG_JSON_ONLY_KEYS" in os.environ:
                self._json_only_keys = \
                    os.environ["MFLOG_JSON_ONLY_KEYS"].split(',')
            else:
                self._json_only_keys = []
        self._override_dict = override_dict
        if fancy_output is None:
            if 'rich' in sys.modules:
                self._fancy_output = None
            else:
                self._fancy_output = False
        else:
            self._fancy_output = fancy_output
        self._auto_dump_locals = auto_dump_locals

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def set_instance(cls, *args, **kwargs):
        cls._instance = Config(*args, **kwargs)

    @classproperty
    def minimal_level(cls):  # pylint: disable=E0213
        return cls.get_instance()._minimal_level

    @classproperty
    def auto_dump_locals(cls):  # pylint: disable=E0213
        return cls.get_instance()._auto_dump_locals

    @classproperty
    def extra_context_func(cls):  # pylint: disable=E0213
        return cls.get_instance()._extra_context_func

    @classproperty
    def json_minimal_level(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_minimal_level

    @classproperty
    def json_file(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_file

    @classproperty
    def override_files(cls):  # pylint: disable=E0213
        return cls.get_instance()._override_files

    @classproperty
    def syslog_minimal_level(cls):  # pylint: disable=E0213
        return cls.get_instance()._syslog_minimal_level

    @classproperty
    def syslog_address(cls):  # pylint: disable=E0213
        return cls.get_instance()._syslog_address

    @classproperty
    def syslog_format(cls):  # pylint: disable=E0213
        return cls.get_instance()._syslog_format

    @classproperty
    def override_dict(cls):  # pylint: disable=E0213
        return cls.get_instance()._override_dict

    @classproperty
    def json_only_keys(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_only_keys

    @classproperty
    def fancy_output(cls):  # pylint: disable=E0213
        return cls.get_instance()._fancy_output


def level_name_to_level_no(level_name):
    """Convert level_name (debug, WARNING...) to level number.

    Args:
        level_name (string): A level name (debug, warning, info, critical
            or errot), case insensitive.

    Returns:
        (int) Corresponding level number (in logging library).

    Raises:
        Exception: if the level in unknown.

    """
    ulevel_name = level_name.upper()
    if ulevel_name == "DEBUG" or ulevel_name == "NOTSET":
        return logging.DEBUG
    elif ulevel_name == "INFO":
        return logging.INFO
    elif ulevel_name == "WARNING":
        return logging.WARNING
    elif ulevel_name == "ERROR" or ulevel_name == "EXCEPTION":
        return logging.ERROR
    elif ulevel_name == "CRITICAL":
        return logging.CRITICAL
    else:
        raise Exception("unknown level name: %s" % level_name)


def _file_to_lines(file_path):
    """Read the given file_path and decode mflog_override format.

    foo.bar.* => DEBUG
    foo.* => WARNING

    Notes:
    - lines beginning with # are ignored
    - the left part is a read as a fnmatch pattern
    - the right part is a case insensitive level name

    Args:
        file_path (string): The full path of the file to read.

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    try:
        with open(file_path, "r") as f:
            tmp = [x.split('=>') for x in f.readlines()]
            lines = [(x[0].strip(), x[1].strip()) for x in tmp
                     if len(x) == 2 and not x[0].strip().startswith('#')]
        return lines
    except IOError:
        return []


def _get_override_lines(path):
    """Read the custom level override configuration file (if exists).

    Args:
        path (string): the full path of the override configuration file.

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global OVERRIDE_LINES_CACHE
    if path not in OVERRIDE_LINES_CACHE:
        lines = _file_to_lines(path)
        OVERRIDE_LINES_CACHE[path] = lines
    return OVERRIDE_LINES_CACHE[path]


def get_extra_context():
    """Return an extra context by calling an external configured python func.

    Returns:
        (dict) A dict of extra context key/values as strings.

    """
    extra_context_f = Config.extra_context_func
    if extra_context_f is None:
        return {}
    extra_context = extra_context_f()  # pylint: disable=E1120
    if not isinstance(extra_context, dict):
        print("bad extra_context (not a dict) => ignoring", file=sys.stderr)
        return {}
    return extra_context


def get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note:
      - first we search in override_dict, if there is a match, it's over
      - (if no match) at first step, we check each files in override_files
        configuration. The first match wins.
      - if there is no match, we return the default level number.

    Note: the result is cached in memory.

    Args:
        logger_name (string): The logger name.

    Returns:
        (int) The level number to use for this logger name.

    """
    global LEVEL_FROM_LOGGER_NAME_CACHE

    class Found(Exception):
        pass

    if logger_name not in LEVEL_FROM_LOGGER_NAME_CACHE:
        # pylint: disable=no-member
        for k, v in Config.override_dict.items():
            if fnmatch.fnmatch(logger_name, k):
                LEVEL_FROM_LOGGER_NAME_CACHE[logger_name] = \
                    level_name_to_level_no(v)
                return LEVEL_FROM_LOGGER_NAME_CACHE[logger_name]
        paths = Config.override_files
        try:
            for path in paths:  # pylint: disable=E1133
                custom_lines = _get_override_lines(path)
                for k, v in custom_lines:
                    if fnmatch.fnmatch(logger_name, k):
                        LEVEL_FROM_LOGGER_NAME_CACHE[logger_name] = \
                            level_name_to_level_no(v)
                        raise Found
        except Found:
            pass
        else:
            LEVEL_FROM_LOGGER_NAME_CACHE[logger_name] = \
                level_name_to_level_no(Config.minimal_level)
    return LEVEL_FROM_LOGGER_NAME_CACHE[logger_name]


def get_resolved_fancy_output_config_value(f=sys.stderr):
    fancy = Config.fancy_output
    if fancy is None:
        try:
            fancy = f.isatty()
        except Exception:
            fancy = False
    return fancy


def dump_locals(f=sys.stderr):
    fancy = get_resolved_fancy_output_config_value(f=f)
    stack_offset = -1
    try:
        caller = inspect.stack()[stack_offset]
        locals_map = {
            key: value
            for key, value in caller.frame.f_locals.items()
            if not key.startswith("__")
        }
        for k, v in locals_map.items():
            if len(repr(v)) > 10000:
                locals_map[k] = \
                    "(too big value => hidden in this variables dump)"
        if fancy:
            c = Console(file=sys.stderr)
            c.print(tabulate_mapping(locals_map, title="Locals"))
        else:
            print("Locals dump", file=f)
            for k, v in locals_map.items():
                print("%s: %r" % (k, v))
    except Exception:
        return False
    return True
