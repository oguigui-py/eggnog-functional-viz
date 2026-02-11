import os
import subprocess
import sys
import pandas as pd
import requests
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# ===================== CONFIG =====================
# Planilha do eggNOG-mapper (a mesma que você já usa)
# Verifica se um caminho foi passado como argumento
if len(sys.argv) > 1:
    ARQUIVO = sys.argv[1]
else:
    print("Nenhum arquivo .xlsx especificado como argumento. Usando valor padrão.")

# Passo 1: usar a coluna KEGG_ko como base
COL_KEGG_KO = "KEGG_ko"      # coluna do eggNOG com Kxxxxx (ex: K00001,K01803)

# Coluna do identificador do gene (o script tenta achar se não existir)
COL_GENE = "query"          # geralmente é "query" no eggNOG

# Passo 7: top 10–20 mais abundantes
TOP_N = 15

# Passo 8: saída do gráfico
OUT_SVG = "KEGG_Level2_barh.svg"
# ==================================================

# Paleta pastel (Level 1 -> cor)
# Captura as 11 cores da interface (do argumento 2 ao 12)
if len(sys.argv) > 2:
    # Captura os 11 hexadecimais enviados
    paleta_usuario = sys.argv[2:13] 
else:
    # Paleta padrão caso o script seja rodado sozinho
    paleta_usuario = [
        "#0B7285", "#1098AD", "#15AABF", "#22B8CF", "#3BC9DB", 
        "#66D9E8", "#96F2D7", "#63E6BE", "#20C997", "#12B886", "#2F9E44"
    ]

# ===================== HELPERS =====================
def escolher_excel_macos() -> str | None:
    """Se o arquivo configurado não existir, abre um seletor de arquivo no macOS (sem Tkinter)."""
    try:
        script = '''
        set f to choose file with prompt "Selecione a planilha do eggNOG-mapper (.xlsx)"
        POSIX path of f
        '''
        out = subprocess.check_output(["osascript", "-e", script], text=True).strip()
        return out if out else None
    except subprocess.CalledProcessError:
        return None

