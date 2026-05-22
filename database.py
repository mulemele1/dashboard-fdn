# database.py
import pandas as pd
import os
from datetime import datetime
import streamlit as st
from config import DISTRICT_TARGETS, COLUMN_MAPPING, ENUMERATORS

DATA_DIR = "data"

@st.cache_data(ttl=300)
def load_caf1():
    """Carrega CAF Parte 1 (Chefes de Agregado)"""
    file_path = os.path.join(DATA_DIR, "results-survey666877.csv")
    df = pd.read_csv(file_path, encoding='utf-8')
    # Filtrar linhas vazias/submissões incompletas
    df = df[df['Data de submissão'].notna()]
    return df

@st.cache_data(ttl=300)
def load_caf2():
    """Carrega CAF Parte 2 (Membros, pecuária, carvão, etc.)"""
    file_path = os.path.join(DATA_DIR, "results-survey163198.csv")
    df = pd.read_csv(file_path, encoding='utf-8')
    df = df[df['Data de submissão'].notna()]
    return df

@st.cache_data(ttl=300)
def load_maf():
    """Carrega MAF (Membros do agregado)"""
    file_path = os.path.join(DATA_DIR, "results-survey757779.csv")
    df = pd.read_csv(file_path, encoding='utf-8')
    df = df[df['Date submitted'].notna()]
    return df

def get_head_summary():
    """Resumo dos Chefes de Agregado levantados"""
    df = load_caf1()
    
    # Contagem por distrito
    district_counts = df[COLUMN_MAPPING['caf1']['district']].value_counts().to_dict()
    
    # Preparar dados para gráfico Alcançados vs Previstos
    targets = []
    achieved = []
    districts_list = []
    
    for district in DISTRICT_TARGETS.keys():
        districts_list.append(district)
        targets.append(DISTRICT_TARGETS[district])
        achieved.append(district_counts.get(district, 0))
    
    return {
        "total_heads": len(df),
        "by_district": district_counts,
        "targets": targets,
        "achieved": achieved,
        "districts": districts_list,
        "gender_counts": df[COLUMN_MAPPING['caf1']['gender']].value_counts().to_dict(),
        "age_stats": df[COLUMN_MAPPING['caf1']['age']].describe().to_dict()
    }

def get_members_summary():
    """Resumo dos Membros do Agregado (CAF2 + MAF)"""
    caf1 = load_caf1()
    maf = load_maf()
    
    # Cada linha do MAF é um membro
    total_members = len(maf)
    
    # Relações mais comuns
    relations = maf[COLUMN_MAPPING['maf']['member_relation']].value_counts().head(10).to_dict()
    
    # Faixas etárias
    ages = maf[COLUMN_MAPPING['maf']['member_age']].dropna()
    
    def age_group(age):
        if age < 5: return "0-4 anos"
        if age < 15: return "5-14 anos"
        if age < 25: return "15-24 anos"
        if age < 60: return "25-59 anos"
        return "60+ anos"
    
    age_groups = ages.apply(age_group).value_counts().to_dict()
    
    return {
        "total_members": total_members,
        "relations": relations,
        "age_groups": age_groups,
        "avg_age": ages.mean() if len(ages) > 0 else 0
    }

def get_enumerator_daily_summary():
    """Resumo de inquéritos por técnico por dia"""
    caf1 = load_caf1()
    maf = load_maf()
    
    # Combinar ambos os inquéritos
    caf1['survey_type'] = 'CAF'
    caf1['date'] = pd.to_datetime(caf1['Data de submissão']).dt.date
    caf1['enumerator'] = caf1[COLUMN_MAPPING['caf1']['inquirer']]
    
    maf['survey_type'] = 'MAF'
    maf['date'] = pd.to_datetime(maf['Date submitted']).dt.date
    maf['enumerator'] = maf[COLUMN_MAPPING['maf']['inquirer']]
    
    # Combinar dataframes
    all_surveys = pd.concat([
        caf1[['enumerator', 'date', 'survey_type']],
        maf[['enumerator', 'date', 'survey_type']]
    ], ignore_index=True)
    
    # Total por técnico
    total_by_enumerator = all_surveys.groupby('enumerator').size().to_dict()
    
    # Daily por técnico
    daily = all_surveys.groupby(['enumerator', 'date']).size().reset_index(name='count')
    
    # Daily total (todos técnicos)
    daily_total = all_surveys.groupby('date').size().reset_index(name='total')
    daily_total = daily_total.sort_values('date')
    
    return {
        "total_by_enumerator": total_by_enumerator,
        "daily_by_enumerator": daily,
        "daily_total": daily_total
    }

