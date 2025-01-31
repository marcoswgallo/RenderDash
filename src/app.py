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
        # Especifica os tipos de dados na leitura
        dtype_dict = {
            'BASE': 'str',
            'SERVIÇO': 'str',
            'HABILIDADE DE TRABALHO': 'str',
            'STATUS ATIVIDADE': 'str',
            'PACOTE': 'str',
            'CLIENTE': 'str',
            'CIDADES': 'str',
            'NODE': 'str',
            'TECNICO': 'str',
            'LOGIN': 'str',
            'SUPERVISOR': 'str',
            'COD STATUS': 'str'
        }
        
        # Parse dates na leitura
        date_columns = ['DATA_TOA', 'DATA', 'INÍCIO', 'FIM', 'DESLOCAMENTO']
        
        df = pd.read_excel(
            file_path,
            dtype=dtype_dict,
            parse_dates=date_columns
        )
        
        # Converte colunas numéricas explicitamente
        numeric_columns = {
            'COP REVERTEU': 'float64',
            'LATIDUDE': 'float64',
            'LONGITUDE': 'float64',
            'COD': 'float64',
            'TIPO OS': 'float64',
            'VALOR TÉCNICO': 'float64',
            'VALOR EMPRESA': 'float64',
            'PONTO': 'float64'
        }
        
        for col, dtype in numeric_columns.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

# Título principal
st.title("📊 Dashboard de Análise de Dados")

# Sidebar para filtros
with st.sidebar:
    st.header("📁 Seleção de Arquivo")
    
    # Lista todos os arquivos Excel no diretório data
    project_root = get_project_root()
    data_dir = project_root / "data"
    excel_files = []
    for year in os.listdir(data_dir):
        year_dir = os.path.join(data_dir, year)
        if os.path.isdir(year_dir):
            for file in os.listdir(year_dir):
                if file.endswith('.xlsx'):
                    excel_files.append(os.path.join(year_dir, file))
    
    if excel_files:
        # Ordena os arquivos por data de modificação (mais recente primeiro)
        excel_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Extrai apenas o nome do arquivo para exibição
        file_names = [os.path.basename(f) for f in excel_files]
        
        selected_file = st.selectbox(
            "Selecione o arquivo Excel:",
            range(len(excel_files)),
            format_func=lambda x: file_names[x]
        )
        
        # Carrega o arquivo selecionado
        df = load_data(excel_files[selected_file])
        
        if df is not None:
            st.success(f"✅ Arquivo carregado com sucesso!")
            
            # Filtros por tipo de base
            st.header("🏢 Filtros por Base")
            
            # Dicionário com as bases por tipo
            bases = {
                'Instalação': [
                    'BASE BAURURIBEIRAOOTUCATU',
                    'BASE CAMPINAS',
                    'BASE LIMEIRA',
                    'BASE PAULINIA',
                    'BASE PIRACICABA',
                    'BASE RIBEIRAO PRETO',
                    'BASE SAO JOSE DO RIO PRETO',
                    'BASE SOROCABA',
                    'BASE SUMARE',
                    'GPON BAURU',
                    'GPON RIBEIRAO PRETO'
                ],
                'Manutenção': [
                    'BASE ARARAS VT',
                    'BASE BOTUCATU VT',
                    'BASE MDU ARARAS',
                    'BASE MDU BAURU',
                    'BASE MDU MOGI',
                    'BASE MDU PIRACICABA',
                    'BASE MDU SJRP',
                    'BASE PIRACICABA VT',
                    'BASE RIBEIRÃO VT',
                    'BASE SERTAOZINHO VT',
                    'BASE SUMARE VT',
                    'BASE VAR BAURU',
                    'BASE VAR PIRACICABA',
                    'BASE VAR SUMARE'
                ],
                'Desconexão': [
                    'DESCONEXAO',
                    'DESCONEXÃO BOTUCATU',
                    'DESCONEXÃO CAMPINAS',
                    'DESCONEXAO RIBEIRAO PRETO'
                ]
            }
            
            # Filtro por tipo de base
            tipo_base = st.multiselect(
                "Tipo de Base:",
                options=list(bases.keys()),
                default=list(bases.keys())
            )
            
            # Filtro por bases específicas
            bases_selecionadas = []
            for tipo in tipo_base:
                bases_selecionadas.extend(bases[tipo])
            
            bases_filtro = st.multiselect(
                "Bases Específicas:",
                options=bases_selecionadas,
                default=bases_selecionadas
            )
            
            # Aplica os filtros
            if bases_filtro:
                df = df[df['BASE'].isin(bases_filtro)]
            
            st.metric("Registros Filtrados", len(df))
    else:
        st.warning("Nenhum arquivo Excel encontrado no diretório data.")

# Layout principal
if 'df' in locals() and df is not None:
    # Métricas principais em uma linha
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

    # Análises e Visualizações
    st.header("📈 Análises e Visualizações")

    # 1. Análise por dia da semana
    if 'DATA' in df.columns:
        try:
            st.subheader("📅 Distribuição por Dia da Semana")
            dias_semana = {
                0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta',
                4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
            }
            
            # Garante que a coluna é datetime
            if not pd.api.types.is_datetime64_any_dtype(df['DATA']):
                df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            
            df_dias = df.copy()
            df_dias['Dia_Semana'] = df_dias['DATA'].dt.dayofweek.map(dias_semana)
            dias_contagem = df_dias['Dia_Semana'].value_counts().reset_index()
            dias_contagem.columns = ['Dia', 'Quantidade']
            
            fig_dias = px.bar(
                dias_contagem,
                x='Dia',
                y='Quantidade',
                title='Quantidade de Atividades por Dia da Semana'
            )
            st.plotly_chart(fig_dias, use_container_width=True)
        except Exception as e:
            st.warning(f"Não foi possível gerar a análise por dia da semana: {e}")

    # 2. Análise por cidade
    if 'CIDADES' in df.columns:
        st.subheader("🌆 Top 10 Cidades")
        cidades_contagem = df['CIDADES'].value_counts().head(10).reset_index()
        cidades_contagem.columns = ['Cidade', 'Quantidade']
        
        fig_cidades = px.bar(
            cidades_contagem,
            x='Cidade',
            y='Quantidade',
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

else:
    st.info("👈 Selecione um arquivo na barra lateral para começar a análise.")
