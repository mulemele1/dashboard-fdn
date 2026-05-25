# app.py
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from auth import login_form, logout, admin_panel

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="FDN Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SESSION STATE
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "user_role" not in st.session_state:
    st.session_state.user_role = ""

# =========================================================
# LOGIN
# =========================================================
if not st.session_state.authenticated:

    st.markdown("""
    <style>
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        section[data-testid="stSidebar"] {
            display: none !important;
        }

        header {
            display: none !important;
        }

        .main .block-container {
            padding-top: 0rem;
        }
    </style>
    """, unsafe_allow_html=True)

    login_form()
    st.stop()

# =========================================================
# CSS GLOBAL
# =========================================================
st.markdown("""
<style>

.main-header {
    background: linear-gradient(135deg, #1a5f7a 0%, #0d3b4a 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 2rem;
}

.stat-card {
    background: white;
    padding: 1rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    text-align: center;
    border-top: 4px solid #1a5f7a;
}

.stat-number {
    font-size: 2.1rem;
    font-weight: bold;
    color: #1a5f7a;
}

.stat-label {
    font-size: 0.9rem;
    color: #666;
}

.sidebar-user {
    text-align: center;
    padding: 1rem;
    background: #f0f4f8;
    border-radius: 12px;
    margin-bottom: 1rem;
}

.sidebar-role {
    font-size: 0.75rem;
    color: #1a5f7a;
    background: #d9edf7;
    padding: 4px 10px;
    border-radius: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown(f"""
    <div class="sidebar-user">
        <div style="font-size:2rem;">👤</div>
        <strong>{st.session_state.user_name}</strong><br><br>
        <span class="sidebar-role">
            {st.session_state.user_role.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.user_role == "admin":
        page = st.radio(
            "Navegação",
            ["📊 Dashboard", "⚙️ Gestão de Utilizadores"]
        )
    else:
        page = "📊 Dashboard"

    st.markdown("---")

    if st.button("🚪 Sair"):
        logout()

# =========================================================
# ADMIN PANEL
# =========================================================
if page == "⚙️ Gestão de Utilizadores":
    admin_panel()
    st.stop()

# =========================================================
# CONFIGURAÇÕES
# =========================================================
DATA_DIR = "data"

DISTRICT_TARGETS = {
    "Distrito de Mecubúri": 150,
    "Distrito de Ribáuè": 120,
    "Distrito de Lalaua": 80,
}

# =========================================================
# FUNÇÕES
# =========================================================
@st.cache_data(ttl=300)
def load_caf1():

    file_path = os.path.join(
        DATA_DIR,
        "results-survey666877.csv"
    )

    if not os.path.exists(file_path):
        return pd.DataFrame()

    df = pd.read_csv(file_path, encoding="utf-8")

    if "Data de submissão" in df.columns:
        df = df[df["Data de submissão"].notna()]

    return df


@st.cache_data(ttl=300)
def load_maf():

    file_path = os.path.join(
        DATA_DIR,
        "results-survey757779.csv"
    )

    if not os.path.exists(file_path):
        return pd.DataFrame()

    df = pd.read_csv(file_path, encoding="utf-8")

    if "Date submitted" in df.columns:
        df = df[df["Date submitted"].notna()]

    return df


@st.cache_data(ttl=300)
def get_daily_progress():

    caf_df = load_caf1()
    maf_df = load_maf()

    if caf_df.empty and maf_df.empty:
        return pd.DataFrame()

    result = pd.DataFrame()

    if not caf_df.empty:
        caf_df["date"] = pd.to_datetime(
            caf_df["Data de submissão"]
        ).dt.date

        daily_caf = caf_df.groupby("date").size().reset_index(name="caf")
        result = daily_caf.copy()

    if not maf_df.empty:
        maf_df["date"] = pd.to_datetime(
            maf_df["Date submitted"]
        ).dt.date

        daily_maf = maf_df.groupby("date").size().reset_index(name="maf")

        if result.empty:
            result = daily_maf.copy()
        else:
            result = result.merge(
                daily_maf,
                on="date",
                how="outer"
            )

    if "caf" not in result.columns:
        result["caf"] = 0

    if "maf" not in result.columns:
        result["maf"] = 0

    result = result.fillna(0)

    result["caf"] = result["caf"].astype(int)
    result["maf"] = result["maf"].astype(int)

    result["total"] = result["caf"] + result["maf"]

    result = result.sort_values("date")

    return result


@st.cache_data(ttl=300)
def get_district_progress():

    df = load_caf1()

    if df.empty:
        return pd.DataFrame()

    district_col = "Em que Distrito está a realizar o levantamento??"

    if district_col not in df.columns:
        return pd.DataFrame()

    achieved = df[district_col].value_counts().to_dict()

    rows = []

    for district, target in DISTRICT_TARGETS.items():

        current = achieved.get(district, 0)

        rows.append({
            "Distrito": district,
            "Previstos": target,
            "Alcançados": current,
            "Percentual": (
                current / target * 100
            ) if target > 0 else 0
        })

    return pd.DataFrame(rows)

# =========================================================
# CARREGAR DADOS
# =========================================================
caf1_df = load_caf1()
maf_df = load_maf()

daily_progress = get_daily_progress()
district_df = get_district_progress()

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="main-header">
    <h1>📊 FDN Dashboard</h1>
    <p>
        Monitorização de Chefes de Agregado e
        Membros | CAF + MAF
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ERRO DE DADOS
# =========================================================
if caf1_df.empty:

    st.error("""
    ❌ Não foi possível carregar os dados.

    Verifique se os ficheiros CSV estão
    dentro da pasta data/
    """)

    st.stop()

# =========================================================
# KPIs
# =========================================================
total_heads = len(caf1_df)
total_members = len(maf_df)

total_target = sum(DISTRICT_TARGETS.values())

percentage = (
    total_heads / total_target * 100
) if total_target > 0 else 0

if "Nome do Inquirido?" in caf1_df.columns:
    unique_inquirers = caf1_df["Nome do Inquirido?"].nunique()
else:
    unique_inquirers = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_heads}</div>
        <div class="stat-label">
            Chefes de Agregado
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_members}</div>
        <div class="stat-label">
            Membros do Agregado
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{percentage:.1f}%</div>
        <div class="stat-label">
            Progresso Geral
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{unique_inquirers}</div>
        <div class="stat-label">
            Técnicos Activos
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# GRÁFICO DIÁRIO
# =========================================================
st.subheader("📈 Levantamentos Diários")

