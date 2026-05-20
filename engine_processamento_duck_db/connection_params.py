from dataclasses import dataclass
from engine_processamento_duck_db.config import Config


@dataclass(frozen=True)
class DBConnectionParams:
    """
    Value Object imutável com parâmetros de conexão.
    Não sabe conectar — só carrega e valida os parâmetros.
    frozen=True garante imutabilidade após criação.
    """
    host: str
    port: str
    dbname: str
    user: str
    password: str

    @classmethod
    def from_local(cls) -> "DBConnectionParams":
        """Parâmetros do banco local via Config."""
        return cls(
            host=Config.host,
            port=Config.port,
            dbname=Config.dbname,
            user=Config.user,
            password=Config.password,
        )

    @classmethod
    def from_custom(cls, host, port, dbname, user, password) -> "DBConnectionParams":
        """Parâmetros passados diretamente — máxima flexibilidade."""
        return cls(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )


