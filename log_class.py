#!/usr/bin/env python3
#
# $Id: log_class.py,v 1.1 2024/12/19 15:30:00 bob Exp $
# Raspberry Pi Internet Radio Logging class
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
# Log levels are :
#   CRITICAL 50
#   ERROR 40
#   WARNING 30
#   INFO 20
#   DEBUG 10
#   NOTSET 0
#
#  See https://docs.python.org/2/library/logging.html
#

import configparser
import logging
import sys

config = configparser.ConfigParser()

ConfigFile = "/etc/radiod.conf"


class Log:

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NONE = 0

    module = ""  # Module name for log entries
    loglevel = logging.INFO
    sMessage = ""  # Duplicate message prevention

    def __init__(self):
        return

    def init(self, module: str, console_output: bool = False) -> None:
        """Initialise log and set module name (usually "radio")."""
        self.module = module
        self.loglevel = self.getConfig()
        self._console_output = console_output
        if console_output:
            logger = logging.getLogger("gipiod")
            logger.setLevel(logging.DEBUG)
            logger.addHandler(
                _console_handler(
                    "stdout",
                    "DEBUG",
                    True,
                    "%(color_on)s[%(levelname)-8s] [%(filename)-20s]%(color_off)s %(message)s",
                )
            )

    def getName(self) -> str:
        """Get module name (usually "radio") to check if initialised."""
        return self.module

    def message(self, message: str, level: int) -> None:
        """Print message."""
        if level != self.NONE and message != self.sMessage:
            try:
                logger = logging.getLogger("gipiod")
                hdlr = logging.FileHandler("/var/log/radiod/" + self.module + ".log")
                formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
                hdlr.setFormatter(formatter)
                logger.addHandler(hdlr)
                logger.setLevel(self.loglevel)

                # write to log
                if level == self.CRITICAL:
                    logger.critical(message)
                elif level == self.ERROR:
                    logger.error(message)
                elif level == self.WARNING:
                    logger.warning(message)
                elif level == self.INFO:
                    logger.info(message)
                elif level == self.DEBUG:
                    logger.debug(message)

                logger.removeHandler(hdlr)
                hdlr.close()
                self.sMessage = message

            except Exception as e:
                print(str(e))
        return

    # Truncate the log file
    def truncate(self):
        logging.FileHandler("/var/log/radiod/" + self.module + ".log", "w")
        return

    # Temporary set log level
    def setLevel(self, level):
        self.loglevel = level
        return

    # Get the log level from the configuration file
    def getLevel(self):
        return self.loglevel

    # Get configuration loglevel option
    def getConfig(self):
        section = "RADIOD"
        option = "loglevel"
        strLogLevel = "INFO"

        # Get loglevel option
        config.read(ConfigFile)
        try:
            strLogLevel = config.get(section, option)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section), "in", ConfigFile
            self.message(msg, self.ERROR)

        if strLogLevel == "CRITICAL":
            loglevel = self.CRITICAL
        elif strLogLevel == "ERROR":
            loglevel = self.ERROR
        elif strLogLevel == "WARNING":
            loglevel = self.WARNING
        elif strLogLevel == "INFO":
            loglevel = self.INFO
        elif strLogLevel == "DEBUG":
            loglevel = self.DEBUG
        elif strLogLevel == "NONE":
            loglevel = self.NONE
        else:
            loglevel = self.INFO
        return loglevel


def _console_handler(
    output: str, level: str, color: bool, line_template: str
) -> logging.Handler:
    """Set up the console handler."""
    output_stream = sys.stdout if output.lower() == "stdout" else sys.stderr
    console_handler = logging.StreamHandler(output_stream)
    console_handler.setLevel(level.upper())
    console_formatter = LogFormatter(fmt=line_template, color=color)
    console_handler.setFormatter(console_formatter)
    return console_handler


class LogFormatter(logging.Formatter):
    """Logging formatter supporting colorized output."""

    COLOR_CODES = {
        # bright/bold magenta
        logging.CRITICAL: "\033[1;35m",
        # bright/bold red
        logging.ERROR: "\033[1;31m",
        # bright/bold yellow
        logging.WARNING: "\033[1;33m",
        # white / light gray
        logging.INFO: "\033[0;37m",
        # bright/bold black / dark gray
        logging.DEBUG: "\033[1;30m",
    }

    RESET_CODE = "\033[0m"

    def __init__(self, color: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.color = color

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        if self.color and record.levelno in self.COLOR_CODES:
            record.color_on = self.COLOR_CODES[record.levelno]
            record.color_off = self.RESET_CODE
        else:
            record.color_on = ""
            record.color_off = ""
        return super().format(record, *args, **kwargs)
