import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from engine_processamento_duck_db.config import Config
from engine_processamento_duck_db.connection_params import DBConnectionParams


class DatabaseConnector:
    """
    Responsabilidade única: gerenciar o pool de conexões com PostgreSQL.
    Recebe DBConnectionParams por injeção — não sabe de onde vieram os parâmetros.
    Troca de banco = troca o objeto DBConnectionParams. Zero alteração aqui.
    """

    def __init__(self, params: DBConnectionParams):
        self._params = params
        self._pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=params.host,
            port=params.port,
            dbname=params.dbname,
            user=params.user,
            password=params.password,
            client_encoding="UTF8",
            connect_timeout=10,
        )
        if Config.DEBUG:
            print(f"[DatabaseConnector] Pool criado — {params.host}:{params.port}/{params.dbname}")

    @contextmanager
    def get_connection(self):
        """
        Context manager — pega conexão do pool e devolve ao finalizar.
        Faz rollback automático em caso de erro.
        """
        conn = self._pool.getconn()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._pool.putconn(conn)

    def close_pool(self) -> None:
        """Encerra todas as conexões do pool."""
        if self._pool:
            self._pool.closeall()
            if Config.DEBUG:
                print("[DatabaseConnector] Pool encerrado.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_pool()