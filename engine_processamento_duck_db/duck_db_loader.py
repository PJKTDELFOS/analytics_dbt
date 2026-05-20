import duckdb
import pandas as pd
from engine_processamento_duck_db.config import Config


class DuckDBLoader:
    """
    Responsabilidade única: carregar o DataFrame transformado no DuckDB.
    Não sabe de onde vieram os dados — recebe um DataFrame pronto.
    Não sabe como os dados foram transformados — só carrega e persiste.
    Cria o arquivo .duckdb automaticamente se não existir.
    """

    TABLE_NAME = "raw_licitacoes"

    def __init__(self, duckdb_path: str = None):
        self._path = duckdb_path or Config.DUCKDB_PATH

    def load(self, df: pd.DataFrame) -> None:
        """
        Carrega o DataFrame no DuckDB.
        Recria a tabela a cada execução — idempotente.
        """
        if Config.DEBUG:
            print(f"[DuckDBLoader] Conectando ao DuckDB: {self._path}")

        with duckdb.connect(self._path) as con:
            self._create_schema(con)
            self._load_data(con, df)
            self._validate(con)

    def load_incremental(self, df: pd.DataFrame) -> None:
        """
        Carga incremental — insere apenas registros novos pelo id.
        Útil para execuções subsequentes sem reprocessar tudo.
        """
        if Config.DEBUG:
            print(f"[DuckDBLoader] Carga incremental — {len(df)} registros recebidos.")

        with duckdb.connect(self._path) as con:
            # Cria tabela se não existir
            if not self._table_exists(con):
                if Config.DEBUG:
                    print(f"[DuckDBLoader] Tabela não existe — criando...")
                self._create_schema(con)
                self._load_data(con, df)
            else:
                # Insere só os ids que ainda não existem
                con.register("df_novos", df)
                con.execute(f"""
                    INSERT INTO {self.TABLE_NAME}
                    SELECT * FROM df_novos
                    WHERE id NOT IN (
                        SELECT id FROM {self.TABLE_NAME}
                    )
                """)
                total = con.execute(
                    f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
                ).fetchone()[0]

                if Config.DEBUG:
                    print(f"[DuckDBLoader] Total na tabela após incremental: {total}")

    # ── Métodos privados ───────────────────────────────────────────────────

    def _create_schema(self, con: duckdb.DuckDBPyConnection) -> None:
        """Recria a tabela com schema explícito."""
        con.execute(f"DROP TABLE IF EXISTS {self.TABLE_NAME}")
        con.execute(f"""
            CREATE TABLE {self.TABLE_NAME} (
                id                      INTEGER,
                numero_controle_pncp    VARCHAR,
                identificador_certame   VARCHAR,
                ano_compra              INTEGER,
                uf                      VARCHAR,
                uf_nome                 VARCHAR,
                municipio               VARCHAR,
                orgao_cnpj              VARCHAR,
                orgao_razao_social      VARCHAR,
                orgao_esfera            VARCHAR,
                orgao_poder             VARCHAR,
                modalidade_id           INTEGER,
                modalidade_nome         VARCHAR,
                situacao_compra_nome    VARCHAR,
                objeto                  VARCHAR,
                objeto_compra           VARCHAR,
                valor_total_estimado    DOUBLE,
                valor_total_homologado  DOUBLE,
                srp                     BOOLEAN,
                modo_disputa_nome       VARCHAR,
                processo                VARCHAR,
                numero_compra           VARCHAR,
                amparo_legal_nome       VARCHAR,
                data_publicacao_pncp    TIMESTAMP,
                data_abertura_proposta  TIMESTAMP,
                data_encerramento       TIMESTAMP,
                data_coleta             TIMESTAMP,
                link_sistema_origem     VARCHAR
            )
        """)

    def _load_data(self, con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
        """Registra o DataFrame e insere na tabela."""
        con.register("df_transformed", df)
        con.execute(f"""
            INSERT INTO {self.TABLE_NAME}
            SELECT * FROM df_transformed
        """)

    def _validate(self, con: duckdb.DuckDBPyConnection) -> None:
        """Valida a carga — conta registros e imprime amostra no DEBUG."""
        total = con.execute(
            f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
        ).fetchone()[0]

        print(f"[DuckDBLoader] {total} registros carregados em '{self.TABLE_NAME}'.")

        if Config.DEBUG:
            print("\n[DuckDBLoader] Amostra dos dados carregados:")
            amostra = con.execute(
                f"""
                SELECT
                    id,
                    uf,
                    orgao_razao_social,
                    modalidade_nome,
                    valor_total_estimado,
                    data_encerramento
                FROM {self.TABLE_NAME}
                LIMIT 5
                """
            ).fetchdf()
            print(amostra.to_string(index=False))

    def _table_exists(self, con: duckdb.DuckDBPyConnection) -> bool:
        """Verifica se a tabela já existe no DuckDB."""
        result = con.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{self.TABLE_NAME}'
        """).fetchone()[0]
        return result > 0