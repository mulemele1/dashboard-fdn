"""
app.py - FDN Dashboard
Versão com Gráficos Detalhados por Distrito e Comunidade (Meta vs Realizado)
Compatível com Python 3.6 e versões antigas do Streamlit/Plotly
"""

import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Importa as funções de autenticação do ficheiro auth.py
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
# CACHE COMPATÍVEL COM STREAMLIT ANTIGO
# =========================================================

if hasattr(st, "cache_data"):
    cache_fn = st.cache_data
else:
    def cache_fn(**kwargs):
        kwargs.pop("ttl", None)
        return st.cache(suppress_st_warning=True, allow_output_mutation=True)

# =========================================================
# SESSÃO DE AUTENTICAÇÃO
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Estado da sidebar (expandida ou colapsada) - apenas para admin
if "sidebar_expanded" not in st.session_state:
    st.session_state.sidebar_expanded = False

if not st.session_state.authenticated:
    login_form()
    st.stop()

# =========================================================
# CSS PARA OCULTAR/MOSTRAR A SIDEBAR
# =========================================================

# CSS base que oculta a sidebar por padrão
sidebar_css_hidden = """
<style>
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    .main-header {
        background: linear-gradient(135deg, #1a5f7a 0%, #0d3b4a 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }
    .stat-card {
        background: white;
        padding: 1.2rem 1rem;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border-top: 4px solid #1a5f7a;
        margin-bottom: 0.5rem;
    }
    .stat-number { font-size: 2rem; font-weight: 700; color: #1a5f7a; }
    .stat-label  { color: #666; font-size: 0.88rem; margin-top: 0.3rem; }
    .stat-sub    { color: #1a5f7a; font-size: 0.78rem; font-weight: 600; margin-top: 0.2rem; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0d3b4a;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e0f0f7;
    }
    .progress-bar-wrap {
        background: #e9ecef;
        border-radius: 8px;
        height: 10px;
        margin-top: 4px;
    }
    .progress-bar-fill {
        height: 10px;
        border-radius: 8px;
        background: linear-gradient(90deg, #1a5f7a, #4aa3c2);
    }
    .toggle-btn {
        background: #1a5f7a;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    .toggle-btn:hover {
        background: #0d3b4a;
    }
    </style>
"""

# CSS que mostra a sidebar (para admin quando expandida)
sidebar_css_visible = """
<style>
    [data-testid="collapsedControl"] {
        display: block !important;
    }
    section[data-testid="stSidebar"] {
        display: block !important;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    .main-header {
        background: linear-gradient(135deg, #1a5f7a 0%, #0d3b4a 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }
    .stat-card {
        background: white;
        padding: 1.2rem 1rem;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border-top: 4px solid #1a5f7a;
        margin-bottom: 0.5rem;
    }
    .stat-number { font-size: 2rem; font-weight: 700; color: #1a5f7a; }
    .stat-label  { color: #666; font-size: 0.88rem; margin-top: 0.3rem; }
    .stat-sub    { color: #1a5f7a; font-size: 0.78rem; font-weight: 600; margin-top: 0.2rem; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0d3b4a;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e0f0f7;
    }
    .progress-bar-wrap {
        background: #e9ecef;
        border-radius: 8px;
        height: 10px;
        margin-top: 4px;
    }
    .progress-bar-fill {
        height: 10px;
        border-radius: 8px;
        background: linear-gradient(90deg, #1a5f7a, #4aa3c2);
    }
    .toggle-btn {
        background: #e07b39;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    .toggle-btn:hover {
        background: #c06020;
    }
    </style>
"""

# Aplica o CSS apropriado baseado no role do usuário e estado da sidebar
if st.session_state.user_role == "admin" and st.session_state.sidebar_expanded:
    st.markdown(sidebar_css_visible, unsafe_allow_html=True)
else:
    st.markdown(sidebar_css_hidden, unsafe_allow_html=True)

# =========================================================
# FUNÇÃO PARA RECARREGAR A PÁGINA (COMPATÍVEL)
# =========================================================

def safe_rerun():
    """Recarrega a página de forma compatível com versões antigas do Streamlit"""
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        # Fallback: recarregar a página via JavaScript
        st.markdown(
            """
            <meta http-equiv="refresh" content="0">
            """,
            unsafe_allow_html=True
        )

# =========================================================
# BARRA SUPERIOR COM BOTÕES
# =========================================================

