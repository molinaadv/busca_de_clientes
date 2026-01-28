import io
import re
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Molina | Busca de Clientes", page_icon="🔎", layout="wide")

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

BASE_ARQUIVO = "Relatorio Pessoa Fisica - LegalOne.xlsx"

CSS = """
<style>
.stApp { background: linear-gradient(180deg, #f5f7fb 0%, #ffffff 55%, #f5f7fb 100%); }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 2.5rem;}
.mlp-card {
    background: rgba(255,255,255,0.95);
    border-radius: 18px;
    padding: 16px;
    border: 1px solid rgba(15,23,42,0.08);
    box-shadow: 0 10px 30px rgba(2,8,23,0.06);
}
.mlp-kpi-title {font-size: 0.85rem; color: #6b7280;}
.mlp-kpi-value {font-size: 1.6rem; font-weight: 700; color:#0f172a;}
.mlp-kpi-sub {font-size: 0.75rem; color: #9ca3af;}
.mlp-section-title {font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:6px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def kpi_card(title, value, sub=""):
    st.markdown(f"""
    <div class="mlp-card">
        <div class="mlp-kpi-title">{title}</div>
        <div class="mlp-kpi-value">{value}</div>
        <div class="mlp-kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def norm_cpf(val):
    if pd.isna(val):
        return ""
    return re.sub(r"\\D", "", str(val))

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

h1, h2 = st.columns([1.2, 2.8])
with h1:
    st.image("assets/logo.png", use_container_width=True)
with h2:
    st.markdown("## Busca de Clientes (Legal One)")
    st.markdown("<span style='color:#64748b'>Consulta por Nome ou CPF</span>", unsafe_allow_html=True)

st.markdown("---")

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

cols = list(df.columns)
col_nome = detectar_coluna(cols, ["nome"])
col_cpf = detectar_coluna(cols, ["cpf"])
col_senha_inss = detectar_coluna(cols, ["senha", "inss"])

st.markdown("### 🔎 Buscar cliente")

c1, c2 = st.columns(2)
with c1:
    nome_busca = st.text_input("Nome do cliente")
with c2:
    cpf_busca = st.text_input("CPF")

df["_NOME_N"] = df[col_nome].apply(norm_text)
df["_CPF_N"] = df[col_cpf].apply(norm_cpf)

resultado = df.copy()

if nome_busca:
    resultado = resultado[resultado["_NOME_N"].str.contains(norm_text(nome_busca), na=False)]

if cpf_busca:
    resultado = resultado[resultado["_CPF_N"] == norm_cpf(cpf_busca)]

export_df = resultado.drop(columns=["_NOME_N", "_CPF_N"], errors="ignore")

senha_inss_valor = "—"
if col_senha_inss and len(export_df) > 0:
    serie = export_df[col_senha_inss].dropna()
    serie = serie.astype(str).str.strip()
    serie = serie[~serie.str.lower().isin(["", "nan", "none", "-", "null"])]
    if len(serie) > 0:
        senha_inss_valor = serie.iloc[0]

st.markdown("---")
k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card("Registros na base", len(df), "Total")

with k2:
    kpi_card("Senha do INSS", senha_inss_valor, "Primeiro preenchido")

with k3:
    kpi_card("Resultados", len(export_df), "Encontrados")

with k4:
    kpi_card("Filtros usados", "Nome / CPF", "Busca ativa")

st.markdown("---")
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
