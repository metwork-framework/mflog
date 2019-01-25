# -*- coding: utf-8 -*-

import os
import six
import fnmatch
import logging
import hashlib

MFCOM_HOME = os.environ.get('MFCOM_HOME', None)
MODULE_HOME = os.environ.get('MODULE_HOME', None)
MFCOM_OVERRIDE_LINES_CACHE = None
MODULE_OVERRIDE_LINES_CACHE = None
CUSTOM_OVERRIDE_LINES_CACHE = None
CUSTOM_OVERRIDE_FILE = None
LEVEL_FROM_LOGGER_NAME_CACHE = {}
MODULE = os.environ.get('MODULE', 'UNKNOWN')


class classproperty(object):

    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class Config(object):

    _instance = None
    _instance_hash = None
    _default_level = None
    _json_default_level = None
    _json_file = None

    def __init__(self, default_level=None, json_default_level=None,
                 json_file=None):
        global MFCOM_OVERRIDE_LINES_CACHE, MODULE_OVERRIDE_LINES_CACHE, \
            LEVEL_FROM_LOGGER_NAME_CACHE, CUSTOM_OVERRIDE_LINES_CACHE, \
            CUSTOM_OVERRIDE_FILE
        MFCOM_OVERRIDE_LINES_CACHE = None
        MODULE_OVERRIDE_LINES_CACHE = None
        CUSTOM_OVERRIDE_LINES_CACHE = None
        CUSTOM_OVERRIDE_FILE = None
        LEVEL_FROM_LOGGER_NAME_CACHE = {}
        if default_level is not None:
            self._default_level = default_level
        else:
            self._default_level = os.environ.get('MFLOG_DEFAULT_LEVEL', None)
            if self._default_level is None:
                self._default_level = \
                    os.environ.get('%s_LOG_DEFAULT_LEVEL' % MODULE, 'INFO')
        if json_default_level is not None:
            self._json_default_level = json_default_level
        else:
            self._json_default_level = \
                os.environ.get('MFLOG_JSON_DEFAULT_LEVEL', None)
            if self._json_default_level is None:
                self._json_default_level = \
                    os.environ.get('%s_LOG_ADMIN_DEFAULT_LEVEL' % MODULE,
                                   'WARNING')
        if json_file is not None:
            self._json_file = os.environ.get("MFLOG_JSON_FILE", None)
            if self._json_file is None:
                self._json_file = os.environ.get('%s_LOG_ADMIN_FILE' % MODULE,
                                                 None)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def set_instance(cls, *args, **kwargs):
        key = str(args + tuple(sorted(kwargs.items())))
        if six.PY2:
            h = hashlib.md5(key).hexdigest
        else:
            h = hashlib.md5(key.encode('utf8')).hexdigest()
        if cls._instance_hash == h:
            return False
        cls._instance = Config(*args, **kwargs)
        cls._instance_hash = h
        return True

    @classproperty
    def default_level(cls):  # pylint: disable=E0213
        return cls.get_instance()._default_level

    @classproperty
    def json_default_level(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_default_level

    @classproperty
    def json_file(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_file


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


def __file_to_lines(file_path):
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


def _get_mfcom_override_lines():
    """Read the mfcom mflog_override.conf file (if exists).

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global MFCOM_OVERRIDE_LINES_CACHE
    if MFCOM_OVERRIDE_LINES_CACHE is None:
        lines = []
        if MFCOM_HOME:
            lines = __file_to_lines("%s/config/mflog_override.conf" %
                                    MFCOM_HOME)
        MFCOM_OVERRIDE_LINES_CACHE = lines
    return MFCOM_OVERRIDE_LINES_CACHE


def _get_module_override_lines():
    """Read the current module mflog_override.conf file (if exists).

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global MODULE_OVERRIDE_LINES_CACHE
    if MODULE_OVERRIDE_LINES_CACHE is None:
        lines = []
        if MODULE_HOME:
            lines = __file_to_lines("%s/config/mflog_override.conf" %
                                    MODULE_HOME)
        MODULE_OVERRIDE_LINES_CACHE = lines
    return MODULE_OVERRIDE_LINES_CACHE


def _get_custom_override_lines():
    """Read the custom mflog_override configuration file (if exists).

    The full path of the file is given by the MFLOG_OVERRIDE_FILE env var.

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global CUSTOM_OVERRIDE_LINES_CACHE, CUSTOM_OVERRIDE_FILE
    f = os.environ.get("MFLOG_OVERRIDE_FILE", None)
    if CUSTOM_OVERRIDE_LINES_CACHE is None or CUSTOM_OVERRIDE_FILE != f:
        lines = []
        if f is not None:
            lines = __file_to_lines(f)
        CUSTOM_OVERRIDE_LINES_CACHE = lines
        CUSTOM_OVERRIDE_FILE = f
    return CUSTOM_OVERRIDE_LINES_CACHE


def _get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check first the current module mflog_override.conf file
        then the mfcom mflog_override.conf file then we return
        the default level number. The first match wins.

    Args:
        logger_name (string): The logger name.

    Returns:
        (int) The level number to use for this logger name.

    """
    custom_lines = _get_custom_override_lines()
    for k, v in custom_lines:
        if fnmatch.fnmatch(logger_name, k):
            return level_name_to_level_no(v)
    module_lines = _get_module_override_lines()
    for k, v in module_lines:
        if fnmatch.fnmatch(logger_name, k):
            return level_name_to_level_no(v)
    mfcom_lines = _get_mfcom_override_lines()
    for k, v in mfcom_lines:
        if fnmatch.fnmatch(logger_name, k):
            return level_name_to_level_no(v)
    return level_name_to_level_no(Config.default_level)


def get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check first the current module mflog_override.conf file
        then the mfcom mflog_override.conf file then we return
        the default level number. The first match wins.

    Note: the result is cached in memory.

    Args:
        logger_name (string): The logger name.

    Returns:
        (int) The level number to use for this logger name.

    """
    global LEVEL_FROM_LOGGER_NAME_CACHE
    if logger_name not in LEVEL_FROM_LOGGER_NAME_CACHE:
        LEVEL_FROM_LOGGER_NAME_CACHE[logger_name] = \
            _get_level_no_from_logger_name(logger_name)
    return LEVEL_FROM_LOGGER_NAME_CACHE[logger_name]


def _get_admin_default_level_no():
    return level_name_to_level_no(Config.json_default_level)


def _get_admin_file():
    return Config.json_file
