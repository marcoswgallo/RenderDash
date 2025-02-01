import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
from datetime import datetime
import numpy as np
import gzip
import json

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

# Função para converter Excel para JSON
def convert_excel_to_json(excel_path, json_path):
    """Converte arquivo Excel para JSON otimizado"""
    try:
        # Lê o Excel com tipos otimizados
        dtype_dict = {
            'BASE': 'category',
            'SERVIÇO': 'category',
            'HABILIDADE DE TRABALHO': 'category',
            'STATUS ATIVIDADE': 'category',
            'PACOTE': 'category',
            'CLIENTE': 'category',
            'CIDADES': 'category',
            'NODE': 'category',
            'TECNICO': 'category',
            'LOGIN': 'category',
            'SUPERVISOR': 'category',
            'COD STATUS': 'category'
        }
        
        date_columns = ['DATA_TOA', 'DATA', 'INÍCIO', 'FIM', 'DESLOCAMENTO']
        
        df = pd.read_excel(
            excel_path,
            dtype=dtype_dict,
            parse_dates=date_columns
        )
        
        # Converte datas para string ISO format para JSON
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Salva como JSON de forma otimizada
        df.to_json(json_path, orient='records', date_format='iso')
        return True
    except Exception as e:
        st.error(f"Erro ao converter Excel para JSON: {e}")
        return False

# Função para carregar dados
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data(file_path):
    try:
        # Se é Excel, procura por um JSON comprimido correspondente
        if file_path.endswith('.xlsx'):
            json_path = file_path.replace('.xlsx', '.json.gz')
            if os.path.exists(json_path):
                file_path = json_path
        
        # Carrega do JSON comprimido
        if file_path.endswith('.json.gz'):
            with st.spinner('Carregando dados...'):
                with gzip.open(file_path, 'rt') as f:
                    data = json.load(f)
                
                # Recria o DataFrame
                df = pd.DataFrame(data['data'], columns=data['columns'])
                
                # Converte tipos de volta
                for col, dtype in data['dtypes'].items():
                    if 'datetime' in dtype:
                        df[col] = pd.to_datetime(df[col], format='%Y%m%d%H%M%S', errors='coerce')
                    elif 'category' in dtype:
                        df[col] = df[col].astype('category')
                    elif 'float32' in dtype:
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')
                    elif 'int32' in dtype:
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('int32')
                
                return df
        
        # Se não encontrou JSON, carrega do Excel
        else:
            with st.spinner('Carregando dados do Excel...'):
                dtype_dict = {
                    'BASE': 'category',
                    'SERVIÇO': 'category',
                    'HABILIDADE DE TRABALHO': 'category',
                    'STATUS ATIVIDADE': 'category',
                    'PACOTE': 'category',
                    'CLIENTE': 'category',
                    'CIDADES': 'category',
                    'NODE': 'category',
                    'TECNICO': 'category',
                    'LOGIN': 'category',
                    'SUPERVISOR': 'category',
                    'COD STATUS': 'category'
                }
                
                df = pd.read_excel(file_path, dtype=dtype_dict)
                
                numeric_columns = {
                    'COP REVERTEU': 'float32',
                    'LATIDUDE': 'float32',
                    'LONGITUDE': 'float32',
                    'COD': 'float32',
                    'TIPO OS': 'float32',
                    'VALOR TÉCNICO': 'float32',
                    'VALOR EMPRESA': 'float32',
                    'PONTO': 'float32'
                }
                
                for col, dtype in numeric_columns.items():
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
                
                return df
            
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

# Função para processar DataFrame
@st.cache_data(ttl=3600)
def process_dataframe(df, bases_filtro=None):
    """Processa o DataFrame aplicando filtros e agregações"""
    try:
        if bases_filtro:
            df = df[df['BASE'].isin(bases_filtro)].copy()  # Usa copy para otimizar memória
        
        # Pré-calcula algumas agregações comuns
        stats = {
            'total_registros': len(df),
            'cidades_unicas': df['CIDADES'].nunique() if 'CIDADES' in df.columns else 0,
            'periodo': {
                'inicio': df['DATA'].min(),
                'fim': df['DATA'].max()
            } if 'DATA' in df.columns else None,
            'valor_total_tecnico': df['VALOR TÉCNICO'].sum() if 'VALOR TÉCNICO' in df.columns else 0,
            'valor_total_empresa': df['VALOR EMPRESA'].sum() if 'VALOR EMPRESA' in df.columns else 0
        }
        
        return df, stats
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return None, None

# Título principal
st.title("📊 Dashboard de Análise de Dados")

# Inicialização do estado da sessão
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'tipo_base' not in st.session_state:
    st.session_state.tipo_base = None
if 'bases_filtro' not in st.session_state:
    st.session_state.bases_filtro = None
if 'df_filtered' not in st.session_state:
    st.session_state.df_filtered = None

# Sidebar para filtros
with st.sidebar:
    st.header("📁 Seleção de Arquivo")
    
    # Lista todos os arquivos Excel e JSON.gz no diretório data
    project_root = get_project_root()
    data_dir = project_root / "data"
    excel_files = []
    for year in os.listdir(data_dir):
        year_dir = os.path.join(data_dir, year)
        if os.path.isdir(year_dir):
            for file in os.listdir(year_dir):
                if file.endswith('.xlsx') or file.endswith('.json.gz'):
                    excel_files.append(os.path.join(year_dir, file))
    
    if excel_files:
        # Ordena os arquivos por data de modificação (mais recente primeiro)
        excel_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Extrai apenas o nome do arquivo para exibição
        file_names = [os.path.basename(f) for f in excel_files]
        
        selected_file_index = st.selectbox(
            "Selecione o arquivo:",
            range(len(excel_files)),
            format_func=lambda x: file_names[x],
            key='selected_file_index'
        )
        
        # Carrega o arquivo selecionado
        if st.session_state.selected_file != excel_files[selected_file_index]:
            st.session_state.selected_file = excel_files[selected_file_index]
            st.session_state.df = load_data(excel_files[selected_file_index])
        
        if st.session_state.df is not None:
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
            tipos_base = list(bases.keys())
            if 'tipo_base' not in st.session_state:
                st.session_state.tipo_base = tipos_base
            
            tipo_base = st.multiselect(
                "Tipo de Base:",
                options=tipos_base,
                default=st.session_state.tipo_base,
                key='tipo_base_select'
            )
            st.session_state.tipo_base = tipo_base
            
            # Filtro por bases específicas
            bases_selecionadas = []
            for tipo in tipo_base:
                bases_selecionadas.extend(bases[tipo])
            
            if 'bases_filtro' not in st.session_state:
                st.session_state.bases_filtro = bases_selecionadas
            
            bases_filtro = st.multiselect(
                "Bases Específicas:",
                options=bases_selecionadas,
                default=st.session_state.bases_filtro,
                key='bases_filtro_select'
            )
            st.session_state.bases_filtro = bases_filtro
            
            # Aplica os filtros
            df_filtered = st.session_state.df.copy()
            if bases_filtro:
                df_filtered = df_filtered[df_filtered['BASE'].isin(bases_filtro)]
            
            st.metric("Registros Filtrados", len(df_filtered))
            
            # Atualiza o DataFrame filtrado na sessão
            st.session_state.df_filtered = df_filtered

    else:
        st.warning("Nenhum arquivo Excel encontrado no diretório data.")

# Layout principal
if 'df_filtered' in st.session_state and st.session_state.df_filtered is not None:
    df = st.session_state.df_filtered
    
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