def get_daily_progress():
    """Levantamentos diários (gráfico de barras como no anexo)"""
    caf1 = load_caf1()
    maf = load_maf()
    
    # Data de submissão como data
    caf1['date'] = pd.to_datetime(caf1['Data de submissão']).dt.date
    maf['date'] = pd.to_datetime(maf['Date submitted']).dt.date
    
    # Contagem diária
    daily_caf = caf1.groupby('date').size().reset_index(name='caf')
    daily_maf = maf.groupby('date').size().reset_index(name='maf')
    
    # Combinar
    all_dates = pd.concat([daily_caf['date'], daily_maf['date']]).unique()
    result = pd.DataFrame({'date': sorted(all_dates)})
    result = result.merge(daily_caf, on='date', how='left')
    result = result.merge(daily_maf, on='date', how='left')
    result['caf'] = result['caf'].fillna(0).astype(int)
    result['maf'] = result['maf'].fillna(0).astype(int)
    result['total'] = result['caf'] + result['maf']
    
    return result

def get_cumulative_progress():
    """Progresso cumulativo ao longo do tempo"""
    daily = get_daily_progress()
    daily['cumulative_caf'] = daily['caf'].cumsum()
    daily['cumulative_maf'] = daily['maf'].cumsum()
    daily['cumulative_total'] = daily['total'].cumsum()
    return daily

def get_district_progress():
    """Progresso por distrito (Alcançados vs Previstos)"""
    df = load_caf1()
    district_col = COLUMN_MAPPING['caf1']['district']
    
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

def get_gps_data():
    """Dados GPS para o mapa dinâmico"""
    df = load_caf1()
    gps_col = COLUMN_MAPPING['caf1']['gps']
    
    # Filtrar linhas com GPS
    gps_df = df[df[gps_col].notna() & (df[gps_col] != "")].copy()
    
    def parse_gps(gps_str):
        """Parse GPS no formato 'latitude;longitude' ou 'latitude, longitude'"""
        if pd.isna(gps_str):
            return None, None
        # Substituir vírgula por ponto e ponto e vírgula por separador
        cleaned = str(gps_str).replace(',', '.').replace(';', ',')
        parts = cleaned.split(',')
        if len(parts) >= 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                # Validar se está em Moçambique
                if -27 <= lat <= -10 and 30 <= lon <= 41:
                    return lat, lon
            except:
                pass
        return None, None
    
    gps_df['lat'], gps_df['lon'] = zip(*gps_df[gps_col].apply(parse_gps))
    gps_df = gps_df.dropna(subset=['lat', 'lon'])
    
    return gps_df

def get_livestock_summary():
    """Resumo da pecuária (CAF Parte 2)"""
    df = load_caf2()
    
    # Colunas de animais
    animal_cols = ['Indique o tipo e a quantidade de animais que o Agregado Familiar tem. [Bois]',
                   'Indique o tipo e a quantidade de animais que o Agregado Familiar tem. [Cabritos]',
                   'Indique o tipo e a quantidade de animais que o Agregado Familiar tem. [Galinhas]']
    
    livestock_summary = {}
    for col in animal_cols:
        if col in df.columns:
            # Contar agregados que têm este animal
            count = df[df[col].notna() & (df[col] != "")].shape[0]
            livestock_summary[col.split('[')[1].split(']')[0]] = count
    
    return livestock_summary

def get_recent_responses(limit=20):
    """Últimas respostas submetidas"""
    caf1 = load_caf1()
    caf1['survey'] = 'CAF Parte 1'
    caf1['date'] = pd.to_datetime(caf1['Data de submissão'])
    caf1['respondent'] = caf1[COLUMN_MAPPING['caf1']['head_name']]
    
    recent = caf1.nlargest(limit, 'date')[['date', 'respondent', 'survey']]
    return recent