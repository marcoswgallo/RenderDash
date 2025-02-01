import pandas as pd
import os
import json
import numpy as np
import gzip

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def convert_excel_to_json(excel_path):
    """Converte arquivo Excel para JSON otimizado e comprimido"""
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
        
        print(f"Lendo arquivo Excel: {excel_path}")
        df = pd.read_excel(excel_path, dtype=dtype_dict)
        
        # Converte datas
        date_columns = ['DATA_TOA', 'DATA', 'INÍCIO', 'FIM', 'DESLOCAMENTO']
        for col in date_columns:
            if col in df.columns:
                print(f"Convertendo coluna {col}")
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Formato mais compacto para datas
                df[col] = df[col].dt.strftime('%Y%m%d%H%M%S')
                df[col] = df[col].replace('NaT', None)
        
        # Converte tipos numéricos para mais eficientes
        numeric_columns = {
            'COP REVERTEU': 'float32',
            'LATIDUDE': 'float32',
            'LONGITUDE': 'float32',
            'COD': 'float32',  # Mudado para float32 para lidar com NaN
            'TIPO OS': 'float32',  # Mudado para float32 para lidar com NaN
            'VALOR TÉCNICO': 'float32',
            'VALOR EMPRESA': 'float32',
            'PONTO': 'float32'
        }
        
        for col, dtype in numeric_columns.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
        
        # Cria o caminho para o JSON
        json_path = excel_path.replace('.xlsx', '.json.gz')
        
        print(f"Salvando JSON comprimido: {json_path}")
        # Converte para dicionário e salva como JSON comprimido
        data_dict = {
            'columns': list(df.columns),
            'data': df.values.tolist(),
            'dtypes': {col: str(df[col].dtype) for col in df.columns}
        }
        
        json_str = json.dumps(data_dict, cls=NumpyEncoder, separators=(',', ':'))
        with gzip.open(json_path, 'wt') as f:
            f.write(json_str)
        
        print(f"Conversão concluída!")
        
        # Mostra tamanho dos arquivos
        excel_size = os.path.getsize(excel_path) / (1024 * 1024)  # MB
        json_size = os.path.getsize(json_path) / (1024 * 1024)  # MB
        print(f"\nTamanho do Excel: {excel_size:.2f} MB")
        print(f"Tamanho do JSON comprimido: {json_size:.2f} MB")
        
        if json_size < excel_size:
            print(f"Redução: {((excel_size - json_size) / excel_size * 100):.1f}%")
        else:
            print(f"Aumento: {((json_size - excel_size) / excel_size * 100):.1f}%")
        
        return True
    except Exception as e:
        print(f"Erro ao converter Excel para JSON: {e}")
        return False

if __name__ == "__main__":
    # Converte o arquivo de janeiro 2025
    excel_path = "data/2025/janeiro_2025.xlsx"
    convert_excel_to_json(excel_path)