# Define as colunas da barra superior
if st.session_state.user_role == "admin":
    # Admin: colunas para toggle button, info, e logout
    col1, col2, col3, col4 = st.columns([1, 5, 1, 1])
    
    with col1:
        # Botão de toggle (seta) - mostra/oculta a sidebar
        if st.session_state.sidebar_expanded:
            toggle_label = "◀️"
            toggle_help = "Ocultar Menu"
        else:
            toggle_label = "▶️"
            toggle_help = "Mostrar Menu"
        
        if st.button(toggle_label, help=toggle_help):
            st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded
            safe_rerun()
    
    with col3:
        st.markdown(
            "<div style='text-align:right;font-size:0.8rem;color:#1a5f7a;'>👤 {}</div>".format(st.session_state.user_role.upper()),
            unsafe_allow_html=True
        )
    
    with col4:
        if st.button("🚪 Sair", help="Fazer logout"):
            logout()
else:
    # Usuário normal: apenas colunas para info e logout
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        st.markdown(
            "<div style='text-align:right;font-size:0.8rem;color:#1a5f7a;'>👤 {}</div>".format(st.session_state.user_role.upper()),
            unsafe_allow_html=True
        )
    with col3:
        if st.button("🚪 Sair", help="Fazer logout"):
            logout()

# =========================================================
# SIDEBAR (aparece apenas quando expandida e para admin)
# =========================================================

if st.session_state.user_role == "admin" and st.session_state.sidebar_expanded:
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:1rem;background:#f0f4f8;"
            "border-radius:10px;margin-bottom:1rem;'>"
            "<div style='font-size:2rem;'>👤</div>"
            "<strong>{}</strong><br>"
            "<span style='font-size:0.8rem;color:#1a5f7a;background:#e0f0f7;"
            "padding:2px 10px;border-radius:10px;'>{}</span>"
            "</div>".format(
                st.session_state.user_name,
                st.session_state.user_role.upper()
            ),
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Menu de navegação
        page = st.radio(
            "📋 Menu",
            ["📊 Dashboard", "⚙️ Gestão de Utilizadores"],
            index=0
        )
        
        st.markdown("---")
        
        # Informações do sistema
        st.markdown("**ℹ️ Informações**")
        st.caption("Versão: 2.0")
        st.caption("Última atualização: {}".format(datetime.now().strftime("%d/%m/%Y")))
else:
    page = "📊 Dashboard"

# =========================================================
# PÁGINA: GESTÃO DE UTILIZADORES (apenas admin)
# =========================================================

if st.session_state.user_role == "admin" and page == "⚙️ Gestão de Utilizadores":
    admin_panel()
    st.stop()

# =========================================================
# METAS (Baseado no Target.docx)
# =========================================================

COMMUNITY_TARGETS_CAF = {
    "Intatapila": {"distrito": "Distrito de Mecubúri", "H": 104, "M": 77,  "CAF": 181, "Machambas": 233},
    "Inticuane":  {"distrito": "Distrito de Mecubúri", "H": 111, "M": 62,  "CAF": 173, "Machambas": 195},
    "Namacula":   {"distrito": "Distrito de Mecubúri", "H": 196, "M": 75,  "CAF": 271, "Machambas": 293},
    "Mutapua":    {"distrito": "Distrito de Mecubúri", "H": 22,  "M": 5,   "CAF": 27,  "Machambas": 31},
    "Lancheque":  {"distrito": "Distrito de Ribáuè",   "H": 15,  "M": 10,  "CAF": 25,  "Machambas": 31},
    "Meparara":   {"distrito": "Distrito de Ribáuè",   "H": 10,  "M": 2,   "CAF": 12,  "Machambas": 13},
    "Mesa":       {"distrito": "Distrito de Ribáuè",   "H": 19,  "M": 4,   "CAF": 23,  "Machambas": 25},
    "Cavucane":   {"distrito": "Distrito de Ribáuè",   "H": 20,  "M": 4,   "CAF": 24,  "Machambas": 25},
    "Namirimo":   {"distrito": "Distrito de Ribáuè",   "H": 31,  "M": 11,  "CAF": 42,  "Machambas": 51},
    "Mussuril":   {"distrito": "Distrito de Ribáuè",   "H": 2,   "M": 0,   "CAF": 2,   "Machambas": 2},
}

DISTRICT_TARGETS = {
    "Distrito de Mecubúri": 652,
    "Distrito de Ribáuè":   128,
}
DISTRICT_MACHAMBA_TARGETS = {
    "Distrito de Mecubúri": 752,
    "Distrito de Ribáuè":   147,
}

DATA_DIR = "data"

# =========================================================
# LEITURA DE CSVs
# =========================================================

def safe_csv(path, encoding="utf-8"):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding=encoding)
    except Exception:
        return pd.DataFrame()

