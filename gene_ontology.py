import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from goatools.obo_parser import GODag
from collections import Counter
import sys

# ===================== CONFIG =====================
# Verifica se um caminho foi passado como argumento
if len(sys.argv) > 1:
    ARQUIVO = sys.argv[1]
else:
    print("Nenhum arquivo .xlsx especificado como argumento. Usando valor padrão.")
    ARQUIVO = "P2240.emapper.annotations.xlsx" # Valor padrão caso não passe argumento

coluna_go = "GOs"          # coluna J
top_n = 6                 # microdomínios por domínio
obo_file = "go.obo"
# ================================================

if len(sys.argv) > 2:
    # Usa a cor 1, 2 e 3 da interface
    cores_dominios = {
        "BP": sys.argv[2],  # Cor 1
        "CC": sys.argv[3],  # Cor 2
        "MF": sys.argv[4]   # Cor 3
    }
else:
    # Cores padrão
    cores_dominios = {
        "BP": "#0B7285",
        "CC": "#3BC9DB",
        "MF": "#20C997"
    }
# ===================== LOAD ======================
df = pd.read_excel(ARQUIVO)
go_dag = GODag(obo_file)

# ===================== PROCESS ===================
def top_terms_por_dominio(namespace):
    termos = (
        df[coluna_go]
        .dropna()
        .loc[df[coluna_go] != "-"]
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

# ===================== PLOT ======================
gap = 1.5

bp_labels, bp_vals = zip(*bp)
cc_labels, cc_vals = zip(*cc)
mf_labels, mf_vals = zip(*mf)

# Cálculo do total para as porcentagens
total_geral = sum(bp_vals) + sum(cc_vals) + sum(mf_vals)

x_bp = np.arange(len(bp_labels))
x_cc = np.arange(len(cc_labels)) + x_bp[-1] + 1 + gap
x_mf = np.arange(len(mf_labels)) + x_cc[-1] + 1 + gap

fig, ax = plt.subplots(figsize=(12, 7)) # Aumentado levemente para acomodar labels rotacionados

# Desenha as barras
bars_bp = ax.bar(x_bp, bp_vals, color=cores_dominios["BP"])
bars_cc = ax.bar(x_cc, cc_vals, color=cores_dominios["CC"])
bars_mf = ax.bar(x_mf, mf_vals, color=cores_dominios["MF"])

# --- ADICIONAR OS NOMES DOS TERMOS NO EIXO X (ALTERAÇÃO SOLICITADA) ---
xticks = np.concatenate([x_bp, x_cc, x_mf])
xlabels = list(bp_labels) + list(cc_labels) + list(mf_labels)

ax.set_xticks(xticks)
ax.set_xticklabels(xlabels, rotation=90, fontsize=9)
ax.set_ylabel("Count")

# --- FUNÇÃO PARA ADICIONAR AS PORCENTAGENS ---
def add_percentage(bars):
    for bar in bars:
        height = bar.get_height()
        percentage = (height / total_geral) * 100
        ax.text(
            bar.get_x() + bar.get_width()/2., 
            height + 0.5,                     
            f'{percentage:.1f}%',             
            ha='center', va='bottom', 
            fontsize=8, fontweight='bold',
            rotation=0 
        )

add_percentage(bars_bp)
add_percentage(bars_cc)
add_percentage(bars_mf)

# Limpeza estética
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Aumentar o limite do eixo Y para o texto não cortar
ax.set_ylim(0, max(bp_vals + cc_vals + mf_vals) * 1.2)

# ===================== DOMÍNIOS EM CIMA =====================
y_top = max(bp_vals + cc_vals + mf_vals) * 1.05

def dominio_box(x_start, x_end, texto):
    ax.annotate(
        texto,
        xy=((x_start + x_end) / 2, y_top),
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black")
    )

dominio_box(x_bp[0], x_bp[-1], "Biological Process")
dominio_box(x_cc[0], x_cc[-1], "Cellular Component")
dominio_box(x_mf[0], x_mf[-1], "Molecular Function")

# ===================== EXPORT =====================
plt.tight_layout()
plt.savefig("GO_domains_vertical.svg", format="svg")
plt.close()

print("Figura final gerada: GO_domains_vertical.svg")