import pandas as pd
from engine_processamento_duck_db.database_manager import DatabaseConnector
from engine_processamento_duck_db.config import Config


class DataExtractor:
    """
    Responsabilidade única: extrair dados do PostgreSQL e retornar um DataFrame.
    Não sabe de onde vem a conexão — recebe um DatabaseConnector pronto.
    Não sabe o que fazer com os dados — só extrai e entrega.
    """

    QUERY = """
        SELECT
            id,
            data_coleta,
            identificador_certame,
            uf,
            objeto,
            dados_json
        FROM pncp_dados_brutos
        ORDER BY id
    """

    def __init__(self, db: DatabaseConnector):
        self._db = db

    def extract(self) -> pd.DataFrame:
        """
        Extrai todos os registros da tabela pncp_dados_brutos.
        Retorna um DataFrame pandas com os dados brutos.
        """
        if Config.DEBUG:
            print("[DataExtractor] Iniciando extração...")

        with self._db.get_connection() as conn:
            df = pd.read_sql(self.QUERY, conn)

        if Config.DEBUG:
            print(f"[DataExtractor] {len(df)} registros extraídos.")

        return df

    def extract_by_uf(self, uf: str) -> pd.DataFrame:
        """
        Extrai registros filtrados por UF.
        Útil para extrações parciais e testes.
        """
        query = f"""
            SELECT
                id,
                data_coleta,
                identificador_certame,
                uf,
                objeto,
                dados_json
            FROM pncp_dados_brutos
            WHERE uf = %(uf)s
            ORDER BY id
        """
        if Config.DEBUG:
            print(f"[DataExtractor] Extraindo registros da UF: {uf}")

        with self._db.get_connection() as conn:
            df = pd.read_sql(query, conn, params={"uf": uf})

        if Config.DEBUG:
            print(f"[DataExtractor] {len(df)} registros extraídos para UF {uf}.")

        return df

    def extract_sample(self, limit: int = 100) -> pd.DataFrame:
        """
        Extrai uma amostra limitada — útil para desenvolvimento e testes.
        """
        query = f"""
            SELECT
                id,
                data_coleta,
                identificador_certame,
                uf,
                objeto,
                dados_json
            FROM pncp_dados_brutos
            ORDER BY id
            LIMIT %(limit)s
        """
        if Config.DEBUG:
            print(f"[DataExtractor] Extraindo amostra de {limit} registros...")

        with self._db.get_connection() as conn:
            df = pd.read_sql(query, conn, params={"limit": limit})

        if Config.DEBUG:
            print(f"[DataExtractor] {len(df)} registros na amostra.")

        return df