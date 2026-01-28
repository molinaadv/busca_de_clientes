import io
import re
from pathlib import Path
import pandas as pd
import streamlit as st

# ======================================================
# CONFIGURAÇÃO
# ======================================================
st.set_page_config(
    page_title="Molina | Busca de Clientes",
    page_icon="🔎",
    layout="wide"
)

# ======================================================
# LOGIN
# ======================================================
USUARIO_CORRETO = "molina"
SENHA_CORRETA = "senha@senha"

def verificar_login():
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if st.session_state["logado"]:
        return

    st.markdown("## 🔐 Acesso restrito")
    st.markdown("Sistema exclusivo do **Molina Advogados**")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    st.stop()

verificar_login()

# ======================================================
# BASE FIXA
# ======================================================
BASE_ARQUIVO = "Relatorio Pessoa Fisica - LegalOne.xlsx"

arquivo = Path(BASE_ARQUIVO)
if not arquivo.exists():
    st.error("Arquivo da base não encontrado.")
    st.stop()

@st.cache_data(ttl=60)
def carregar_base(path):
    df = pd.read_excel(path)
    df.columns = df.columns.map(lambda x: str(x).strip())
    return df

df = carregar_base(str(arquivo))

# ======================================================
# FUNÇÕES
# ======================================================
def norm_cpf(val):
    if pd.isna(val):
        return ""
    return re.sub(r"\D", "", str(val))

def norm_text(val):
    if pd.isna(val):
        return ""
    return str(val).strip().lower()

def detectar_coluna(colunas, palavras):
    for c in colunas:
        nome = str(c).lower().strip()
        if all(p in nome for p in palavras):
            return c
    return None

# ======================================================
# DETECTAR COLUNAS
# ======================================================
cols = list(df.columns)

col_nome = detectar_coluna(cols, ["nome"])
col_cpf = detectar_coluna(cols, ["cpf"])
col_senha_inss = detectar_coluna(cols, ["senha", "inss"])

# ======================================================
# HEADER
# ======================================================
c1, c2 = st.columns([1, 3])
with c1:
    st.image("assets/logo.png", use_container_width=True)
with c2:
    st.markdown("## 🔎 Busca de Clientes — Legal One")
    st.caption("Pesquisa por Nome ou CPF")

# ======================================================
# BUSCA
# ======================================================
nome_busca = st.text_input("Nome do cliente")
cpf_busca = st.text_input("CPF")

df["_NOME_N"] = df[col_nome].apply(norm_text)
df["_CPF_N"] = df[col_cpf].apply(norm_cpf)

resultado = df.copy()

if nome_busca:
    resultado = resultado[
        resultado["_NOME_N"].str.contains(norm_text(nome_busca), na=False)
    ]

if cpf_busca:
    resultado = resultado[
        resultado["_CPF_N"] == norm_cpf(cpf_busca)
    ]

export_df = resultado.drop(columns=["_NOME_N", "_CPF_N"], errors="ignore")

# ======================================================
# SENHA INSS — PRIMEIRO CAMPO PREENCHIDO
# ======================================================
senha_inss_valor = "—"

if col_senha_inss and len(export_df) > 0:
    serie = export_df[col_senha_inss].dropna()
    serie = serie.astype(str).str.strip()
    serie = serie[
        ~serie.str.lower().isin(["", "nan", "none", "-", "null"])
    ]

    if len(serie) > 0:
        senha_inss_valor = serie.iloc[0]

# ======================================================
# DASHBOARD
# ======================================================
st.markdown("---")
k1, k2, k3 = st.columns(3)

with k1:
    st.metric("Registros na base", len(df))

with k2:
    st.metric("Senha do INSS", senha_inss_valor)

with k3:
    st.metric("Resultados", len(export_df))

# ======================================================
# RESULTADOS
# ======================================================
st.markdown("### Resultados")
st.dataframe(export_df, use_container_width=True, height=520)

def gerar_excel(df_):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_.to_excel(writer, index=False)
    return out.getvalue()

st.download_button(
    "⬇️ Baixar resultado em Excel",
    data=gerar_excel(export_df),
    file_name="resultado_busca.xlsx"
)
