# -*- coding: utf-8 -*-

import os
import fnmatch
import logging
import fcntl

OVERRIDE_LINES_CACHE = None
LEVEL_FROM_LOGGER_NAME_CACHE = {}

# metwork stuff
MFCOM_HOME = os.environ.get('MFCOM_HOME', None)
MODULE_HOME = os.environ.get('MODULE_HOME', None)
MODULE_RUNTIME_HOME = os.environ.get('MODULE_RUNTIME_HOME', None)
MODULE = os.environ.get('MODULE', 'UNKNOWN')


def write_with_lock(f, message):
    fcntl.flock(f, fcntl.LOCK_EX)
    f.write(message)


def flush_with_lock(f):
    f.flush()
    fcntl.flock(f, fcntl.LOCK_UN)


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

    def __init__(self, minimal_level=None, json_minimal_level=None,
                 json_file=None, override_files=None,
                 thread_local_context=False):
        global LEVEL_FROM_LOGGER_NAME_CACHE, OVERRIDE_LINES_CACHE
        OVERRIDE_LINES_CACHE = {}
        LEVEL_FROM_LOGGER_NAME_CACHE = {}
        if minimal_level is not None:
            self._minimal_level = minimal_level
        else:
            self._minimal_level = os.environ.get('MFLOG_MINIMAL_LEVEL', None)
            if self._minimal_level is None:
                # metwork mode
                self._minimal_level = \
                    os.environ.get('%s_LOG_MINIMAL_LEVEL' % MODULE, 'INFO')
        if json_minimal_level is not None:
            self._json_minimal_level = json_minimal_level
        else:
            self._json_minimal_level = \
                os.environ.get('MFLOG_JSON_MINIMAL_LEVEL', None)
            if self._json_minimal_level is None:
                # metwork mode
                self._json_minimal_level = \
                    os.environ.get('%s_LOG_JSON_MINIMAL_LEVEL' % MODULE,
                                   'WARNING')
        if json_file is not None:
            self._json_file = json_file
        else:
            self._json_file = os.environ.get("MFLOG_JSON_FILE", None)
            if self._json_file is None:
                # metwork mode
                self._json_file = os.environ.get('%s_LOG_JSON_FILE' % MODULE,
                                                 None)
            if self._json_file == "null":
                self._json_file = None
        if override_files is not None:
            self._override_files = override_files
        else:
            if "MFLOG_MINIMAL_LEVEL_OVERRIDE_FILES" in os.environ:
                self._override_files = \
                    [x.strip() for x in os.environ.get(
                        "MFLOG_MINIMAL_LEVEL_OVERRIDE_FILES", None).split(';')]
            else:
                # metwork mode
                self._override_files = []
                for env in MODULE_RUNTIME_HOME, MODULE_HOME, MFCOM_HOME:
                    if env:
                        self._override_files.append(
                            "%s/config/mflog_override.conf" % env
                        )

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
    def json_minimal_level(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_minimal_level

    @classproperty
    def json_file(cls):  # pylint: disable=E0213
        return cls.get_instance()._json_file

    @classproperty
    def override_files(cls):  # pylint: disable=E0213
        return cls.get_instance()._override_files


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


def get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check each files in override_files configuration. The first match
        wins. If there is no mathc, we return the default level number.

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
