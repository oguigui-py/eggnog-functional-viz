import os
import re
from collections import Counter
import sys
import pandas as pd
import plotly.express as px

# Verifica se um caminho foi passado como argumento
if len(sys.argv) > 1:
    ARQUIVO = sys.argv[1]
else:
    print("Nenhum arquivo .xlsx especificado como argumento. Usando valor padrão.")

# ----------------------------
# 1) Ler planilha e achar coluna COG_category
# ----------------------------
caminho = os.path.join(os.getcwd(), ARQUIVO)
if not os.path.exists(caminho):
    raise FileNotFoundError(f"Não achei '{ARQUIVO}' no diretório atual: {os.getcwd()}")

# Tenta ler com header normal
df = pd.read_excel(caminho, engine="openpyxl")

col_cog = None
for c in df.columns:
    if isinstance(c, str) and "COG_category" in c:
        col_cog = c
        break

# Se não achou como nome de coluna, procura na primeira linha (linha 1 do Excel)
if col_cog is None:
    df0 = pd.read_excel(caminho, engine="openpyxl", header=None)
    header_row = df0.iloc[0].astype(str)
    matches = [i for i, v in enumerate(header_row) if "COG_category" in v]
    if not matches:
        raise KeyError("Não encontrei nenhuma célula na linha 1 contendo 'COG_category'.")
    col_idx = matches[0]
    # Constrói df com header na linha 1
    df = df0.copy()
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    col_cog = df.columns[col_idx]

# ----------------------------
# 2) Contar letras até a primeira célula vazia
# ----------------------------
contagem = Counter()

serie = df[col_cog]

for val in serie:
    # Para no primeiro vazio
    if pd.isna(val) or str(val).strip() == "":
        break

    s = str(val).strip()

    # ignora "-"
    if s == "-":
        continue

    # Extrai letras A-Z independentemente do separador (vírgula, espaço, etc.)
    letras = re.findall(r"[A-Z]", s.upper())
    for letra in letras:
        contagem[letra] += 1

# ----------------------------
# 3) Montar hierarquia macro -> letra
# ----------------------------
macro_map = {
    "POORLY CHARACTERIZED": list("S"),
    "METABOLYSM": ["F", "I", "Q", "H", "C", "P", "E", "G"],
    "INFORMATION STORAGE AND PROCESSING": ["J", "L", "K", "A"],
    "CELLULAR PROCESSES AND SIGNALING": ["D", "U", "N", "V", "O", "M", "T"],
}

rows = []
for macro, letras in macro_map.items():
    for letra in letras:
        qtd = contagem.get(letra, 0)
        # Se quiser esconder categorias zeradas, troque para: if qtd > 0:
        rows.append({"Macro": macro, "COG": letra, "Count": qtd})

df_plot = pd.DataFrame(rows)

# (opcional) remover letras com 0 para o sunburst ficar mais limpo
df_plot = df_plot[df_plot["Count"] > 0].copy()

# ----------------------------
# ----------------------------
# 4) Captura de Cores da Interface
# ----------------------------
if len(sys.argv) > 2:
    # Captura os 11 hexadecimais enviados pela interface
    paleta_usuario = sys.argv[2:13] 
else:
    # Paleta padrão caso o script seja rodado sozinho
    paleta_usuario = [
        "#0B7285", "#1098AD", "#15AABF", "#22B8CF", "#3BC9DB", 
        "#66D9E8", "#96F2D7", "#63E6BE", "#20C997", "#12B886", "#2F9E44"
    ]

# ----------------------------
# 5) Sunburst com Percentagens
# ----------------------------
# No Plotly, usamos 'hover_data' ou 'textinfo' para exibir as porcentagens
fig = px.sunburst(
    df_plot,
    path=["Macro", "COG"],
    values="Count",
    color="Macro",
    color_discrete_sequence=paleta_usuario, # Usa a sua paleta da interface
)

# Configura para mostrar: Nome da Categoria + Porcentagem em relação ao total
fig.update_traces(
    textinfo="label+percent entry", # Exibe o nome e a % relativa ao centro
    insidetextorientation="radial"  # Melhora a leitura do texto dentro das fatias
)

fig.update_layout(
    margin=dict(t=10, l=10, r=10, b=10),
    font=dict(family="Serif", size=12) # Estética de jornal
)

# Salvar em SVG (para manter a qualidade infinita que você queria)
fig.write_image(
    "COG_sunburst.svg",
    width=1200,
    height=1200,
    scale=2
)

print("✅ Gráfico COG finalizado: COG_sunburst.svg")