"""
Common interface for propagating logable messages.
"""
import logging

def set_console_handler(logger, format):
    """
    Create a `logging.StreamHandler()`, which is able to write to `stderr` and 
    pass given `format` to that handler for output messages. Add the handler to 
    `logger` and return the logger.
    """
    handler = logging.StreamHandler()
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_logger(name, format='%(name)s: %(message)s'):
    """
    Request a logger from Python's `logging`-module by using the given `name`. 
    If the resulting logger object does already have at least one handler, it
    is returned unchanged. Otherwise a console handler will be added to it and 
    given `format` will be passed to that handler. In addition, logging level
    will be set to `logging.INFO`.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger = set_console_handler(logger, format)
        logger.setLevel(logging.INFO)
    return logger

# Used for access on module-level by `info()`, `warning()` and `error()` in 
# order to provide a simplified way for other modules, when they need to show 
# status messages. A `logging`-compatible object is expected here. When this
# is `None`, it is assumed, that no logging is desired.
LOGGER = None

def enable(name='Launchit'):
    """
    Enable logging by setting a logger with the given `name` as `LOGGER`.
    """
    global LOGGER
    LOGGER = get_logger(name)

def disable():
    """
    Disable logging. This is setting `LOGGER` to `None`.
    """
    global LOGGER
    LOGGER = None

def _log(level, message):
    """
    Log `message` with `level` on `LOGGER`. Do nothing, if `LOGGER` is `None`.
    """
    if LOGGER is not None:
        LOGGER.log(level, message)

def info(message):
    """
    Log a `message` with logging level `INFO` on the `LOGGER`.
    """
    _log(logging.INFO, message)

def warning(message):
    """
    Log a `message` with logging level `WARNING` on the `LOGGER`.
    """
    _log(logging.WARNING, message)

def error(message):
    """
    Log a `message` with logging level `ERROR` on the `LOGGER`.
    """
    _log(logging.ERROR, message)
