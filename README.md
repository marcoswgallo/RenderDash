# Dashboard de Análise de Dados Excel

Dashboard interativo para análise de dados em Excel usando Python e Streamlit, otimizado para grandes volumes de dados.

## Funcionalidades

- Upload de arquivos Excel
- Visualização interativa dos dados
- Análises estatísticas automáticas
- Gráficos de distribuição
- Filtros dinâmicos

## Configuração

1. Criar ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

2. Instalar dependências:
```bash
pip install -r requirements.txt
```

3. Executar:
```bash
streamlit run src/app.py
```

## Estrutura do Projeto

```
excel_analytics/
├── data/           # Pasta para arquivos de dados
├── src/            # Código fonte
│   └── app.py      # Aplicação principal
├── requirements.txt # Dependências
├── .gitignore      # Arquivos ignorados pelo git
└── README.md       # Documentação
```

## Deploy no Render

1. Conecte seu repositório ao Render
2. Crie um novo Web Service
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run src/app.py`
