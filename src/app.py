import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Análise de Dados Excel",
    page_icon="📊",
    layout="wide"
)

# Função para obter o caminho base do projeto
def get_project_root():
    """Retorna o caminho base do projeto"""
    script_path = Path(__file__).resolve()  # Caminho absoluto do script atual
    return script_path.parent.parent  # Volta dois níveis (src -> raiz do projeto)

# Função para listar arquivos Excel disponíveis
def list_excel_files():
    project_root = get_project_root()
    data_dir = project_root / "data"
    excel_files = []
    
    if data_dir.exists():
        for year_dir in data_dir.glob("*"):
            if year_dir.is_dir():
                for excel_file in year_dir.glob("*.xlsx"):
                    # Armazena o caminho completo e o nome para exibição
                    excel_files.append({
                        'path': excel_file,
                        'display_name': f"{excel_file.parent.name}/{excel_file.stem}"
                    })
    return sorted(excel_files, key=lambda x: x['display_name'])

# Função para carregar dados
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

# Função para validar e inferir tipos de dados
def validate_data_types(df):
    """
    Analisa e valida os tipos de dados de cada coluna do DataFrame
    Retorna um dicionário com informações sobre cada coluna
    """
    analysis = {}
    
    for column in df.columns:
        col_data = df[column]
        analysis[column] = {
            'atual_tipo': str(col_data.dtype),
            'sugerido_tipo': None,
            'problemas': [],
            'exemplos': col_data.head(3).tolist(),
            'valores_nulos': col_data.isna().sum(),
            'valores_unicos': col_data.nunique(),
            'status': '✅' # Default status
        }
        
        # Tenta inferir se é data
        if col_data.dtype == 'object':
            try:
                pd.to_datetime(col_data, errors='raise')
                analysis[column]['sugerido_tipo'] = 'DATA'
                if col_data.dtype != 'datetime64[ns]':
                    analysis[column]['problemas'].append('Coluna pode ser convertida para DATA')
                    analysis[column]['status'] = '⚠️'
            except:
                # Tenta inferir se é número
                numeric_count = sum(str(x).replace('.','',1).replace('-','',1).isdigit() for x in col_data.dropna())
                if numeric_count / len(col_data.dropna()) > 0.8:
                    analysis[column]['sugerido_tipo'] = 'NÚMERO'
                    analysis[column]['problemas'].append('Coluna pode ser convertida para NÚMERO')
                    analysis[column]['status'] = '⚠️'
                else:
                    analysis[column]['sugerido_tipo'] = 'TEXTO'
        
        # Validações específicas
        if col_data.dtype in ['int64', 'float64']:
            analysis[column]['sugerido_tipo'] = 'NÚMERO'
            # Verifica valores extremos
            if col_data.dropna().std() > col_data.dropna().mean() * 3:
                analysis[column]['problemas'].append('Possíveis outliers detectados')
                analysis[column]['status'] = '⚠️'
        
        elif col_data.dtype == 'datetime64[ns]':
            analysis[column]['sugerido_tipo'] = 'DATA'
            # Verifica datas futuras
            if col_data.max() > pd.Timestamp.now():
                analysis[column]['problemas'].append('Datas futuras detectadas')
                analysis[column]['status'] = '⚠️'
        
        # Verifica valores nulos
        if analysis[column]['valores_nulos'] > 0:
            analysis[column]['problemas'].append(f'{analysis[column]["valores_nulos"]} valores nulos encontrados')
            analysis[column]['status'] = '⚠️'
            
        # Se não houver problemas
        if not analysis[column]['problemas']:
            analysis[column]['problemas'].append('Nenhum problema encontrado')
            
    return analysis

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
            format_func=lambda x: x['display_name']
        )
        
        if selected_file:
            df = load_data(selected_file['path'])
            
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
    # Tabs para organizar o conteúdo
    tab1, tab2, tab3 = st.tabs(["📊 Análise de Dados", "🔍 Qualidade dos Dados", "📈 Visualizações"])
    
    with tab1:
        # Visão geral dos dados
        st.header("📋 Visão Geral dos Dados")
        st.dataframe(df.head(1000))
    
    with tab2:
        st.header("🔍 Análise de Qualidade dos Dados")
        
        # Executa a validação
        data_analysis = validate_data_types(df)
        
        # Cria um DataFrame com a análise para melhor visualização
        analysis_data = []
        for col, info in data_analysis.items():
            analysis_data.append({
                'Coluna': col,
                'Status': info['status'],
                'Tipo Atual': info['atual_tipo'],
                'Tipo Sugerido': info['sugerido_tipo'],
                'Valores Únicos': info['valores_unicos'],
                'Valores Nulos': info['valores_nulos'],
                'Exemplos': str(info['exemplos']),
                'Problemas': '\n'.join(info['problemas'])
            })
        
        df_analysis = pd.DataFrame(analysis_data)
        
        # Mostra estatísticas gerais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Colunas", len(df.columns))
        with col2:
            problemas = sum(1 for col in data_analysis.values() if col['status'] == '⚠️')
            st.metric("Colunas com Problemas", problemas)
        with col3:
            st.metric("Linhas no Dataset", len(df))
        
        # Mostra a análise detalhada
        st.dataframe(df_analysis, use_container_width=True)
        
        # Sugestões de correção
        if problemas > 0:
            st.header("🛠️ Sugestões de Correção")
            for col, info in data_analysis.items():
                if info['status'] == '⚠️':
                    st.write(f"**{col}**:")
                    for problema in info['problemas']:
                        st.write(f"- {problema}")
                    if info['sugerido_tipo'] == 'DATA':
                        st.code(f"df['{col}'] = pd.to_datetime(df['{col}'])")
                    elif info['sugerido_tipo'] == 'NÚMERO':
                        st.code(f"df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce')")
    
    with tab3:
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