@cache_fn(ttl=300)
def load_caf():
    df1 = safe_csv(os.path.join(DATA_DIR, "results-survey666877.csv"))
    df2 = safe_csv(os.path.join(DATA_DIR, "results-survey163198.csv"))
    
    dfs = []
    if not df1.empty:
        dfs.append(df1[df1["Data de submissão"].notna()])
    if not df2.empty:
        dfs.append(df2[df2["Data de submissão"].notna()])
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

@cache_fn(ttl=300)
def load_maf():
    df = safe_csv(os.path.join(DATA_DIR, "results-survey757779.csv"))
    if df.empty:
        return df
    return df[df["Data de submissão"].notna()].copy()

@cache_fn(ttl=300)
def load_survey4():
    df = safe_csv(os.path.join(DATA_DIR, "results-survey996006.csv"))
    if df.empty:
        return df
    return df[df["Date submitted"].notna()].copy()

# =========================================================
# FUNÇÕES DE ANÁLISE
# =========================================================

def normalise_community(name):
    if pd.isna(name):
        return ""
    name = str(name).strip()
    mapping = {
        "intatapila": "Intatapila",
        "inticuane": "Inticuane",
        "namacula": "Namacula",
        "mutapua": "Mutapua",
        "lancheque": "Lancheque",
        "meparara": "Meparara",
        "mesa": "Mesa",
        "cavucane": "Cavucane",
        "namirimo": "Namirimo",
        "mussuril": "Mussuril",
    }
    name_lower = name.lower()
    for key, val in mapping.items():
        if key in name_lower:
            return val
    return name

def get_daily_progress(caf_df, maf_df):
    rows = []
    
    if not caf_df.empty and "Data de submissão" in caf_df.columns:
        c = caf_df.copy()
        c["date"] = pd.to_datetime(c["Data de submissão"], errors="coerce").dt.date
        c["tipo"] = "CAF"
        rows.append(c[["date", "tipo"]])
    
    if not maf_df.empty and "Data de submissão" in maf_df.columns:
        m = maf_df.copy()
        m["date"] = pd.to_datetime(m["Data de submissão"], errors="coerce").dt.date
        m["tipo"] = "MAF"
        rows.append(m[["date", "tipo"]])
    
    if not rows:
        return pd.DataFrame(), pd.DataFrame()
    
    all_df = pd.concat(rows, ignore_index=True).dropna(subset=["date"])
    
    daily_caf = all_df[all_df["tipo"] == "CAF"].groupby("date").size().reset_index(name="CAF")
    daily_maf = all_df[all_df["tipo"] == "MAF"].groupby("date").size().reset_index(name="MAF")
    
    dates = pd.DataFrame({"date": sorted(all_df["date"].unique())})
    daily = dates.merge(daily_caf, on="date", how="left").merge(daily_maf, on="date", how="left")
    daily["CAF"] = daily["CAF"].fillna(0).astype(int)
    daily["MAF"] = daily["MAF"].fillna(0).astype(int)
    daily["Total"] = daily["CAF"] + daily["MAF"]
    
    daily = daily.sort_values("date")
    daily["CAF_Acumulado"] = daily["CAF"].cumsum()
    daily["MAF_Acumulado"] = daily["MAF"].cumsum()
    daily["Total_Acumulado"] = daily["Total"].cumsum()
    
    return daily, all_df

def get_community_progress(caf_df):
    if caf_df.empty:
        return pd.DataFrame()
    
    col_comunidade = "Indique o Povoado/comunidade em que o agregado familiar está localizado."
    col_machambas = "Quantas machambas tem o Chefe do Agregado?"
    
    if col_comunidade not in caf_df.columns:
        return pd.DataFrame()
    
    df = caf_df.copy()
    df["comunidade_norm"] = df[col_comunidade].apply(normalise_community)
    
    achieved_caf = df["comunidade_norm"].value_counts().to_dict()
    
    if col_machambas in df.columns:
        df[col_machambas] = pd.to_numeric(df[col_machambas], errors="coerce").fillna(0)
        mach_by_comm = df.groupby("comunidade_norm")[col_machambas].sum().fillna(0).astype(int).to_dict()
    else:
        mach_by_comm = {}
    
    rows = []
    for comm, t in COMMUNITY_TARGETS_CAF.items():
        caf_alc = achieved_caf.get(comm, 0)
        mach_alc = mach_by_comm.get(comm, 0)
        rows.append({
            "Distrito": t["distrito"],
            "Comunidade": comm,
            "Meta CAF": t["CAF"],
            "CAF Realizados": caf_alc,
            "% CAF": round(caf_alc / t["CAF"] * 100, 1) if t["CAF"] > 0 else 0,
            "Meta Machambas": t["Machambas"],
            "Machambas Realizadas": mach_alc,
            "% Machambas": round(mach_alc / t["Machambas"] * 100, 1) if t["Machambas"] > 0 else 0,
            "Faltam CAF": t["CAF"] - caf_alc,
            "Faltam Machambas": t["Machambas"] - mach_alc,
        })
    return pd.DataFrame(rows)

