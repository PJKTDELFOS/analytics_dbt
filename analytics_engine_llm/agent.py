import sys
import os

# Adiciona a raiz do projeto ao sistema de caminhos do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from engine_processamento_duck_db.config import Config

load_dotenv()


class PublicProcurementAIAgente:  # Mantido o nome igual ao seu appstr.py
    def __init__(self):
        duckdb_file = Config.DUCKDB_PATH

        marts_validos = ["mart_por_uf", "mart_por_modalidade", "mart_por_orgao"]
        self.db = SQLDatabase.from_uri(
            f"duckdb:///{duckdb_file}",
            include_tables=marts_validos
        )

        # Corrigido para buscar do os.getenv e o nome correto do modelo
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.0
        )

        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            verbose=Config.DEBUG,
            agent_type="openai-tools"
        )

    def ask(self, question: str) -> str:
        prompt_contexto = (
            f"Você é um Analista de Dados especialista em compras públicas no Brasil. "
            f"Sua tarefa é responder a perguntas de negócio usando apenas os dados das tabelas de marts analíticos "
            f"fornecidas. Formate números grandes de forma legível e valores monetários em R$. "
            f"Pergunta do usuário: {question}"
        )
        try:
            response = self.agent_executor.invoke({"input": prompt_contexto})
            return response["output"]
        except Exception as e:
            return f"Erro ao processar análise nos marts: {str(e)}"