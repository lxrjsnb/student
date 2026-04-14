import os
import queue
import threading
from pathlib import Path

import pymysql


ENV_FILE = Path(__file__).resolve().parent / '.env'
_ENV_LOADED = False
_POOL = None
_POOL_LOCK = threading.Lock()


def _raise_clear_auth_dependency_error(exc):
    message = str(exc)
    if 'cryptography' in message and (
        'caching_sha2_password' in message or 'sha256_password' in message
    ):
        raise RuntimeError(
            "数据库账号使用了 MySQL 的 sha256/caching_sha2 认证，但当前 Python 环境未安装 "
            "`cryptography`。请先执行 `conda run -n check pip install cryptography` "
            "或重新安装 `requirements.txt` 中的依赖后再启动服务。"
        ) from exc
    raise exc


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


class _PooledConnection:
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn

    def close(self):
        if self._conn is None:
            return
        conn = self._conn
        self._conn = None
        self._pool.release(conn)

    def __getattr__(self, item):
        if self._conn is None:
            raise RuntimeError('database connection has been returned to the pool')
        return getattr(self._conn, item)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SimpleConnectionPool:
    def __init__(self, config, max_connections, min_cached, acquire_timeout):
        self._config = config
        self._max_connections = max(1, max_connections)
        self._min_cached = max(0, min(min_cached, self._max_connections))
        self._acquire_timeout = max(1, acquire_timeout)
        self._idle_connections = queue.LifoQueue(maxsize=self._max_connections)
        self._created_connections = 0
        self._lock = threading.Lock()

        for _ in range(self._min_cached):
            conn = self._create_raw_connection()
            self._idle_connections.put_nowait(conn)
            self._created_connections += 1

    def _create_raw_connection(self):
        try:
            return pymysql.connect(**self._config)
        except RuntimeError as exc:
            _raise_clear_auth_dependency_error(exc)

    def _discard_connection(self, conn):
        try:
            conn.close()
        except Exception:
            pass

        with self._lock:
            if self._created_connections > 0:
                self._created_connections -= 1

    def _prepare_connection(self, conn):
        try:
            conn.ping(reconnect=True)
            return conn
        except Exception:
            self._discard_connection(conn)
            return None

    def connection(self):
        while True:
            try:
                conn = self._idle_connections.get_nowait()
            except queue.Empty:
                conn = None

            if conn is not None:
                prepared = self._prepare_connection(conn)
                if prepared is not None:
                    return _PooledConnection(self, prepared)
                continue

            with self._lock:
                if self._created_connections < self._max_connections:
                    self._created_connections += 1
                    should_create = True
                else:
                    should_create = False

            if should_create:
                try:
                    return _PooledConnection(self, self._create_raw_connection())
                except Exception:
                    with self._lock:
                        self._created_connections -= 1
                    raise

            try:
                conn = self._idle_connections.get(timeout=self._acquire_timeout)
            except queue.Empty as exc:
                raise RuntimeError(
                    f'数据库连接池已耗尽，等待 {self._acquire_timeout} 秒仍未获取到连接'
                ) from exc

            prepared = self._prepare_connection(conn)
            if prepared is not None:
                return _PooledConnection(self, prepared)

    def release(self, conn):
        if conn is None:
            return

        try:
            conn.rollback()
        except Exception:
            self._discard_connection(conn)
            return

        try:
            conn.ping(reconnect=True)
        except Exception:
            self._discard_connection(conn)
            return

        try:
            self._idle_connections.put_nowait(conn)
        except queue.Full:
            self._discard_connection(conn)


def get_db_pool():
    global _POOL
    if _POOL is not None:
        return _POOL

    with _POOL_LOCK:
        if _POOL is not None:
            return _POOL

        _POOL = SimpleConnectionPool(
            config=get_db_config(),
            max_connections=_get_int_env('DB_POOL_MAX_CONNECTIONS', 100),
            min_cached=_get_int_env('DB_POOL_MIN_CACHED', 3),
            acquire_timeout=_get_int_env('DB_POOL_ACQUIRE_TIMEOUT', 10),
        )
        return _POOL


def get_db_connection():
    return get_db_pool().connection()


def get_server_connection():
    config = get_db_config().copy()
    config.pop('database', None)
    try:
        return pymysql.connect(**config)
    except RuntimeError as exc:
        _raise_clear_auth_dependency_error(exc)
