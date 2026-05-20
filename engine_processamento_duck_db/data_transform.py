import json
import unicodedata
import pandas as pd
from engine_processamento_duck_db.config import Config


class DataTransformer:
    """
    Responsabilidade única: transformar o DataFrame bruto em dados estruturados.
    Não sabe de onde vieram os dados — recebe um DataFrame e devolve um DataFrame.
    Não sabe para onde vão os dados — só transforma e entrega.
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df.copy()

    def transform(self) -> pd.DataFrame:
        """
        Executa o pipeline completo de transformação.
        Retorna DataFrame limpo e estruturado, pronto para o DuckDBLoader.
        """
        if Config.DEBUG:
            print("[DataTransformer] Iniciando transformação...")

        self._parse_json()
        self._extract_json_fields()
        self._normalize_text()
        self._parse_dates()
        self._clean_values()
        self._drop_raw_json()
        self._reorder_columns()

        if Config.DEBUG:
            print(f"[DataTransformer] Transformação concluída — {len(self._df)} registros, {len(self._df.columns)} colunas.")

        return self._df

    # ── Etapas privadas ────────────────────────────────────────────────────

    def _parse_json(self) -> None:
        """Garante que dados_json é dict — pode vir como string do PostgreSQL."""
        def to_dict(val):
            if isinstance(val, str):
                return json.loads(val)
            return val if val else {}

        self._df["dados_json"] = self._df["dados_json"].apply(to_dict)

    def _extract_json_fields(self) -> None:
        """Extrai campos relevantes do payload JSONB para colunas individuais."""
        j = self._df["dados_json"]

        # Campos diretos
        self._df["numero_controle_pncp"]   = j.apply(lambda x: x.get("numeroControlePNCP"))
        self._df["objeto_compra"]          = j.apply(lambda x: x.get("objetoCompra"))
        self._df["modalidade_nome"]        = j.apply(lambda x: x.get("modalidadeNome"))
        self._df["modalidade_id"]          = j.apply(lambda x: x.get("modalidadeId"))
        self._df["situacao_compra_nome"]   = j.apply(lambda x: x.get("situacaoCompraNome"))
        self._df["valor_total_estimado"]   = j.apply(lambda x: x.get("valorTotalEstimado"))
        self._df["valor_total_homologado"] = j.apply(lambda x: x.get("valorTotalHomologado"))
        self._df["data_abertura_proposta"] = j.apply(lambda x: x.get("dataAberturaProposta"))
        self._df["data_encerramento"]      = j.apply(lambda x: x.get("dataEncerramentoProposta"))
        self._df["data_publicacao_pncp"]   = j.apply(lambda x: x.get("dataPublicacaoPncp"))
        self._df["ano_compra"]             = j.apply(lambda x: x.get("anoCompra"))
        self._df["numero_compra"]          = j.apply(lambda x: x.get("numeroCompra"))
        self._df["processo"]               = j.apply(lambda x: x.get("processo"))
        self._df["srp"]                    = j.apply(lambda x: x.get("srp"))
        self._df["modo_disputa_nome"]      = j.apply(lambda x: x.get("modoDisputaNome"))
        self._df["link_sistema_origem"]    = j.apply(lambda x: x.get("linkSistemaOrigem"))

        # Campos aninhados — órgão
        self._df["orgao_cnpj"]         = j.apply(lambda x: x.get("orgaoEntidade", {}).get("cnpj"))
        self._df["orgao_razao_social"]  = j.apply(lambda x: x.get("orgaoEntidade", {}).get("razaoSocial"))
        self._df["orgao_esfera"]        = j.apply(lambda x: x.get("orgaoEntidade", {}).get("esferaId"))
        self._df["orgao_poder"]         = j.apply(lambda x: x.get("orgaoEntidade", {}).get("poderId"))

        # Campos aninhados — unidade
        self._df["municipio"]  = j.apply(lambda x: x.get("unidadeOrgao", {}).get("municipioNome"))
        self._df["uf_nome"]    = j.apply(lambda x: x.get("unidadeOrgao", {}).get("ufNome"))

        # Amparo legal
        self._df["amparo_legal_nome"] = j.apply(
            lambda x: x.get("amparoLegal", {}).get("nome")
            if x.get("amparoLegal") else None
        )

    def _normalize_text(self) -> None:
        """
        Normaliza colunas de texto — remove acentos, strip, uppercase onde aplicável.
        Mesmo padrão usado no Appa para matching de palavras-chave.
        """
        def normalize(val):
            if not isinstance(val, str):
                return val
            val = val.strip()
            return unicodedata.normalize("NFD", val)

        text_cols = ["objeto", "objeto_compra", "orgao_razao_social", "municipio"]
        for col in text_cols:
            if col in self._df.columns:
                self._df[col] = self._df[col].apply(normalize)

        # UF sempre maiúscula
        if "uf" in self._df.columns:
            self._df["uf"] = self._df["uf"].str.upper().str.strip()

    def _parse_dates(self) -> None:
        """Converte colunas de data para datetime."""
        date_cols = [
            "data_coleta",
            "data_abertura_proposta",
            "data_encerramento",
            "data_publicacao_pncp",
        ]
        for col in date_cols:
            if col in self._df.columns:
                self._df[col] = pd.to_datetime(self._df[col], errors="coerce")

    def _clean_values(self) -> None:
        """Limpa valores numéricos — substitui None por 0.0 onde aplicável."""
        numeric_cols = ["valor_total_estimado", "valor_total_homologado"]
        for col in numeric_cols:
            if col in self._df.columns:
                self._df[col] = pd.to_numeric(self._df[col], errors="coerce").fillna(0.0)

    def _drop_raw_json(self) -> None:
        """Remove o JSON bruto — dados já foram extraídos para colunas."""
        if "dados_json" in self._df.columns:
            self._df = self._df.drop(columns=["dados_json"])

    def _reorder_columns(self) -> None:
        """Reordena colunas — identificadores primeiro, dados depois."""
        priority = [
            "id",
            "numero_controle_pncp",
            "identificador_certame",
            "ano_compra",
            "uf",
            "uf_nome",
            "municipio",
            "orgao_cnpj",
            "orgao_razao_social",
            "orgao_esfera",
            "orgao_poder",
            "modalidade_id",
            "modalidade_nome",
            "situacao_compra_nome",
            "objeto",
            "objeto_compra",
            "valor_total_estimado",
            "valor_total_homologado",
            "srp",
            "modo_disputa_nome",
            "processo",
            "numero_compra",
            "amparo_legal_nome",
            "data_publicacao_pncp",
            "data_abertura_proposta",
            "data_encerramento",
            "data_coleta",
            "link_sistema_origem",
        ]
        # Só reordena colunas que existem — sem quebrar se faltar alguma
        ordered = [c for c in priority if c in self._df.columns]
        remaining = [c for c in self._df.columns if c not in ordered]
        self._df = self._df[ordered + remaining]