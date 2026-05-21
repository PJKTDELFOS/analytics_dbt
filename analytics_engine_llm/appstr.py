import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics_engine_llm.agent import PublicProcurementAIAgente

st.set_page_config(page_title="Data AI Analyst", page_icon="🤖", layout="wide")

st.title("🤖 Analista de Dados com IA — Compras Públicas (PNCP)")
st.subheader("Camada analítica inteligente sobre dbt + DuckDB")


@st.cache_resource
def init_agent():
    return PublicProcurementAIAgente()


try:
    ai_analyst = init_agent()
    st.success("Conectado com sucesso ao arquivo DuckDB local e à API do Gemini! 🎉")
except Exception as e:
    st.error(f"Falha ao inicializar o agente de IA: {e}")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("Ex: Qual modalidade de licitação movimentou o maior valor total estimado?"):

    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # CORRIGIDO — fora do bloco do usuário
    with st.chat_message("assistant"):
        with st.spinner("Analisando os marts analíticos no DuckDB..."):
            response = ai_analyst.ask(user_input)

            if isinstance(response, list) and len(response) > 0 and "text" in response[0]:
                texto_limpo = response[0]["text"]
            elif isinstance(response, dict) and "text" in response:
                texto_limpo = response["text"]
            else:
                texto_limpo = str(response)

            st.write(texto_limpo)
            st.session_state.chat_history.append({"role": "assistant", "content": texto_limpo})