if not daily_progress.empty:

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=daily_progress["date"],
            y=daily_progress["caf"],
            name="CAF"
        )
    )

    fig.add_trace(
        go.Bar(
            x=daily_progress["date"],
            y=daily_progress["maf"],
            name="MAF"
        )
    )

    fig.update_layout(
        barmode="group",
        height=400,
        xaxis_title="Data",
        yaxis_title="Questionários"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Sem dados diários disponíveis.")

# =========================================================
# TÉCNICOS
# =========================================================
st.subheader("👥 Inquéritos por Técnico")

if "Nome do Inquirido?" in caf1_df.columns:

    tech_counts = (
        caf1_df["Nome do Inquirido?"]
        .value_counts()
        .reset_index()
    )

    tech_counts.columns = ["Técnico", "Total"]

    fig = px.bar(
        tech_counts,
        x="Técnico",
        y="Total",
        text="Total",
        color="Total"
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# DISTRITOS
# =========================================================
st.subheader("🗺️ Progresso por Distrito")

if not district_df.empty:

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=district_df["Distrito"],
        y=district_df["Previstos"],
        name="Previstos"
    ))

    fig.add_trace(go.Bar(
        x=district_df["Distrito"],
        y=district_df["Alcançados"],
        name="Alcançados"
    ))

    fig.update_layout(
        barmode="group",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        district_df.style.format({
            "Percentual": "{:.1f}%"
        })
    )

# =========================================================
# SEXO
# =========================================================
st.subheader("👤 Sexo dos Chefes de Agregado")

gender_col = "Sexo do chefe de agregado"

if gender_col in caf1_df.columns:

    gender_counts = (
        caf1_df[gender_col]
        .value_counts()
        .reset_index()
    )

    gender_counts.columns = ["Sexo", "Total"]

    fig = px.pie(
        gender_counts,
        values="Total",
        names="Sexo"
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TABELA
# =========================================================
st.subheader("📋 Últimas Submissões")

required_cols = [
    "Data de submissão",
    "Nome do Inquirido?",
    "Qual é o nome do Chefe do Agregado Familiar?",
    "Em que Distrito está a realizar o levantamento??"
]

valid_cols = [
    c for c in required_cols
    if c in caf1_df.columns
]

if valid_cols:

    display_df = caf1_df[valid_cols].copy()

    rename_map = {
        "Data de submissão": "Data",
        "Nome do Inquirido?": "Técnico",
        "Qual é o nome do Chefe do Agregado Familiar?": "Chefe do Agregado",
        "Em que Distrito está a realizar o levantamento??": "Distrito"
    }

    display_df = display_df.rename(columns=rename_map)

    st.dataframe(
        display_df.head(20),
        use_container_width=True
    )

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")

st.caption(
    "FDN Dashboard | Última actualização: {}".format(
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )
)