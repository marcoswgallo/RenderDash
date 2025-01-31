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

# Função para pré-processar os dados
def preprocess_data(df):
    """
    Aplica correções automáticas nos dados
    """
    df = df.copy()  # Cria uma cópia para não modificar os dados originais
    
    # Conversão de datas
    date_columns = ['DATA_TOA', 'DATA', 'INÍCIO', 'FIM', 'DESLOCAMENTO']
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                st.warning(f"Não foi possível converter a coluna {col} para data")
    
    # Conversão de números
    numeric_columns = {
        'COP REVERTEU': 'float64',
        'LATIDUDE': 'float64',
        'LONGITUDE': 'float64',
        'COD': 'int64',
        'TIPO OS': 'int64',
        'VALOR TÉCNICO': 'float64',
        'VALOR EMPRESA': 'float64',
        'PONTO': 'float64'
    }
    
    for col, dtype in numeric_columns.items():
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
            except:
                st.warning(f"Não foi possível converter a coluna {col} para {dtype}")
    
    # Tratamento de valores nulos
    categorical_columns = ['BASE', 'SERVIÇO', 'HABILIDADE DE TRABALHO', 'STATUS ATIVIDADE', 
                         'PACOTE', 'CLIENTE', 'CIDADES', 'NODE', 'TECNICO', 'LOGIN', 
                         'SUPERVISOR', 'COD STATUS']
    
    for col in categorical_columns:
        if col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                st.warning(f"Coluna {col} tem {missing} valores nulos")
    
    return df

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
                
                # Adiciona botão para pré-processar os dados
                if st.button("🔄 Pré-processar Dados"):
                    with st.spinner("Aplicando correções..."):
                        df = preprocess_data(df)
                        st.success("Dados pré-processados com sucesso!")
    else:
        st.warning("Nenhum arquivo Excel encontrado no diretório data.")

