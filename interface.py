import customtkinter as ctk
from tkinter import filedialog, colorchooser
import subprocess
import os
import numpy as np
import tempfile
import pandas as pd
from PIL import Image
from sklearn.cluster import KMeans

# Configurações de aparência
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppEggNOG(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EggNOG Functional Viz - Pipeline")
        self.geometry("600x800")
        
        self.caminho_arquivo = ""
        # Cores iniciais (Paleta padrão)
        self.cores = ["#0B7285", "#1098AD", "#15AABF", "#22B8CF", "#3BC9DB", 
                      "#66D9E8", "#96F2D7", "#63E6BE", "#20C997", "#12B886", "#2F9E44"]

        # --- Layout UI ---
        self.label_titulo = ctk.CTkLabel(self, text="EggNOG Pipeline Manager", font=("Serif", 26, "bold"))
        self.label_titulo.pack(pady=25)

        # Seção de Seleção de Arquivo
        self.btn_arquivo = ctk.CTkButton(self, text="📁 Selecionar Planilha .xlsx", 
                                         command=self.escolher_arquivo, height=40)
        self.btn_arquivo.pack(pady=5)
        self.label_arquivo = ctk.CTkLabel(self, text="Nenhum arquivo selecionado", font=("Arial", 12, "italic"))
        self.label_arquivo.pack(pady=5)

        ctk.CTkLabel(self, text="—" * 30, text_color="gray").pack(pady=10)

        # Seção de Estilo (IA de Cores)
        self.label_estilo = ctk.CTkLabel(self, text="Identidade Visual do Projeto", font=("Arial", 14, "bold"))
        self.label_estilo.pack(pady=5)
        
        self.btn_imagem = ctk.CTkButton(self, text="🎨 Extrair Paleta de uma Imagem", 
                                        fg_color="#495057", hover_color="#343a40",
                                        command=self.extrair_cores_da_imagem)
        self.btn_imagem.pack(pady=10)

        # Grade de Cores (Visualização e Ajuste Manual)
        self.frame_cores = ctk.CTkFrame(self)
        self.frame_cores.pack(pady=10, padx=20)

        self.botoes_cores = []
        for i in range(11):
            btn = ctk.CTkButton(self.frame_cores, text="", width=45, height=45, 
                                fg_color=self.cores[i], corner_radius=8,
                                command=lambda idx=i: self.escolher_cor_manual(idx))
            btn.grid(row=i//4, column=i%4, padx=8, pady=8)
            self.botoes_cores.append(btn)

        # Botão de Execução Final
        self.btn_run = ctk.CTkButton(self, text="📊Gerar o Gráfico", 
                                     height=60, font=("Arial", 18, "bold"),
                                     fg_color="#2F9E44", hover_color="#237A35",
                                     command=self.executar_scripts)
        self.btn_run.pack(pady=40, padx=50, fill="x")

    # --- Lógica de Limpeza de Dados ---
    def limpar_planilha(self, caminho_original):
        """Remove comentários (#) e garante cabeçalho na linha 1."""
        try:
            # O Pandas com comment='#' ignora as linhas de metadados do cluster
            df = pd.read_excel(caminho_original, comment='#')
            
            # Criar um arquivo temporário para processamento
            temp_file = os.path.join(tempfile.gettempdir(), "eggnog_processed.xlsx")
            df.to_excel(temp_file, index=False)
            return temp_file
        except Exception as e:
            print(f"Erro na limpeza automática: {e}")
            return caminho_original

    # --- Lógica de UI e Processamento ---
    def escolher_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if caminho:
            self.caminho_arquivo = caminho
            self.label_arquivo.configure(text=f"Planilha: {os.path.basename(caminho)}")

    def extrair_cores_da_imagem(self):
        caminho_img = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if not caminho_img: return

        img = Image.open(caminho_img).copy()
        img = img.resize((100, 100))
        img_data = np.array(img).reshape(-1, 3)
        
        # IA K-Means para agrupar 11 cores dominantes
        kmeans = KMeans(n_clusters=11, n_init=10).fit(img_data)
        cores_rgb = kmeans.cluster_centers_.astype(int)

        for i, rgb in enumerate(cores_rgb):
            hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
            self.cores[i] = hex_color
            self.botoes_cores[i].configure(fg_color=hex_color)

    def escolher_cor_manual(self, index):
        cor = colorchooser.askcolor(initialcolor=self.cores[index])[1]
        if cor:
            self.cores[index] = cor
            self.botoes_cores[index].configure(fg_color=cor)

    def executar_scripts(self):
        if not self.caminho_arquivo:
            print("❌ Selecione o arquivo primeiro!")
            return

        # 1. Limpeza automática
        print("🧹 Limpando metadados da planilha...")
        arquivo_limpo = self.limpar_planilha(self.caminho_arquivo)

        # 2. Execução dos scripts filhos
        scripts = ["COG_category.py", "gene_ontology.py", "workflow_KEGG.py"]
        current_dir = os.path.dirname(os.path.abspath(__file__))

        for script in scripts:
            path = os.path.join(current_dir, script)
            if os.path.exists(path):
                print(f"⚙️ Processando {script}...")
                subprocess.run(["python", path, arquivo_limpo] + self.cores)
            else:
                print(f"⚠️ Script {script} não encontrado no diretório.")
        
        print("✅ Pipeline Finalizado! Gráficos gerados com sucesso.")

if __name__ == "__main__":
    app = AppEggNOG()
    app.mainloop()