def get_technician_stats(caf_df, maf_df):
    result = None
    col_caf = "Nome do Inquirido?"
    col_maf = "Nome do Inqueridor?"
    if not caf_df.empty and col_caf in caf_df.columns:
        t = caf_df[col_caf].value_counts().reset_index()
        t.columns = ["Técnico", "CAF"]
        result = t
    if not maf_df.empty and col_maf in maf_df.columns:
        t = maf_df[col_maf].value_counts().reset_index()
        t.columns = ["Técnico", "MAF"]
        result = t if result is None else result.merge(t, on="Técnico", how="outer")
    if result is None:
        return pd.DataFrame()
    result = result.fillna(0)
    for c in ["CAF", "MAF"]:
        if c in result.columns:
            result[c] = result[c].astype(int)
    cols_sum = [c for c in ["CAF", "MAF"] if c in result.columns]
    result["Total"] = sum(result[c] for c in cols_sum)
    return result.sort_values("Total", ascending=False)

# =========================================================
# FUNÇÃO PARA CRIAR GRÁFICO DE COMPARAÇÃO (VERSÃO COMPATÍVEL)
# =========================================================

def create_comparison_chart(df, distrito, metric):
    df_dist = df[df["Distrito"] == distrito].copy()
    if df_dist.empty:
        return None
    
    if metric == "CAF":
        meta_col = "Meta CAF"
        real_col = "CAF Realizados"
        pct_col = "% CAF"
        title = "{} - Comparação de Inquéritos CAF por Comunidade".format(distrito)
        y_title = "Número de Inquéritos CAF"
        color_meta = "#c8dfe8"
        color_real = "#1a5f7a"
    else:
        meta_col = "Meta Machambas"
        real_col = "Machambas Realizadas"
        pct_col = "% Machambas"
        title = "{} - Comparação de Machambas por Comunidade".format(distrito)
        y_title = "Número de Machambas"
        color_meta = "#c8dfe8"
        color_real = "#e07b39"
    
    df_dist = df_dist.sort_values("Comunidade")
    
    fig = go.Figure()
    
    # Barras para Meta
    fig.add_trace(go.Bar(
        x=df_dist["Comunidade"],
        y=df_dist[meta_col],
        name="Meta (Previsto)",
        marker_color=color_meta,
        text=df_dist[meta_col],
        textposition="outside",
        textfont=dict(size=11, color="#333"),
        hoverinfo="x+y",
        hoverlabel=dict(bgcolor="white")
    ))
    
    # Barras para Realizado
    fig.add_trace(go.Bar(
        x=df_dist["Comunidade"],
        y=df_dist[real_col],
        name="Realizado",
        marker_color=color_real,
        text=df_dist[real_col],
        textposition="outside",
        textfont=dict(size=11, color=color_real),
        hoverinfo="x+y",
        hoverlabel=dict(bgcolor="white")
    ))
    
    # Adicionar anotações com percentuais
    for i, row in df_dist.iterrows():
        max_val = max(row[meta_col], row[real_col])
        offset = max_val * 0.05 if max_val > 0 else 5
        fig.add_annotation(
            x=row["Comunidade"],
            y=row[real_col] + offset,
            text="{}%".format(row[pct_col]),
            showarrow=False,
            font=dict(size=11, color=color_real),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#ddd",
            borderwidth=1,
            borderpad=2
        )
    
    # Configuração do layout
    fig.update_layout(
        title=title,
        barmode="group",
        height=450,
        xaxis_title="Comunidade",
        yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_tickangle=-45,
        plot_bgcolor="white",
        hovermode="x"
    )
    
    # Configurar grid do eixo Y
    fig.layout.yaxis.gridcolor = "#e9ecef"
    fig.layout.yaxis.gridwidth = 1
    fig.layout.yaxis.showgrid = True
    
    return fig

# =========================================================
# FUNÇÃO PARA TABELA RESUMO POR COMUNIDADE
# =========================================================