# Layout principal
if 'df' in locals() and df is not None:
    # Tabs para organizar o conteúdo
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise de Dados", "🔍 Qualidade dos Dados", "📈 Análises e Visualizações", "📋 Dicionário de Dados"])
    
    with tab1:
        # Visão geral dos dados
        st.header("📋 Visão Geral dos Dados")
        st.dataframe(df.head(1000))
        
        # Informações adicionais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros", len(df))
        with col2:
            if 'DATA' in df.columns:
                try:
                    # Tenta converter para datetime se ainda não for
                    if not pd.api.types.is_datetime64_any_dtype(df['DATA']):
                        data_col = pd.to_datetime(df['DATA'], errors='coerce')
                    else:
                        data_col = df['DATA']
                    
                    periodo = f"{data_col.min().strftime('%d/%m/%Y')} até {data_col.max().strftime('%d/%m/%Y')}"
                except:
                    periodo = "N/A"
            else:
                periodo = "N/A"
            st.metric("Período", periodo)
        with col3:
            st.metric("Cidades Únicas", df['CIDADES'].nunique() if 'CIDADES' in df.columns else "N/A")
    
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
        st.header("📈 Análises e Visualizações")

        # Análises automáticas principais
        if 'DATA' in df.columns:
            try:
                # Converte DATA para datetime se necessário
                if not pd.api.types.is_datetime64_any_dtype(df['DATA']):
                    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
                
                # 1. Análise por dia da semana
                st.subheader("📅 Distribuição por Dia da Semana")
                dias_semana = {
                    0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta',
                    4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
                }
                df['Dia_Semana'] = df['DATA'].dt.dayofweek.map(dias_semana)
                fig_dias = px.bar(
                    df['Dia_Semana'].value_counts().reset_index(),
                    x='index',
                    y='Dia_Semana',
                    title='Quantidade de Atividades por Dia da Semana'
                )
                st.plotly_chart(fig_dias, use_container_width=True)
            except Exception as e:
                st.warning(f"Não foi possível gerar a análise por dia da semana: {e}")

        # 2. Análise por cidade
        if 'CIDADES' in df.columns:
            st.subheader("🌆 Top 10 Cidades")
            fig_cidades = px.bar(
                df['CIDADES'].value_counts().head(10).reset_index(),
                x='index',
                y='CIDADES',
                title='Top 10 Cidades com Mais Atividades'
            )
            st.plotly_chart(fig_cidades, use_container_width=True)

        # 3. Análise por tipo de serviço
        if 'SERVIÇO' in df.columns:
            st.subheader("🔧 Distribuição por Tipo de Serviço")
            fig_servico = px.pie(
                df['SERVIÇO'].value_counts().reset_index(),
                values='SERVIÇO',
                names='index',
                title='Distribuição de Tipos de Serviço'
            )
            st.plotly_chart(fig_servico, use_container_width=True)

        # 4. Análise de Status
        if 'STATUS ATIVIDADE' in df.columns:
            st.subheader("📊 Status das Atividades")
            fig_status = px.bar(
                df['STATUS ATIVIDADE'].value_counts().reset_index(),
                x='index',
                y='STATUS ATIVIDADE',
                title='Distribuição de Status das Atividades'
            )
            st.plotly_chart(fig_status, use_container_width=True)

        # 5. Análise de Valores
        if all(col in df.columns for col in ['VALOR TÉCNICO', 'VALOR EMPRESA']):
            st.subheader("💰 Análise de Valores")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Valor Total Técnico", f"R$ {df['VALOR TÉCNICO'].sum():,.2f}")
                st.metric("Média por Atividade", f"R$ {df['VALOR TÉCNICO'].mean():,.2f}")
            
            with col2:
                st.metric("Valor Total Empresa", f"R$ {df['VALOR EMPRESA'].sum():,.2f}")
                st.metric("Média por Atividade", f"R$ {df['VALOR EMPRESA'].mean():,.2f}")

        # 6. Análise Temporal
        if 'DATA' in df.columns:
            st.subheader("📈 Evolução Temporal")
            try:
                # Agrupa por data e conta atividades
                daily_activities = df.groupby('DATA').size().reset_index(name='Quantidade')
                fig_temporal = px.line(
                    daily_activities,
                    x='DATA',
                    y='Quantidade',
                    title='Quantidade de Atividades por Dia'
                )
                st.plotly_chart(fig_temporal, use_container_width=True)
            except Exception as e:
                st.warning(f"Não foi possível gerar a análise temporal: {e}")

        # 7. Análise de Eficiência
        if all(col in df.columns for col in ['INÍCIO', 'FIM']):
            st.subheader("⏱️ Análise de Tempo de Execução")
            try:
                # Converte para datetime se necessário
                if not pd.api.types.is_datetime64_any_dtype(df['INÍCIO']):
                    df['INÍCIO'] = pd.to_datetime(df['INÍCIO'], errors='coerce')
                if not pd.api.types.is_datetime64_any_dtype(df['FIM']):
                    df['FIM'] = pd.to_datetime(df['FIM'], errors='coerce')
                
                # Calcula duração em horas
                df['Duração'] = (df['FIM'] - df['INÍCIO']).dt.total_seconds() / 3600
                
                fig_duracao = px.histogram(
                    df[df['Duração'] > 0],  # Remove durações negativas ou zero
                    x='Duração',
                    title='Distribuição do Tempo de Execução (horas)',
                    nbins=30
                )
                st.plotly_chart(fig_duracao, use_container_width=True)
                
                # Estatísticas de duração
                st.metric("Tempo Médio de Execução", f"{df['Duração'].mean():,.2f} horas")
                
            except Exception as e:
                st.warning(f"Não foi possível gerar a análise de tempo de execução: {e}")

    with tab4:
        st.header("📋 Dicionário de Dados")
        
        dict_data = {
            'DATA_TOA': 'Data e hora de abertura da atividade',
            'DATA': 'Data da atividade',
            'BASE': 'Base operacional',
            'SERVIÇO': 'Tipo de serviço prestado',
            'COP REVERTEU': 'Indicador de reversão pelo COP',
            'HABILIDADE DE TRABALHO': 'Especialidade técnica necessária',
            'STATUS ATIVIDADE': 'Status atual da atividade',
            'PACOTE': 'Pacote de serviços',
            'CLIENTE': 'Nome do cliente',
            'CIDADES': 'Cidade onde o serviço foi prestado',
            'LATIDUDE': 'Latitude da localização',
            'LONGITUDE': 'Longitude da localização',
            'NODE': 'Identificador do nó de rede',
            'TECNICO': 'Nome do técnico',
            'LOGIN': 'Login do técnico',
            'SUPERVISOR': 'Nome do supervisor',
            'INÍCIO': 'Hora de início da atividade',
            'FIM': 'Hora de fim da atividade',
            'DESLOCAMENTO': 'Tempo de deslocamento',
            'COD': 'Código da atividade',
            'COD STATUS': 'Código do status',
            'TIPO OS': 'Tipo de ordem de serviço',
            'VALOR TÉCNICO': 'Valor pago ao técnico',
            'VALOR EMPRESA': 'Valor pago à empresa',
            'PONTO': 'Pontuação da atividade'
        }
        
        dict_df = pd.DataFrame([
            {
                'Coluna': col,
                'Descrição': desc,
                'Tipo Sugerido': 'Data' if col in ['DATA_TOA', 'DATA', 'INÍCIO', 'FIM', 'DESLOCAMENTO'] else 
                                'Número' if col in ['COP REVERTEU', 'LATIDUDE', 'LONGITUDE', 'COD', 'TIPO OS', 'VALOR TÉCNICO', 'VALOR EMPRESA', 'PONTO'] else 'Texto'
            }
            for col, desc in dict_data.items()
        ])
        
        st.dataframe(dict_df, use_container_width=True)

else:
    st.info("👈 Selecione um arquivo na barra lateral para começar a análise.")
