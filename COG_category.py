import os
import re
from collections import Counter
import sys
import pandas as pd
import plotly.express as px

# ===================== CONFIG =====================
if len(sys.argv) > 1:
    ARQUIVO = sys.argv[1]
else:
    ARQUIVO = "P2240.emapper.annotations.xlsx"

# ----------------------------
# 1) Ler planilha e achar coluna COG_category
# ----------------------------
try:
    # ADICIONADO: comment='#' para ignorar o cabeçalho do eggNOG
    df = pd.read_excel(ARQUIVO, engine="openpyxl", comment='#')
except Exception as e:
    print(f"Erro ao abrir o arquivo: {e}")
    sys.exit(1)

col_cog = None
for c in df.columns:
    if isinstance(c, str) and "COG_category" in c:
        col_cog = c
        break

if col_cog is None:
    print("Erro: Não encontrei a coluna 'COG_category'. Verifique se o arquivo está correto.")
    sys.exit(1)

# ----------------------------
# 2) Contagem e Processamento
# ----------------------------
contagem = Counter()
serie = df[col_cog].dropna()

for val in serie:
    s = str(val).strip()
    if s == "-" or s == "":
        continue
    # Extrai letras A-Z (categorias COG)
    letras = re.findall(r"[A-Z]", s.upper())
    for letra in letras:
        contagem[letra] += 1

# ----------------------------
# 3) Montar Hierarquia
# ----------------------------
macro_map = {
    "POORLY CHARACTERIZED": list("S"),
    "METABOLISM": ["F", "I", "Q", "H", "C", "P", "E", "G"],
    "INFORMATION STORAGE AND PROCESSING": ["J", "L", "K", "A"],
    "CELLULAR PROCESSES AND SIGNALING": ["D", "U", "N", "V", "O", "M", "T"],
}

rows = []
for macro, letras in macro_map.items():
    for letra in letras:
        qtd = contagem.get(letra, 0)
        if qtd > 0:
            rows.append({"Macro": macro, "COG": letra, "Count": qtd})

df_plot = pd.DataFrame(rows)

# ----------------------------
# 4) Cores e Plotagem
# ----------------------------
if len(sys.argv) > 2:
    paleta_usuario = sys.argv[2:13] 
else:
    paleta_usuario = px.colors.qualitative.Pastel

fig = px.sunburst(
    df_plot,
    path=["Macro", "COG"],
    values="Count",
    color="Macro",
    color_discrete_sequence=paleta_usuario,
)

# AJUSTE: textinfo para mostrar labels e porcentagens
fig.update_traces(
    textinfo="label+percent entry",
    insidetextorientation="radial"
)

# AJUSTE: Tamanho da fonte aumentado para 16 (conforme solicitado)
fig.update_layout(
    margin=dict(t=20, l=20, r=20, b=20),
    font=dict(family="Arial", size=16, color="black"), 
    paper_bgcolor='white'
)

# ----------------------------
# 5) Exportação
# ----------------------------
# O Plotly precisa do pacote 'kaleido' instalado para salvar em SVG/PNG
try:
    fig.write_image("COG_sunburst.svg", width=1000, height=1000, engine="kaleido")
    print("✅ Gráfico COG finalizado: COG_sunburst.svg")
except Exception as e:
    print(f"Erro ao salvar imagem (verifique se o pacote 'kaleido' está instalado): {e}")