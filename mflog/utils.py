# -*- coding: utf-8 -*-

import os
import fnmatch
import logging

MFCOM_HOME = os.environ.get('MFCOM_HOME', None)
MODULE_HOME = os.environ.get('MODULE_HOME', None)
MFCOM_OVERRIDE_LINES_CACHE = None
MODULE_OVERRIDE_LINES_CACHE = None
LEVEL_FROM_LOGGER_NAME_CACHE = {}
MODULE = os.environ.get('MODULE', 'UNKNOWN')
DEFAULT_LEVEL = os.environ.get('%s_LOG_DEFAULT_LEVEL' % MODULE, 'INFO')


def _level_name_to_level_no(level_name):
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
    """Read the given file_path and decode python_logging_override format.

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
    """Read the mfcom python_logging_override.conf file (if exists).

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global MFCOM_OVERRIDE_LINES_CACHE
    if MFCOM_OVERRIDE_LINES_CACHE is None:
        lines = []
        if MFCOM_HOME:
            lines = __file_to_lines("%s/config/python_logging_override.conf" %
                                    MFCOM_HOME)
        MFCOM_OVERRIDE_LINES_CACHE = lines
    return MFCOM_OVERRIDE_LINES_CACHE


def _get_module_override_lines():
    """Read the current module python_logging_override.conf file (if exists).

    Note: the content is cached (in memory).

    Returns:
        (list of couples) A list of (logger name pattern, level name).

    """
    global MODULE_OVERRIDE_LINES_CACHE
    if MODULE_OVERRIDE_LINES_CACHE is None:
        lines = []
        if MODULE_HOME:
            lines = __file_to_lines("%s/config/python_logging_override.conf" %
                                    MODULE_HOME)
        MODULE_OVERRIDE_LINES_CACHE = lines
    return MODULE_OVERRIDE_LINES_CACHE


def __get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check first the current module python_logging_override.conf file
        then the mfcom python_logging_override.conf file then we return
        the default level number. The first match wins.

    Args:
        logger_name (string): The logger name.

    Returns:
        (int) The level number to use for this logger name.

    """
    module_lines = _get_module_override_lines()
    for k, v in module_lines:
        if fnmatch.fnmatch(logger_name, k):
            return _level_name_to_level_no(v)
    mfcom_lines = _get_mfcom_override_lines()
    for k, v in mfcom_lines:
        if fnmatch.fnmatch(logger_name, k):
            return _level_name_to_level_no(v)
    return _level_name_to_level_no(DEFAULT_LEVEL)


def _get_level_no_from_logger_name(logger_name):
    """Get the level number to use for the given logger name.

    Note: we check first the current module python_logging_override.conf file
        then the mfcom python_logging_override.conf file then we return
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
            __get_level_no_from_logger_name(logger_name)
    return LEVEL_FROM_LOGGER_NAME_CACHE[logger_name]
