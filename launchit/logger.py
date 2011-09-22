"""
Common interface for propagating logable messages.
"""
import logging

# Name to use for the `LOGGER`
DEFAULT_LOGGER_NAME = 'Launchit'

def get_console_logger(name, format='%(name)s: [%(levelname)s] %(message)s'):
    """
    Return a logger with the given `name`, which is able to write messages to 
    a terminal's `stderr`-stream by using the given `format`. See the `logging`
    module's documentation for details.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(format)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

# Used for access on module-level by `info()`, `warning()` and `error()` in 
# order to provide a simplified way for other modules, when they need to show 
# status messages. A `logging`-compatible object is expected here.
LOGGER = get_console_logger(DEFAULT_LOGGER_NAME)

# Flag to indicate whether logging should be done
SHOULD_LOG = False

def _log(level, message):
    """
    Log `message` with `level` on `LOGGER` if `SHOULD_LOG` is `True`.
    """
    if SHOULD_LOG:
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
