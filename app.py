
import io
import re
from pathlib import Path
import pandas as pd
import streamlit as st

import hashlib

# ===============================
# LOGIN DO SISTEMA
# ===============================

USUARIO_CORRETO = "molina"
SENHA_CORRETA = "senha@senha"

def tela_login():
    st.markdown("## 🔐 Acesso restrito")
    st.markdown("Sistema exclusivo do escritório Molina Advogados")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

def verificar_login():
    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if not st.session_state["logado"]:
        tela_login()
        st.stop()

# chama o login
verificar_login()



st.set_page_config(page_title="Molina | Busca de Clientes", page_icon="🔎", layout="wide")

BASE_ARQUIVO = "Relatorio Pessoa Fisica - LegalOne.xlsx"

CSS = """
<style>
.stApp { background: linear-gradient(180deg, rgba(245,247,251,1) 0%, rgba(255,255,255,1) 55%, rgba(245,247,251,1) 100%); }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 2.5rem;}
.mlp-card { background: rgba(255,255,255,0.92); border: 1px solid rgba(15,23,42,0.08);
  border-radius: 18px; padding: 16px 16px 14px 16px; box-shadow: 0 10px 30px rgba(2, 8, 23, 0.06); }
.mlp-section-title {font-size: 1.05rem; font-weight: 700; color: rgba(15,23,42,0.92); margin: 6px 0 10px 0;}
.mlp-muted {color: rgba(15,23,42,0.60);}
.mlp-kpi-title {font-size: 0.85rem; color: rgba(15,23,42,0.70); margin-bottom: 2px;}
.mlp-kpi-value {font-size: 1.55rem; font-weight: 700; color: rgba(15,23,42,0.92);}
.mlp-kpi-sub {font-size: 0.80rem; color: rgba(15,23,42,0.55); margin-top: 2px;}
hr {border: none; border-top: 1px solid rgba(15,23,42,0.08); margin: 16px 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

h1, h2 = st.columns([1.2, 2.8], vertical_alignment="center")
with h1:
    st.image("assets/logo.png", use_container_width=True)
with h2:
    st.markdown("## Busca de Clientes (Nome / CPF)")
    st.markdown('<span class="mlp-muted">Base fixa do Legal One → pesquise por <b>nome</b> e/ou <b>CPF</b> → exporte o resultado.</span>', unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return out.getvalue()

def norm_cpf(val) -> str:
    if val is None:
        return ""
    s = str(val)
    if s.lower() in ("nan", "none"):
        return ""
    return re.sub(r"\D", "", s)

def norm_name(val) -> str:
    if val is None:
        return ""
    s = str(val)
    if s.lower() in ("nan", "none"):
        return ""
    return s.strip().lower()

def kpi_card(title: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="mlp-card">
            <div class="mlp-kpi-title">{title}</div>
            <div class="mlp-kpi-value">{value}</div>
            <div class="mlp-kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.image("assets/logo.png", use_container_width=True)
    st.markdown("### Base fixa")
    st.caption("O sistema lê automaticamente o Excel na pasta do sistema.")
    st.code(BASE_ARQUIVO)
    st.markdown("### Configurações")
    st.caption("Selecione as colunas corretas de Nome e CPF.")
    match_mode = st.radio("Modo de busca por Nome", ["Contém (recomendado)", "Exato"], index=0)
    show_sensitive = st.checkbox("Mostrar CPF completo na tela", value=False)

base_path = Path(BASE_ARQUIVO)
if not base_path.exists():
    st.error("Não encontrei o arquivo base do Legal One na pasta do sistema.")
    st.markdown(
        f'<div class="mlp-card"><div class="mlp-section-title">Como corrigir</div>'
        f'<div class="mlp-muted">'
        f'1) Coloque o arquivo <b>{BASE_ARQUIVO}</b> na <b>mesma pasta</b> do app.py<br/>'
        f'2) Reabra o sistema<br/>'
        f'</div></div>',
        unsafe_allow_html=True
    )
    st.stop()

@st.cache_data(ttl=60)
def load_base(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

try:
    df = load_base(str(base_path))
    cols = list(df.columns)

    def find_col(keywords):
        for c in cols:
            lc = str(c).strip().lower()
            if any(k in lc for k in keywords):
                return c
        return None

    detected_name = find_col(["nome", "cliente", "envolvido", "parte"])
    detected_cpf = find_col(["cpf", "documento", "doc"])

    c1, c2 = st.columns(2)
    with c1:
        name_col = st.selectbox("Coluna de Nome", options=cols, index=cols.index(detected_name) if detected_name in cols else 0)
    with c2:
        cpf_default_idx = cols.index(detected_cpf) if detected_cpf in cols else min(1, len(cols)-1)
        cpf_col = st.selectbox("Coluna de CPF", options=cols, index=cpf_default_idx)

    work = df.copy()
    work["_NOME_NORM"] = work[name_col].apply(norm_name)
    work["_CPF_NORM"] = work[cpf_col].apply(norm_cpf)

    st.markdown('<div class="mlp-section-title">Buscar</div>', unsafe_allow_html=True)
    q1, q2, q3 = st.columns([2.2, 1.4, 1.4])
    with q1:
        name_query = st.text_input("Nome (ou parte do nome)", placeholder="Ex.: Maria, João Silva...")
    with q2:
        cpf_query = st.text_input("CPF (somente números ou com pontos/traço)", placeholder="Ex.: 123.456.789-00")
    with q3:
        limit = st.number_input("Limite de resultados", min_value=10, max_value=5000, value=200, step=10)

    nq = norm_name(name_query)
    cq = norm_cpf(cpf_query)

    if not nq and not cq:
        st.info("Digite um Nome e/ou CPF para buscar. (Sem filtro, o sistema não lista a base inteira.)")
        st.markdown("<hr/>", unsafe_allow_html=True)
        k1, k2 = st.columns(2)
        with k1:
            kpi_card("Registros na base", f"{len(df):,}".replace(",", "."), "Base carregada do Excel")
        with k2:
            kpi_card("Atualização", "Automática", "Recarrega a cada 60s (se o arquivo mudar)")
        st.stop()

    out = work.copy()
    filters_used = []

    if nq:
        filters_used.append("Nome")
        if match_mode.startswith("Contém"):
            out = out[out["_NOME_NORM"].str.contains(re.escape(nq), na=False)]
        else:
            out = out[out["_NOME_NORM"] == nq]

    if cq:
        filters_used.append("CPF")
        out = out[out["_CPF_NORM"] == cq]

    export_df = out.drop(columns=["_NOME_NORM", "_CPF_NORM"], errors="ignore").copy()
    display_df = export_df.copy()

    if (not show_sensitive) and (cpf_col in display_df.columns):
        def mask(val):
            d = norm_cpf(val)
            if len(d) == 11:
                return f"{d[:3]}.***.***-{d[-2:]}"
            return "***"
        display_df[cpf_col] = display_df[cpf_col].apply(mask)

    st.markdown("<hr/>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Registros na base", f"{len(df):,}".replace(",", "."), "Total no Excel")
    with k2:
        kpi_card("Resultados", f"{len(display_df):,}".replace(",", "."), "Após filtros")
    with k3:
        kpi_card("Filtros usados", ", ".join(filters_used) if filters_used else "Nenhum", "Critérios de busca")

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown('<div class="mlp-section-title">Resultados</div>', unsafe_allow_html=True)
    st.dataframe(display_df.head(int(limit)), use_container_width=True, height=520)

    st.download_button(
        "⬇️ Baixar Excel (resultado filtrado)",
        data=to_excel_bytes(export_df),
        file_name="resultado_busca_clientes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

except Exception as e:
    st.error(f"Erro ao ler a base do Excel: {e}")