def display_community_table(df, distrito):
    df_dist = df[df["Distrito"] == distrito].copy()
    if df_dist.empty:
        st.info("Não há dados para {}".format(distrito))
        return
    
    display_cols = ["Comunidade", "Meta CAF", "CAF Realizados", "% CAF", "Faltam CAF", 
                   "Meta Machambas", "Machambas Realizadas", "% Machambas", "Faltam Machambas"]
    df_display = df_dist[display_cols].copy()
    
    total_row = {
        "Comunidade": "**TOTAL**",
        "Meta CAF": df_dist["Meta CAF"].sum(),
        "CAF Realizados": df_dist["CAF Realizados"].sum(),
        "% CAF": round(df_dist["CAF Realizados"].sum() / df_dist["Meta CAF"].sum() * 100, 1) if df_dist["Meta CAF"].sum() > 0 else 0,
        "Faltam CAF": df_dist["Faltam CAF"].sum(),
        "Meta Machambas": df_dist["Meta Machambas"].sum(),
        "Machambas Realizadas": df_dist["Machambas Realizadas"].sum(),
        "% Machambas": round(df_dist["Machambas Realizadas"].sum() / df_dist["Meta Machambas"].sum() * 100, 1) if df_dist["Meta Machambas"].sum() > 0 else 0,
        "Faltam Machambas": df_dist["Faltam Machambas"].sum(),
    }
    df_display = pd.concat([df_display, pd.DataFrame([total_row])], ignore_index=True)
    
    st.dataframe(df_display)

# =========================================================
# CARREGAR DADOS
# =========================================================

caf_df = load_caf()
maf_df = load_maf()
s4_df = load_survey4()

if caf_df.empty:
    st.error("Não foi possível carregar os dados de CAF. Verifique a pasta 'data/'.")
    st.stop()

daily_df, all_submissions_df = get_daily_progress(caf_df, maf_df)
comm_df = get_community_progress(caf_df)
tech_df = get_technician_stats(caf_df, maf_df)

# =========================================================
# HEADER
# =========================================================

st.markdown(
    "<div class='main-header'>"
    "<h1>📊 FDN Dashboard - Progresso dos Levantamentos</h1>"
    "<p>Monitorização CAF + MAF | Mecubúri e Ribáuè | Atualizado: {}</p>"
    "</div>".format(datetime.now().strftime("%d/%m/%Y %H:%M")),
    unsafe_allow_html=True
)

# =========================================================
# KPI CARDS
# =========================================================

total_caf = len(caf_df)
total_maf = len(maf_df)
total_target = sum(DISTRICT_TARGETS.values())
pct_caf = round(total_caf / total_target * 100, 1) if total_target > 0 else 0

mach_col = "Quantas machambas tem o Chefe do Agregado?"
total_machambas = int(caf_df[mach_col].sum()) if mach_col in caf_df.columns else 0
total_mach_target = sum(DISTRICT_MACHAMBA_TARGETS.values())
pct_mach = round(total_machambas / total_mach_target * 100, 1) if total_mach_target > 0 else 0

today = datetime.now().date()
if not daily_df.empty:
    today_data = daily_df[daily_df["date"] == today]
    recrutados_hoje = int(today_data["Total"].sum()) if not today_data.empty else 0
else:
    recrutados_hoje = 0

if not daily_df.empty:
    start_of_week = today - timedelta(days=today.weekday())
    week_data = daily_df[daily_df["date"] >= start_of_week]
    recrutados_semana = int(week_data["Total"].sum()) if not week_data.empty else 0
else:
    recrutados_semana = 0

st.markdown('<div class="section-title">📊 Indicadores Gerais</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(
        "<div class='stat-card'><div class='stat-number'>{}</div>"
        "<div class='stat-label'>CAF Totais</div>"
        "<div class='stat-sub'>Meta: {} | {}%</div></div>".format(total_caf, total_target, pct_caf),
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        "<div class='stat-card'><div class='stat-number'>{}</div>"
        "<div class='stat-label'>MAF Totais</div>"
        "<div class='stat-sub'>Membros do Agregado</div></div>".format(total_maf),
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        "<div class='stat-card'><div class='stat-number'>{}</div>"
        "<div class='stat-label'>Machambas</div>"
        "<div class='stat-sub'>Meta: {} | {}%</div></div>".format(total_machambas, total_mach_target, pct_mach),
        unsafe_allow_html=True
    )
with c4:
    st.markdown(
        "<div class='stat-card'><div class='stat-number'>{}</div>"
        "<div class='stat-label'>Hoje</div>"
        "<div class='stat-sub'>Novos registos</div></div>".format(recrutados_hoje),
        unsafe_allow_html=True
    )
