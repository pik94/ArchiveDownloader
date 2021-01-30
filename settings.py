import logging
from logging.config import dictConfig
from pathlib import Path
from typing import NoReturn, Optional


class ServerSettings:
    # An interval between sending a chunk of data to a client
    DELAY = 0.5

    # How many data is sent to a clint (in Kb)
    CHUNK_SIZE = 100

    # A directory path to all photos
    STORAGE_PATH = 'test_photos'


def set_logger_settings(log_file: str,
                        level: Optional[int] = logging.DEBUG) -> NoReturn:
    log_file = Path(log_file)
    log_file.parent.mkdir(exist_ok=True, parents=True)
    config = dict(
        version=1,
        formatters={
            # For files
            'detailed': {
                'format': '%(asctime)s %(levelname)-8s %(message)s'
            },
            # For the console
            'console': {
                'format': '%(asctime)s [%(levelname)s] %(message)s'}
        },
        handlers={
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'console',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': level,
                'formatter': 'detailed',
                'filename': log_file,
                'mode': 'a',
                'maxBytes': 1048576,  # 1 MB
                # 'maxBytes': 10485760,  # 10 MB
                'backupCount': 5
            }
        },
        root={
            'handlers': ['console', 'file'],
            'level': level,
        },
        disable_existing_loggers=False
    )
    dictConfig(config)
