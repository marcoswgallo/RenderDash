import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Análise de Dados Excel",
    page_icon="📊",
    layout="wide"
)

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

# Sidebar para upload e filtros
with st.sidebar:
    st.header("Configurações")
    uploaded_file = st.file_uploader("Carregar arquivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
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

# Layout principal
if 'df' in locals():
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

else:
    st.info("👈 Por favor, faça upload de um arquivo Excel na barra lateral para começar a análise.")
