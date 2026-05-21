import streamlit as st
import sys
import os

# Adiciona a raiz do projeto ao sistema de caminhos do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agora o Python vai encontrar o módulo perfeitamente
from analytics_engine_llm.agent import PublicProcurementAIAgente

st.set_page_config(page_title="Data AI Analyst", page_icon="🤖", layout="wide")

st.title("🤖 Analista de Dados com IA — Compras Públicas (PNCP)")
st.subheader("Camada analítica inteligente sobre dbt + DuckDB")

# Inicialização do agente com cache do Streamlit para evitar recarregar a cada clique
@st.cache_resource
def init_agent():
    return PublicProcurementAIAgente()


try:
    ai_analyst = init_agent()
    st.success("Conectado com sucesso ao arquivo DuckDB local e à API do Gemini! 🎉")
except Exception as e:
    st.error(f"Falha ao inicializar o agente de IA: {e}")
    st.stop()

# Inicializa o histórico de mensagens no estado da sessão
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Renderiza mensagens anteriores do chat
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Caixa de entrada para perguntas do usuário
if user_input := st.chat_input("Ex: Qual modalidade de licitação movimentou o maior valor total estimado?"):
    # Adiciona e exibe a mensagem do usuário
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Processa a resposta com o agente de IA
        # Processa a resposta com o agente de IA
        with st.chat_message("assistant"):
            with st.spinner("Analisando os marts analíticos no DuckDB..."):
                response = ai_analyst.ask(user_input)

                # Garante que vamos extrair apenas o texto se a resposta vier como lista/dicionário
                if isinstance(response, list) and len(response) > 0 and "text" in response[0]:
                    texto_limpo = response[0]["text"]
                elif isinstance(response, dict) and "text" in response:
                    texto_limpo = response["text"]
                else:
                    texto_limpo = str(response)

                st.write(texto_limpo)
                st.session_state.chat_history.append({"role": "assistant", "content": texto_limpo})