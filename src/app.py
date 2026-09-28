import streamlit as st
from analise_risco import calcular_score_risco, carregar_perfil_cliente
from agente import gerar_resposta_agente

st.set_page_config(page_title="GuardIA Bradesco", page_icon="🛡️", layout="centered")

perfil = carregar_perfil_cliente()


def brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_alerta(nome: str, valor: float, risco: dict, chamada_ativa: bool) -> str:
    linhas = [
        f"Olá, {nome}! Sou a **GuardIA Bradesco**. Identifiquei uma tentativa de PIX de "
        f"**{brl(valor)}** com nível de risco **{risco['nivel']}** ({risco['score']}/100).",
        "",
        "O que chamou minha atenção:",
        "",
    ]
    linhas += [f"- {fator}" for fator in risco["fatores"]]
    linhas.append("")
    if chamada_ativa:
        linhas.append(
            "**Atenção:** se alguém ao telefone está pedindo esse PIX (para 'cancelar uma compra', "
            "'testar a conta' ou 'proteger seu dinheiro'), **DESLIGUE AGORA!** "
            "O Bradesco nunca pede transferências por telefone."
        )
    else:
        linhas.append(
            "Antes de continuar, confirme que foi você quem decidiu fazer esse PIX e que ninguém "
            "está te pressionando. Posso te ajudar a conferir?"
        )
    return "\n".join(linhas)


st.title("🛡️ Bradesco - GuardIA Security Prototype")
st.caption("Demonstração de Agente Financeiro Proativo e Consultivo contra Engenharia Social")

# Sidebar - simulação do contexto do app mobile
st.sidebar.caption(f"👤 Cliente: {perfil['nome']}")
if perfil["valor_habitual"]:
    st.sidebar.caption(f"Gasto habitual (mediana): {brl(perfil['valor_habitual'])}")
st.sidebar.header("⚙️ Simulação de Transação PIX")
valor = st.sidebar.number_input("Valor do PIX (R$)", min_value=10.0, value=3500.0, step=100.0)
chave = st.sidebar.text_input("Chave PIX Destino", value="nova_chave_desconhecida@email.com")
hora = st.sidebar.slider("Horário da Transação (Hora)", 0, 23, 23)
chamada_ativa = st.sidebar.checkbox("Simular chamada telefônica ativa?", value=True)

# Avaliação do risco via Python
resultado_risco = calcular_score_risco(valor, chave, chamada_ativa, hora, perfil["valor_habitual"])
contexto = {**resultado_risco, "cliente_nome": perfil["nome"], "renda_mensal": perfil["renda_mensal"]}

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Módulo de Análise de Risco")
st.sidebar.metric("Score de Risco", f"{resultado_risco['score']}/100")
if resultado_risco["nivel"] == "alto":
    st.sidebar.error("⚠️ Risco ALTO: TRANSAÇÃO SUSPEITA")
elif resultado_risco["nivel"] == "médio":
    st.sidebar.warning("🟡 Risco MÉDIO: atenção")
else:
    st.sidebar.success("✅ Risco BAIXO: TRANSAÇÃO NORMAL")

# Inicialização do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("🔄 Nova simulação"):
    st.session_state.messages = []
    st.rerun()

# Se for suspeita, a GuardIA inicia a conversa de forma proativa
if resultado_risco["suspeita"] and len(st.session_state.messages) == 0:
    alerta = montar_alerta(perfil['nome'].split()[0], valor, resultado_risco, chamada_ativa)
    st.session_state.messages.append({"role": "assistant", "content": alerta})

if not resultado_risco["suspeita"] and not st.session_state.messages:
    st.info("Nenhum alerta gerado: a transação está dentro do padrão. Você ainda pode conversar com a GuardIA.")

# Histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do cliente
if prompt := st.chat_input("Digite sua mensagem para a GuardIA..."):
    historico_anterior = list(st.session_state.messages)  # antes de incluir a nova mensagem
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("GuardIA analisando diretrizes de segurança..."):
            resposta = gerar_resposta_agente(prompt, contexto, historico_anterior)
            st.markdown(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})
