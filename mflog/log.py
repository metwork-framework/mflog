#!/bin/env python3

import argparse
from mflog import get_logger


def main():
    parser = argparse.ArgumentParser("log a message with standard metwork "
                                     "logging system")
    parser.add_argument('--application-name', '-a', action="store",
                        default="default", help="application name")
    parser.add_argument('LEVEL', action='store',
                        help="Log level",
                        choices=['ERROR', 'CRITICAL', 'WARNING', 'INFO',
                                 'DEBUG'])
    parser.add_argument('MESSAGE', action='store', help="message to log")
    options = parser.parse_args()

    logger = get_logger(options.application_name)
    if options.LEVEL == 'DEBUG':
        logger.debug(options.MESSAGE)
    elif options.LEVEL == 'INFO':
        logger.info(options.MESSAGE)
    elif options.LEVEL == 'WARNING':
        logger.warning(options.MESSAGE)
    elif options.LEVEL == 'CRITICAL':
        logger.critical(options.MESSAGE)
    elif options.LEVEL == 'ERROR':
        logger.error(options.MESSAGE)
    else:
        raise Exception("Bad message level: %s", options.LEVEL)


if __name__ == "__main__":
    main()
