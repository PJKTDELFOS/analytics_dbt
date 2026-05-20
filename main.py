from engine_processamento_duck_db.config import Config
from engine_processamento_duck_db.connection_params import DBConnectionParams
from engine_processamento_duck_db.database_manager import DatabaseConnector
from engine_processamento_duck_db.data_extractor import DataExtractor
from engine_processamento_duck_db.data_transform import DataTransformer
from engine_processamento_duck_db.duck_db_loader import DuckDBLoader


class Pipeline:
    """
    Orquestra as 4 etapas do pipeline de dados.
    Não contém lógica de negócio — só coordena as classes.
    Troca qualquer etapa sem impacto nas demais.
    """

    def __init__(self, incremental: bool = False):
        self._incremental = incremental

    def run(self) -> None:
        print("=" * 55)
        print("  PIPELINE — PostgreSQL → DuckDB")
        print("=" * 55)

        # 1. Parâmetros de conexão
        print("\n[1/4] Configurando conexão...")
        params = DBConnectionParams.from_local()

        # 2. Extração
        print("\n[2/4] Extraindo dados do PostgreSQL...")
        with DatabaseConnector(params) as db:
            extractor = DataExtractor(db)

            if Config.DEBUG:
                df_raw = extractor.extract_sample(500)
            else:
                df_raw = extractor.extract()

        # 3. Transformação
        print("\n[3/4] Transformando dados...")
        transformer = DataTransformer(df_raw)
        df_transformed = transformer.transform()

        # 4. Carga no DuckDB
        print("\n[4/4] Carregando no DuckDB...")
        loader = DuckDBLoader()

        if self._incremental:
            loader.load_incremental(df_transformed)
        else:
            loader.load(df_transformed)

        print("\n" + "=" * 55)
        print("  Pipeline concluído com sucesso.")
        print("=" * 55)


if __name__ == "__main__":
    pipeline = Pipeline(incremental=False)
    pipeline.run()