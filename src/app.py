import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Análise de Dados Excel",
    page_icon="📊",
    layout="wide"
)

# Função para listar arquivos Excel disponíveis
def list_excel_files():
    data_dir = Path("data")
    excel_files = []
    for year_dir in data_dir.glob("*"):
        if year_dir.is_dir():
            for excel_file in year_dir.glob("*.xlsx"):
                excel_files.append(excel_file)
    return sorted(excel_files)

# Função para carregar dados
@st.cache_data
def load_data(file_path):
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

# Título principal
st.title("📊 Dashboard de Análise de Dados")

# Sidebar para seleção de arquivo
with st.sidebar:
    st.header("Configurações")
    
    # Lista os arquivos Excel disponíveis
    excel_files = list_excel_files()
    if excel_files:
        selected_file = st.selectbox(
            "Selecione o período:",
            excel_files,
            format_func=lambda x: x.stem  # Mostra apenas o nome do arquivo sem extensão
        )
        
        if selected_file:
            df = load_data(selected_file)
            
            if df is not None:
                # Mostra informações básicas
                st.write("### Informações do Dataset")
                st.write(f"Total de registros: {len(df):,}")
                st.write(f"Colunas disponíveis: {', '.join(df.columns)}")
                
                # Seleção de colunas para análise
                selected_columns = st.multiselect(
                    "Selecione as colunas para análise",
                    df.columns
                )
    else:
        st.warning("Nenhum arquivo Excel encontrado no diretório data.")

# Layout principal
if 'df' in locals() and df is not None:
    # Visão geral dos dados
    st.header("📋 Visão Geral dos Dados")
    st.dataframe(df.head(1000))  # Limitando a 1000 linhas para performance
    
    if selected_columns:
        # Análises básicas
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("📈 Estatísticas Descritivas")
            st.write(df[selected_columns].describe())
        
        with col2:
            st.header("📊 Gráfico de Distribuição")
            for col in selected_columns:
                if df[col].dtype in ['int64', 'float64']:
                    fig = px.histogram(df, x=col, title=f'Distribuição de {col}')
                    st.plotly_chart(fig, use_container_width=True)
                    
        # Análise temporal se houver uma coluna de data
        date_columns = df.select_dtypes(include=['datetime64']).columns
        if len(date_columns) > 0:
            st.header("📅 Análise Temporal")
            date_col = st.selectbox("Selecione a coluna de data:", date_columns)
            
            if date_col and len(selected_columns) > 0:
                numeric_cols = df[selected_columns].select_dtypes(include=['int64', 'float64']).columns
                for col in numeric_cols:
                    fig = px.line(df, x=date_col, y=col, title=f'Evolução de {col} ao longo do tempo')
                    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Selecione um arquivo na barra lateral para começar a análise.")
