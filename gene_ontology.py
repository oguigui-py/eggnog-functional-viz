import matplotlib
matplotlib.use('Agg')  # Essencial para rodar em segundo plano com interface Tkinter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from goatools.obo_parser import GODag
from collections import Counter
import sys
import os

# ===================== CONFIG =====================
if len(sys.argv) > 1:
    ARQUIVO = sys.argv[1]
else:
    ARQUIVO = "P2240.emapper.annotations.xlsx"

coluna_go = "GOs"          
top_n = 6                 
# Garante que o script procure o .obo no diretório do script, não onde o XLSX está
script_dir = os.path.dirname(os.path.abspath(__file__))
obo_file = os.path.join(script_dir, "go.obo")

if len(sys.argv) > 4:
    cores_dominios = {
        "BP": sys.argv[2],
        "CC": sys.argv[3],
        "MF": sys.argv[4]
    }
else:
    cores_dominios = {"BP": "#0B7285", "CC": "#3BC9DB", "MF": "#20C997"}

# ===================== LOAD ======================
try:
    # O eggNOG costuma ter 4 ou 5 linhas de comentário. 
    # O engine openpyxl é o padrão para .xlsx
    df = pd.read_excel(ARQUIVO, comment='#') 
    
    if not os.path.exists(obo_file):
        print(f"ERRO: Arquivo {obo_file} não encontrado!")
        sys.exit(1)
        
    go_dag = GODag(obo_file)
except Exception as e:
    print(f"Erro ao carregar arquivos: {e}")
    sys.exit(1)

# ===================== PROCESS ===================
def top_terms_por_dominio(namespace):
    if coluna_go not in df.columns:
        print(f"Erro: Coluna {coluna_go} não encontrada no arquivo.")
        return []
        
    termos = (
        df[coluna_go]
        .dropna()
        .loc[df[coluna_go] != "-"]
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
    )
    filtrados = [
        go_dag[go].name
        for go in termos
        if go in go_dag and go_dag[go].namespace == namespace
    ]
    return Counter(filtrados).most_common(top_n)

bp = top_terms_por_dominio("biological_process")
cc = top_terms_por_dominio("cellular_component")
mf = top_terms_por_dominio("molecular_function")

# Prevenção caso um dos domínios esteja vazio
if not bp or not cc or not mf:
    print("Aviso: Um ou mais domínios GO não possuem dados suficientes.")

# ===================== PLOT ======================
gap = 1.5
bp_labels, bp_vals = zip(*bp) if bp else (["N/A"], [0])
cc_labels, cc_vals = zip(*cc) if cc else (["N/A"], [0])
mf_labels, mf_vals = zip(*mf) if mf else (["N/A"], [0])

total_geral = sum(bp_vals) + sum(cc_vals) + sum(mf_vals)

x_bp = np.arange(len(bp_labels))
x_cc = np.arange(len(cc_labels)) + x_bp[-1] + 1 + gap
x_mf = np.arange(len(mf_labels)) + x_cc[-1] + 1 + gap

fig, ax = plt.subplots(figsize=(12, 8))

bars_bp = ax.bar(x_bp, bp_vals, color=cores_dominios["BP"])
bars_cc = ax.bar(x_cc, cc_vals, color=cores_dominios["CC"])
bars_mf = ax.bar(x_mf, mf_vals, color=cores_dominios["MF"])

# Ticks e Labels do Eixo X (Alteração solicitada anteriormente)
xticks = np.concatenate([x_bp, x_cc, x_mf])
xlabels = list(bp_labels) + list(cc_labels) + list(mf_labels)
ax.set_xticks(xticks)
ax.set_xticklabels(xlabels, rotation=90, fontsize=10)
ax.set_ylabel("Count", fontsize=12)

# --- PORCENTAGEM MAIOR (Alteração solicitada) ---
def add_percentage(bars):
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            percentage = (height / total_geral) * 100
            ax.text(
                bar.get_x() + bar.get_width()/2., 
                height + (max(bp_vals+cc_vals+mf_vals)*0.01),                     
                f'{percentage:.1f}%',             
                ha='center', va='bottom', 
                fontsize=11, fontweight='bold', # Tamanho aumentado
                color="#333333"
            )

add_percentage(bars_bp)
add_percentage(bars_cc)
add_percentage(bars_mf)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(0, max(bp_vals + cc_vals + mf_vals) * 1.3) 

# ===================== DOMÍNIOS =====================
y_top = max(bp_vals + cc_vals + mf_vals) * 1.15

def dominio_box(x_start, x_end, texto):
    ax.annotate(
        texto,
        xy=((x_start + x_end) / 2, y_top),
        ha="center", va="bottom",
        fontsize=11, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black")
    )

dominio_box(x_bp[0], x_bp[-1], "Biological Process")
dominio_box(x_cc[0], x_cc[-1], "Cellular Component")
dominio_box(x_mf[0], x_mf[-1], "Molecular Function")

plt.tight_layout()
# Caminho de saída (Pode ser adaptado para o interface.py enviar um destino)
output_path = "GO_domains_vertical.svg"
plt.savefig(output_path, format="svg")
plt.close()

print(f"✅ Figura gerada com sucesso: {output_path}")