def get_text(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.text

def parse_brite_br08901() -> tuple[dict[str, str], dict[str, str]]:
    """
    Lê a hierarquia KEGG BRITE br08901 (Pathway hierarchy) e retorna:
    - map_id -> Level2
    - map_id -> Level1
    Onde map_id é tipo '00010', '02010', etc.
    """
    txt = get_text("https://rest.kegg.jp/get/br:br08901")
    level1 = None
    level2 = None
    map_to_l1 = {}
    map_to_l2 = {}

    for line in txt.splitlines():
        # Formato típico:
        # A <level1>
        # B  <level2>
        # C   00010 Glycolysis / Gluconeogenesis [PATH:ko00010]
        if not line:
            continue

        tag = line[0]
        if tag == "A":
            level1 = line[1:].strip()
        elif tag == "B":
            level2 = line[1:].strip()
        elif tag == "C":
            # tenta capturar o id numérico do mapa
            parts = line.split()
            # normalmente: ["C", "00010", "Glycolysis", ...]
            if len(parts) >= 2 and parts[1].isdigit():
                map_id = parts[1]
                if level1 and level2:
                    map_to_l1[map_id] = level1
                    map_to_l2[map_id] = level2

    return map_to_l2, map_to_l1

def build_ko_to_map() -> dict[str, set[str]]:
    """
    Usa KEGG REST 'link/pathway/ko' para mapear:
    KO (Kxxxxx) -> set(map_id)
    """
    txt = get_text("https://rest.kegg.jp/link/pathway/ko")
    ko_to_maps = defaultdict(set)

    for line in txt.splitlines():
        if not line.strip():
            continue
        left, right = line.split("\t")
        # left: ko:K00001
        # right: path:map00010  (ou path:ko00010 em alguns casos)
        ko = left.replace("ko:", "").strip()
        pw = right.replace("path:", "").strip()

        # Extrai o id do mapa:
        # map00010 -> 00010
        # ko00010  -> 00010
        map_id = None
        if pw.startswith("map") and len(pw) >= 8:
            map_id = pw[3:8]
        elif pw.startswith("ko") and len(pw) >= 7:
            map_id = pw[2:7]

        if map_id and map_id.isdigit():
            ko_to_maps[ko].add(map_id)

    return ko_to_maps

def pick_gene_column(df: pd.DataFrame) -> str:
    if COL_GENE in df.columns:
        return COL_GENE
    # fallback: primeira coluna (muito comum ser o identificador do gene)
    return df.columns[0]

def normalize_kegg_cell(x) -> str:
    """Normaliza a célula KEGG_ko (Passos 2 e 3):
    - Trata NaN/None
    - Remove espaços
    - Não muda a informação; só prepara para split/validação
    """
    if x is None:
        return ""
    s = str(x).strip()
    # eggNOG costuma usar '-' para ausente
    if s == "-":
        return ""
    return s

def split_kos(cell: str) -> list[str]:
    """Separa múltiplos KOs numa célula (Passo 3).
    Aceita separadores comuns: vírgula, ponto-e-vírgula, espaço.
    """
    if not cell:
        return []
    # troca separadores por vírgula e divide
    for sep in [";", " "]:
        cell = cell.replace(sep, ",")
    parts = [p.strip() for p in cell.split(",") if p.strip()]
    return parts

# ===================== LOAD =====================
arquivo = ARQUIVO
if not os.path.exists(arquivo):
    print(f"Arquivo '{arquivo}' não encontrado. Abrindo seletor...")
    escolhido = escolher_excel_macos()
    if not escolhido:
        raise FileNotFoundError("Nenhum arquivo selecionado.")
    arquivo = escolhido

df = pd.read_excel(arquivo)

if COL_KEGG_KO not in df.columns:
    raise KeyError(f"Coluna '{COL_KEGG_KO}' não encontrada. Colunas disponíveis: {df.columns.tolist()}")

gene_col = pick_gene_column(df)

# ===================== CLEAN + EXPLODE =====================
# Passo 2: remover vazios e '-'
# Passo 3: separar múltiplos KOs por célula
df_kegg = df[[gene_col, COL_KEGG_KO]].copy()
df_kegg[COL_KEGG_KO] = df_kegg[COL_KEGG_KO].apply(normalize_kegg_cell)
df_kegg = df_kegg[df_kegg[COL_KEGG_KO] != ""]

# explode robusto (suporta "K00001,K01803" e também ";" e espaços)
df_kegg[COL_KEGG_KO] = df_kegg[COL_KEGG_KO].apply(split_kos)
df_kegg = df_kegg.explode(COL_KEGG_KO)
df_kegg[COL_KEGG_KO] = df_kegg[COL_KEGG_KO].astype(str).str.strip()

# remove prefixo "ko:" se existir
df_kegg[COL_KEGG_KO] = df_kegg[COL_KEGG_KO].str.replace("ko:", "", regex=False)

# mantém só KOs válidos (Kxxxxx)
df_kegg = df_kegg[df_kegg[COL_KEGG_KO].str.match(r"^K\d{5}$", na=False)]

if df_kegg.empty:
    raise RuntimeError("Nenhum KO válido encontrado após limpeza. Verifique a coluna KEGG_ko.")

# ===================== DOWNLOAD MAPS =====================
print("Baixando hierarquia KEGG (br08901)...")
map_to_l2, map_to_l1 = parse_brite_br08901()

# índice direto Level2 -> Level1 (Passo 5)
level2_to_level1 = {}
for mid, l2 in map_to_l2.items():
    l1 = map_to_l1.get(mid)
    if l2 and l1 and l2 not in level2_to_level1:
        level2_to_level1[l2] = l1

print("Baixando mapeamento KO -> pathway maps...")
ko_to_maps = build_ko_to_map()

# ===================== GENE-LEVEL COUNT =====================
# Queremos: para cada gene, quais Level2 ele atinge (via qualquer KO), e contar genes por Level2 (sem duplicar)
gene_to_level2 = defaultdict(set)

for gene, ko in zip(df_kegg[gene_col], df_kegg[COL_KEGG_KO]):
    for map_id in ko_to_maps.get(ko, []):
        l2 = map_to_l2.get(map_id)
        l1 = map_to_l1.get(map_id)
        if l2 and l1:
            gene_to_level2[gene].add(l2)

# contagem por Level2 = quantos genes tiveram pelo menos um KO mapeando para aquele Level2
level2_counts = Counter()
for gene, l2_set in gene_to_level2.items():
    for l2 in l2_set:
        level2_counts[l2] += 1

if not level2_counts:
    raise RuntimeError(
        "Nenhuma categoria KEGG Level 2 foi mapeada. "
        "Possíveis causas: KOs raros/ausentes ou problemas de rede com KEGG."
    )

# total genes anotados com KEGG (após limpeza) = genes únicos com pelo menos 1 KO válido
genes_com_kegg = df_kegg[gene_col].nunique()

# ===================== BUILD PLOT DF =====================
plot_rows = []
for l2, cnt in level2_counts.items():
    # Passo 5: associar Level2 -> Level1
    l1 = level2_to_level1.get(l2, "Other")

    plot_rows.append((l1, l2, cnt, 100 * cnt / genes_com_kegg))

df_plot = pd.DataFrame(plot_rows, columns=["Level1", "Level2", "CountGenes", "PercentGenes"])
df_plot = df_plot.sort_values("PercentGenes", ascending=False).head(TOP_N)

# Para barh ficar visualmente melhor (topo em cima), inverte a ordem
df_plot = df_plot.sort_values("PercentGenes", ascending=True)

# ===================== PLOT (Passo 8: barras horizontais) =====================
bar_colors = [
    paleta_usuario[df_plot["Level1"].tolist().index(l1)] if l1 in df_plot["Level1"].tolist() else "#e2ece9"
    for l1 in df_plot["Level1"]
]

plt.figure(figsize=(12, 9)) # Aumentei um pouco a largura para caber o texto lateral

# Cria as barras
bars = plt.barh(
    df_plot["Level2"],
    df_plot["PercentGenes"],
    color=bar_colors
)

# --- ADICIONAR PERCENTAGENS À DIREITA DAS BARRAS ---
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + 0.2,                # Posição X: um pouco depois do fim da barra
        bar.get_y() + bar.get_height()/2, # Posição Y: centro vertical da barra
        f'{width:.1f}%',            # O valor da percentagem formatado
        va='center',                # Alinhamento vertical ao centro
        ha='left',                  # Alinhamento horizontal à esquerda do ponto X
        fontsize=9, 
        fontweight='bold',
        fontfamily='serif'          # Mantendo a estética de jornal
    )

plt.xlabel("Percentual de genes anotados com KEGG (%)")
plt.ylabel("KEGG Level 2")

# Ajuste do limite do eixo X para o texto não ser cortado
plt.xlim(0, df_plot["PercentGenes"].max() * 1.15)

# estilo clean
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)


# legenda KEGG Level 1
from matplotlib.lines import Line2D

unique_l1 = list(dict.fromkeys(df_plot["Level1"].tolist()))
handles = [
    Line2D([0], [0], color=paleta_usuario[df_plot["Level1"].tolist().index(l1)] if l1 in df_plot["Level1"].tolist() else "#e2ece9", lw=6)
    for l1 in unique_l1
]

plt.legend(
    handles,
    unique_l1,
    title="KEGG Level 1",
    frameon=False,
    loc="lower right"
)

plt.tight_layout()
plt.savefig(OUT_SVG, format="svg")
plt.close()