with c5:
    st.markdown(
        "<div class='stat-card'><div class='stat-number'>{}</div>"
        "<div class='stat-label'>Esta semana</div>"
        "<div class='stat-sub'>Últimos 7 dias</div></div>".format(recrutados_semana),
        unsafe_allow_html=True
    )
with c6:
    n_tecnicos = caf_df["Nome do Inquirido?"].nunique() if "Nome do Inquirido?" in caf_df.columns else 0
    st.markdown(
        "<div class='stat-card'><div class='stat-number'>{}</div>"
        "<div class='stat-label'>Técnicos</div>"
        "<div class='stat-sub'>Activos no campo</div></div>".format(n_tecnicos),
        unsafe_allow_html=True
    )

# =========================================================
# BARRAS DE PROGRESSO GERAIS
# =========================================================

st.markdown('<div class="section-title">🎯 Progresso Geral em Relação à Meta</div>', unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    pw = min(pct_caf, 100)
    st.markdown(
        "<p style='margin:0;font-size:0.9rem;font-weight:600;'>CAF: {}/{} ({}%)</p>"
        "<div class='progress-bar-wrap'><div class='progress-bar-fill' style='width:{}%;'></div></div>".format(total_caf, total_target, pct_caf, pw),
        unsafe_allow_html=True
    )
with col_b:
    pm = min(pct_mach, 100)
    st.markdown(
        "<p style='margin:0;font-size:0.9rem;font-weight:600;'>Machambas: {}/{} ({}%)</p>"
        "<div class='progress-bar-wrap'><div class='progress-bar-fill' style='width:{}%;background:#e07b39;'></div></div>".format(total_machambas, total_mach_target, pct_mach, pm),
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================================================
# GRÁFICO: RESUMO POR DISTRITO
# =========================================================

st.markdown('<div class="section-title">🏛️ Resumo por Distrito</div>', unsafe_allow_html=True)

if not comm_df.empty:
    dist_summary = comm_df.groupby("Distrito").agg({
        "Meta CAF": "sum",
        "CAF Realizados": "sum",
        "Meta Machambas": "sum",
        "Machambas Realizadas": "sum"
    }).reset_index()
    
    dist_summary["Pct CAF"] = (dist_summary["CAF Realizados"] / dist_summary["Meta CAF"] * 100).round(1)
    dist_summary["Pct Machambas"] = (dist_summary["Machambas Realizadas"] / dist_summary["Meta Machambas"] * 100).round(1)
    
    # Gráfico CAF por distrito
    fig_dist_caf = go.Figure()
    fig_dist_caf.add_trace(go.Bar(
        name="Meta CAF",
        x=dist_summary["Distrito"],
        y=dist_summary["Meta CAF"],
        marker_color="#c8dfe8",
        text=dist_summary["Meta CAF"],
        textposition="outside"
    ))
    fig_dist_caf.add_trace(go.Bar(
        name="CAF Realizados",
        x=dist_summary["Distrito"],
        y=dist_summary["CAF Realizados"],
        marker_color="#1a5f7a",
        text=dist_summary["CAF Realizados"],
        textposition="outside"
    ))
    fig_dist_caf.update_layout(
        title="CAF: Meta vs Realizados por Distrito",
        barmode="group",
        height=400,
        yaxis_title="Número de CAF"
    )
    st.plotly_chart(fig_dist_caf, use_container_width=True)
    
    # Gráfico Machambas por distrito
    fig_dist_mach = go.Figure()
    fig_dist_mach.add_trace(go.Bar(
        name="Meta Machambas",
        x=dist_summary["Distrito"],
        y=dist_summary["Meta Machambas"],
        marker_color="#c8dfe8",
        text=dist_summary["Meta Machambas"],
        textposition="outside"
    ))
    fig_dist_mach.add_trace(go.Bar(
        name="Machambas Realizadas",
        x=dist_summary["Distrito"],
        y=dist_summary["Machambas Realizadas"],
        marker_color="#e07b39",
        text=dist_summary["Machambas Realizadas"],
        textposition="outside"
    ))
    fig_dist_mach.update_layout(
        title="Machambas: Meta vs Realizadas por Distrito",
        barmode="group",
        height=400,
        yaxis_title="Número de Machambas"
    )
    st.plotly_chart(fig_dist_mach, use_container_width=True)

# =========================================================
# GRÁFICOS PRINCIPAIS: POR DISTRITO E COMUNIDADE
# =========================================================

st.markdown('<div class="section-title">📍 Progresso Detalhado por Distrito e Comunidade</div>', unsafe_allow_html=True)

if not comm_df.empty:
    # Distrito de Mecubúri
    st.markdown("### 🏛️ Distrito de Mecubúri")
    
    fig_mec_caf = create_comparison_chart(comm_df, "Distrito de Mecubúri", "CAF")
    if fig_mec_caf:
        st.plotly_chart(fig_mec_caf, use_container_width=True)
    
    fig_mec_mach = create_comparison_chart(comm_df, "Distrito de Mecubúri", "Machambas")
    if fig_mec_mach:
        st.plotly_chart(fig_mec_mach, use_container_width=True)
    
    with st.expander("📋 Ver Tabela Detalhada - Mecubúri"):
        display_community_table(comm_df, "Distrito de Mecubúri")
    
    st.markdown("---")
    
    # Distrito de Ribáuè
    st.markdown("### 🏛️ Distrito de Ribáuè")
    
    fig_rib_caf = create_comparison_chart(comm_df, "Distrito de Ribáuè", "CAF")
    if fig_rib_caf:
        st.plotly_chart(fig_rib_caf, use_container_width=True)
    
    fig_rib_mach = create_comparison_chart(comm_df, "Distrito de Ribáuè", "Machambas")
    if fig_rib_mach:
        st.plotly_chart(fig_rib_mach, use_container_width=True)
    
    with st.expander("📋 Ver Tabela Detalhada - Ribáuè"):
        display_community_table(comm_df, "Distrito de Ribáuè")
    
else:
    st.warning("Não foi possível calcular o progresso por comunidade. Verifique os nomes das comunidades nos dados.")

st.markdown("---")

# =========================================================
# GRÁFICO: EVOLUÇÃO ACUMULADA
# =========================================================

st.markdown('<div class="section-title">📈 Evolução Acumulada dos Levantamentos</div>', unsafe_allow_html=True)

if not daily_df.empty:
    fig_cumulative = go.Figure()
    fig_cumulative.add_trace(go.Scatter(
        x=daily_df["date"],
        y=daily_df["Total_Acumulado"],
        name="Total Acumulado (CAF+MAF)",
        mode="lines+markers",
        line=dict(color="#1a5f7a", width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(26, 95, 122, 0.1)'
    ))
    fig_cumulative.add_hline(
        y=total_target,
        line_dash="dash",
        line_color="#e07b39",
        annotation_text="Meta CAF: {}".format(total_target),
        annotation_position="bottom right"
    )
    fig_cumulative.update_layout(
        height=400,
        title="Progresso Acumulado de CAF em Direção à Meta",
        xaxis_title="Data",
        yaxis_title="Número Acumulado de CAF",
        hovermode="x"
    )
    st.plotly_chart(fig_cumulative, use_container_width=True)

# =========================================================
# GRÁFICO: LEVANTAMENTOS DIÁRIOS
# =========================================================

st.markdown('<div class="section-title">📊 Levantamentos Diários</div>', unsafe_allow_html=True)
if not daily_df.empty:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(x=daily_df["date"], y=daily_df["CAF"], name="CAF", marker_color="#1a5f7a"))
        fig_daily.add_trace(go.Bar(x=daily_df["date"], y=daily_df["MAF"], name="MAF", marker_color="#4aa3c2"))
        fig_daily.add_trace(go.Scatter(x=daily_df["date"], y=daily_df["Total"], name="Total Diário", mode="lines+markers", line=dict(color="#e07b39", width=2)))
        fig_daily.update_layout(barmode="group", height=400, xaxis_title="Data", yaxis_title="Número de Formulários", hovermode="x")
        st.plotly_chart(fig_daily, use_container_width=True)
    with col_right:
        st.markdown("**📋 Resumo Últimos 7 Dias**")
        last_7 = daily_df.tail(7).copy()
        last_7["date"] = pd.to_datetime(last_7["date"]).dt.strftime("%d/%m")
        last_7 = last_7[["date", "CAF", "MAF", "Total"]]
        last_7.columns = ["Data", "CAF", "MAF", "Total"]
        st.dataframe(last_7)

# =========================================================
# GRÁFICO: DESEMPENHO POR TÉCNICO
# =========================================================

st.markdown('<div class="section-title">👥 Desempenho por Técnico</div>', unsafe_allow_html=True)
if not tech_df.empty:
    col1, col2 = st.columns([2, 1])
    with col1:
        top_tech = tech_df.head(10).sort_values("Total", ascending=True)
        fig_tech = go.Figure()
        if "CAF" in top_tech.columns:
            fig_tech.add_trace(go.Bar(y=top_tech["Técnico"], x=top_tech["CAF"], name="CAF", orientation='h', marker_color="#1a5f7a"))
        if "MAF" in top_tech.columns:
            fig_tech.add_trace(go.Bar(y=top_tech["Técnico"], x=top_tech["MAF"], name="MAF", orientation='h', marker_color="#4aa3c2"))
        fig_tech.update_layout(barmode="stack", height=400, title="Top 10 Técnicos (CAF + MAF)", xaxis_title="Número de Formulários", yaxis_title="Técnico")
        st.plotly_chart(fig_tech, use_container_width=True)
    with col2:
        st.markdown("**🏆 Ranking de Técnicos**")
        show_cols = ["Técnico", "Total"] + [c for c in ["CAF", "MAF"] if c in tech_df.columns]
        st.dataframe(tech_df[show_cols].head(10))

# =========================================================
# GRÁFICO: SEXO DOS CHEFES
# =========================================================

st.markdown('<div class="section-title">👨‍👩‍👧 Distribuição por Sexo</div>', unsafe_allow_html=True)
gender_col = "Sexo do chefe de agregado"
if gender_col in caf_df.columns:
    g = caf_df[gender_col].value_counts().reset_index()
    g.columns = ["Sexo", "Total"]
    col1, col2 = st.columns([1, 2])
    with col1:
        fig_pie = go.Figure(data=[go.Pie(labels=g["Sexo"], values=g["Total"], hole=0.5, marker_colors=["#1a5f7a", "#e07b39"])])
        fig_pie.update_layout(height=300, title="Distribuição por Sexo")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        meta_h = sum(v["H"] for v in COMMUNITY_TARGETS_CAF.values())
        meta_m = sum(v["M"] for v in COMMUNITY_TARGETS_CAF.values())
        alc_h = int(g[g["Sexo"] == "Masculino"]["Total"].sum()) if "Masculino" in g["Sexo"].values else 0
        alc_m = int(g[g["Sexo"] == "Feminino"]["Total"].sum()) if "Feminino" in g["Sexo"].values else 0
        pct_h = round(alc_h / meta_h * 100, 1) if meta_h > 0 else 0
        pct_m = round(alc_m / meta_m * 100, 1) if meta_m > 0 else 0
        
        st.markdown("**Alcançados vs Meta por Sexo**")
        st.markdown(
            "<p style='font-weight:600;margin-bottom:2px;'>Homens: {}/{} ({}%)</p>"
            "<div class='progress-bar-wrap'><div class='progress-bar-fill' style='width:{}%;background:#1a5f7a;'></div></div>"
            "<br>"
            "<p style='font-weight:600;margin-bottom:2px;'>Mulheres: {}/{} ({}%)</p>"
            "<div class='progress-bar-wrap'><div class='progress-bar-fill' style='width:{}%;background:#e07b39;'></div></div>"
            .format(alc_h, meta_h, pct_h, min(pct_h, 100), alc_m, meta_m, pct_m, min(pct_m, 100)),
            unsafe_allow_html=True
        )

# =========================================================
# TABELA: ÚLTIMAS SUBMISSÕES
# =========================================================

st.markdown('<div class="section-title">📝 Últimas Submissões (CAF)</div>', unsafe_allow_html=True)
wanted = ["Data de submissão", "Nome do Inquirido?", "Qual é o nome do Chefe do Agregado Familiar?", 
          "Em que Distrito está a realizar o levantamento??", "Indique o Povoado/comunidade em que o agregado familiar está localizado.",
          "Sexo do chefe de agregado", "Quantas machambas tem o Chefe do Agregado?"]
valid = [c for c in wanted if c in caf_df.columns]
if valid:
    last = caf_df[valid].copy().sort_values("Data de submissão", ascending=False).head(20)
    rename = {
        "Qual é o nome do Chefe do Agregado Familiar?": "Chefe do Agregado",
        "Em que Distrito está a realizar o levantamento??": "Distrito",
        "Indique o Povoado/comunidade em que o agregado familiar está localizado.": "Comunidade",
        "Nome do Inquirido?": "Técnico",
        "Data de submissão": "Data",
        "Sexo do chefe de agregado": "Sexo",
        "Quantas machambas tem o Chefe do Agregado?": "Machambas"
    }
    last = last.rename(columns=rename)
    st.dataframe(last)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("FDN Dashboard | Actualizado: {} | CAF: {} | MAF: {} | Survey4: {}".format(
    datetime.now().strftime("%d/%m/%Y %H:%M:%S"), total_caf, total_maf, len(s4_df)))