import os
from dotenv import load_dotenv

load_dotenv()


def _require(key:str)->str:
    value=os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Variável de ambiente obrigatória '{key}' não está definida. "
            f"Verifique o arquivo .env"
        )
    return value



class Config:
    dbname= _require("DB_NAME")
    user= _require("DB_USER")
    password= _require("DB_PASSWORD")
    host= _require("DB_HOST")
    port =_require("DB_PORT")

    DUCKDB_PATH = os.getenv("DUCKDB_PATH", "licitacoes.duckdb")
    GEMINI_API_KEY=_require("GEMINI_API_KEY")
    # DEBUG = False

    # RESEND_API_KEY = _require('RESEND_API_KEY')
    # EMAIL_RESEND_FROM = _require('EMAIL_FROM_RESEND')

    # GMAIL_EMAIL_FROM=_require('USER_GMAIL')
    # GMAIL_PASSWORD=_require('GMAIL_KEY')

    DEBUG= os.getenv('DEBUG', 'False') == 'True'




