# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="FDN Dashboard - Progresso dos Levantamentos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a5f7a 0%, #0d3b4a 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #1a5f7a;
    }
    .stat-number {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1a5f7a;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .progress-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURAÇÕES
# ============================================
DATA_DIR = "data"

# Metas por distrito
DISTRICT_TARGETS = {
    "Distrito de Mecubúri": 150,
    "Distrito de Ribáuè": 120,
    "Distrito de Lalaua": 80,
}

# ============================================
# FUNÇÕES DE CARREGAMENTO
# ============================================
@st.cache(allow_output_mutation=True)
def load_caf1():
    """Carrega CAF Parte 1"""
    file_path = os.path.join(DATA_DIR, "results-survey666877.csv")
    if not os.path.exists(file_path):
        st.error(f"Ficheiro não encontrado: {file_path}")
        return pd.DataFrame()
    df = pd.read_csv(file_path, encoding='utf-8')
    df = df[df['Data de submissão'].notna()]
    return df

@st.cache(allow_output_mutation=True)
def load_caf2():
    """Carrega CAF Parte 2"""
    file_path = os.path.join(DATA_DIR, "results-survey163198.csv")
    if not os.path.exists(file_path):
        st.warning(f"Ficheiro não encontrado: {file_path}")
        return pd.DataFrame()
    df = pd.read_csv(file_path, encoding='utf-8')
    df = df[df['Data de submissão'].notna()]
    return df

@st.cache(allow_output_mutation=True)
def load_maf():
    """Carrega MAF"""
    file_path = os.path.join(DATA_DIR, "results-survey757779.csv")
    if not os.path.exists(file_path):
        st.warning(f"Ficheiro não encontrado: {file_path}")
        return pd.DataFrame()
    df = pd.read_csv(file_path, encoding='utf-8')
    df = df[df['Date submitted'].notna()]
    return df

def get_daily_progress():
    """Levantamentos diários"""
    caf1 = load_caf1()
    maf = load_maf()
    
    if caf1.empty and maf.empty:
        return pd.DataFrame()
    
    caf1['date'] = pd.to_datetime(caf1['Data de submissão']).dt.date
    maf['date'] = pd.to_datetime(maf['Date submitted']).dt.date
    
    daily_caf = caf1.groupby('date').size().reset_index(name='caf')
    daily_maf = maf.groupby('date').size().reset_index(name='maf')
    
    all_dates = pd.concat([daily_caf['date'], daily_maf['date']]).unique()
    result = pd.DataFrame({'date': sorted(all_dates)})
    result = result.merge(daily_caf, on='date', how='left')
    result = result.merge(daily_maf, on='date', how='left')
    result['caf'] = result['caf'].fillna(0).astype(int)
    result['maf'] = result['maf'].fillna(0).astype(int)
    result['total'] = result['caf'] + result['maf']
    
    return result

def get_district_progress():
    """Progresso por distrito"""
    df = load_caf1()
    if df.empty:
        return pd.DataFrame()
    
    district_col = "Em que Distrito está a realizar o levantamento??"
    achieved = df[district_col].value_counts().to_dict()
    
    result = []
    for district, target in DISTRICT_TARGETS.items():
        result.append({
            "Distrito": district,
            "Previstos": target,
            "Alcançados": achieved.get(district, 0),
            "Percentual": (achieved.get(district, 0) / target * 100) if target > 0 else 0
        })
    
    return pd.DataFrame(result)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>📊 FDN Dashboard - Progresso dos Levantamentos</h1>
    <p>Monitorização de Chefes de Agregado e Membros | CAF + MAF</p>
</div>
""", unsafe_allow_html=True)

# Carregar dados
caf1_df = load_caf1()
maf_df = load_maf()
daily_progress = get_daily_progress()
district_df = get_district_progress()

# Verificar se há dados
if caf1_df.empty:
    st.error("❌ Não foi possível carregar os dados. Verifique se os ficheiros CSV estão na pasta 'data/'")
    st.info("""
    **Solução:**
    1. Crie a pasta `data/` se não existir
    2. Coloque os seguintes ficheiros na pasta:
       - results-survey666877.csv
       - results-survey163198.csv
       - results-survey757779.csv
    3. Recarregue a página
    """)
    st.stop()

# ============================================
# KPI CARDS
# ============================================
total_heads = len(caf1_df)
total_members = len(maf_df)
total_target = sum(DISTRICT_TARGETS.values())
percentage = (total_heads / total_target * 100) if total_target > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_heads}</div>
        <div class="stat-label">Chefes de Agregado</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_members}</div>
        <div class="stat-label">Membros do Agregado</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{percentage:.1f}%</div>
        <div class="stat-label">Progresso Geral</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    unique_inquirers = caf1_df['Nome do Inquirido?'].nunique()
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{unique_inquirers}</div>
        <div class="stat-label">Técnicos Activos</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# GRÁFICO 1: Levantamentos Diários
# ============================================
st.subheader("📈 Levantamentos Diários")

if not daily_progress.empty:
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=daily_progress['date'],
        y=daily_progress['caf'],
        name='CAF',
        marker_color='#1a5f7a'
    ))
    
    fig.add_trace(go.Bar(
        x=daily_progress['date'],
        y=daily_progress['maf'],
        name='MAF',
        marker_color='#4aa3c2'
    ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title="Data",
        yaxis_title="Número de Questionários",
        legend_title="Tipo",
        height=400
    )
    
    st.plotly_chart(fig)
else:
    st.info("Sem dados diários disponíveis")

# ============================================
# GRÁFICO 2: Por Técnico
# ============================================
st.subheader("👥 Inquéritos por Técnico")

tech_counts = caf1_df['Nome do Inquirido?'].value_counts().reset_index()
tech_counts.columns = ['Técnico', 'Total']

if not tech_counts.empty:
    fig = px.bar(
        tech_counts,
        x='Técnico',
        y='Total',
        title="Total de CAFs por Técnico",
        color='Total',
        color_continuous_scale='Blues',
        text='Total'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig)

# ============================================
# GRÁFICO 3: Distritos
# ============================================
st.subheader("🗺️ Progresso por Distrito")

if not district_df.empty:
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=district_df['Distrito'],
        y=district_df['Previstos'],
        name='Previstos',
        marker_color='lightgray'
    ))
    
    fig.add_trace(go.Bar(
        x=district_df['Distrito'],
        y=district_df['Alcançados'],
        name='Alcançados',
        marker_color='#1a5f7a'
    ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title="Distrito",
        yaxis_title="Número de Chefes de Agregado",
        height=400
    )
    
    st.plotly_chart(fig)
    
    # Tabela
    st.dataframe(
        district_df.style.format({'Percentual': '{:.1f}%'}),
        
    )

# ============================================
# GRÁFICO 4: Sexo
# ============================================
st.subheader("👤 Sexo dos Chefes de Agregado")

gender_col = "Sexo do chefe de agregado"
if gender_col in caf1_df.columns:
    gender_counts = caf1_df[gender_col].value_counts().reset_index()
    gender_counts.columns = ['Sexo', 'Total']
    
    fig = px.pie(
        gender_counts,
        values='Total',
        names='Sexo',
        title="Distribuição por Sexo",
        color_discrete_sequence=['#1a5f7a', '#4aa3c2']
    )
    st.plotly_chart(fig)

# ============================================
# Tabela de Dados
# ============================================
st.subheader("📋 Últimas Submissões")

if not caf1_df.empty:
    display_df = caf1_df[['Data de submissão', 'Nome do Inquirido?', 'Qual é o nome do Chefe do Agregado Familiar?', 'Em que Distrito está a realizar o levantamento??']].copy()
    display_df.columns = ['Data', 'Técnico', 'Chefe do Agregado', 'Distrito']
    st.dataframe(display_df.head(20))

# ============================================
# RODAPÉ
# ============================================
st.markdown("---")
st.caption(f"FDN Dashboard | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")