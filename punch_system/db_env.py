import os
from pathlib import Path

import pymysql


ENV_FILE = Path(__file__).resolve().parent / '.env'
_ENV_LOADED = False


def load_env_file():
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    if ENV_FILE.exists():
        for raw_line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('export '):
                line = line[len('export '):].strip()

            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]

            os.environ.setdefault(key, value)

    _ENV_LOADED = True


def _get_int_env(name, default):
    value = os.getenv(name)
    if value in (None, ''):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_db_name():
    load_env_file()
    return os.getenv('DB_NAME', 'student')


def get_db_config():
    load_env_file()
    return {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': _get_int_env('DB_PORT', 3306),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': get_db_name(),
        'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
        'cursorclass': pymysql.cursors.DictCursor,
    }


def get_db_connection():
    return pymysql.connect(**get_db_config())


def get_server_connection():
    config = get_db_config().copy()
    config.pop('database', None)
    return pymysql.connect(**config)
