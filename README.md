🧬 EggNOG Functional Pipeline
Este é um conjunto de ferramentas automatizadas para a visualização e interpretação funcional de anotações genômicas geradas pelo eggnog-mapper. O pipeline transforma planilhas .xlsx complexas em gráficos vetoriais de alta qualidade (SVG).

🚀 Funcionalidades
Interface Moderna: Interface gráfica construída com CustomTkinter para facilitar a seleção de arquivos e personalização.

Extração de Cores via IA: Carregue uma imagem de referência para extrair automaticamente uma paleta de 11 cores harmônicas utilizando o algoritmo K-Means.

Pipeline de Bioinformática:

COG Category: Gera um gráfico Sunburst com a hierarquia macro e funcional dos grupos COG.

Gene Ontology (GO): Categoriza e conta os termos GO em Biological Process, Cellular Component e Molecular Function.

KEGG Pathway: Mapeia identificadores KO diretamente da API do KEGG para visualizar os níveis metabólicos mais abundantes.

⚠️ Atenção: Formatação da Planilha (Importante)
Para que o programa identifique corretamente os dados, a planilha Excel deve seguir esta regra:

Cabeçalhos na Linha 1: Os nomes das colunas (como COG_category, GOs, KEGG_ko) devem estar obrigatoriamente na primeira linha da planilha.

Limpeza de Arquivos de Cluster: Arquivos vindos de clusters ou servidores costumam trazer linhas de metadados ou comentários no topo. Você deve excluir essas linhas extras antes de rodar o programa, garantindo que o cabeçalho seja a linha 1 do arquivo .xlsx.

🛠️ Pré-requisitos
Certifique-se de ter as seguintes bibliotecas instaladas(caso não tenha só copiar e colar no bash):

Bash
pip install pandas numpy matplotlib plotly requests openpyxl customtkinter Pillow scikit-learn goatools

Nota: O script de Gene Ontology requer o arquivo go.obo no diretório raiz para funcionar corretamente.

📖 Como Usar
Execute o script principal:

Bash
python interface.py
Clique em "Escolher Planilha .xlsx" e selecione o arquivo gerado pelo eggNOG-mapper (já formatado com o cabeçalho na linha 1).

(Opcional) Use o botão "Extrair Cores de uma Imagem" para definir a identidade visual dos seus gráficos.

Clique em "Executar Pipeline" e os arquivos .svg serão gerados na pasta do projeto.