import customtkinter as ctk
from tkinter import filedialog, colorchooser
import subprocess
import os
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

# Configurações de aparência
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppNoticias(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Montador de gráficos do EggNog Mapper")
        self.geometry("600x750")
        
        self.caminho_arquivo = ""
        # Cores iniciais padrão
        self.cores = ["#0B7285", "#1098AD", "#15AABF", "#22B8CF", "#3BC9DB", 
                      "#66D9E8", "#96F2D7", "#63E6BE", "#20C997", "#12B886", "#2F9E44"]

        # --- Layout ---
        self.label_titulo = ctk.CTkLabel(self, text="Configurações da Análise", font=("Serif", 24, "bold"))
        self.label_titulo.pack(pady=20)

        # Seção de Arquivo
        self.btn_arquivo = ctk.CTkButton(self, text="📁 Escolher Planilha .xlsx", command=self.escolher_arquivo)
        self.btn_arquivo.pack(pady=5)
        self.label_arquivo = ctk.CTkLabel(self, text="Nenhum arquivo selecionado", font=("Arial", 12, "italic"))
        self.label_arquivo.pack(pady=5)

        # Seção de Imagem (A sua nova ideia!)
        self.label_img = ctk.CTkLabel(self, text="Estilo Visual:", font=("Arial", 14, "bold"))
        self.label_img.pack(pady=(20, 5))
        self.btn_imagem = ctk.CTkButton(self, text="🖼️ Extrair Cores de uma Imagem", 
                                        fg_color="#5c5c5c", hover_color="#3d3d3d",
                                        command=self.extrair_cores_da_imagem)
        self.btn_imagem.pack(pady=5)

        # Grid para os botões de cores
        self.label_cores = ctk.CTkLabel(self, text="Paleta Ativa (clique para ajustar):", font=("Arial", 14, "bold"))
        self.label_cores.pack(pady=(20, 10))
        
        self.frame_cores = ctk.CTkFrame(self)
        self.frame_cores.pack(pady=10, padx=20)

        self.botoes_cores = []
        for i in range(11):
            btn = ctk.CTkButton(self.frame_cores, text="", width=45, height=45, 
                                fg_color=self.cores[i], corner_radius=10,
                                command=lambda idx=i: self.escolher_cor_manual(idx))
            btn.grid(row=i//4, column=i%4, padx=8, pady=8)
            self.botoes_cores.append(btn)

        # Botão Executar
        self.btn_run = ctk.CTkButton(self, text="📊Gerar gráficos", 
                                     height=50, font=("Arial", 16, "bold"),
                                     fg_color="#2F9E44", hover_color="#237A35",
                                     command=self.executar_scripts)
        self.btn_run.pack(pady=40)

    def escolher_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if caminho:
            self.caminho_arquivo = caminho
            self.label_arquivo.configure(text=f"Arquivo: {os.path.basename(caminho)}")

    def extrair_cores_da_imagem(self):
        caminho_img = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if not caminho_img:
            return

        # Processamento da Imagem
        img = Image.open(caminho_img).copy()
        img = img.resize((100, 100)) # Redimensiona para ser mais rápido
        img_data = np.array(img)
        
        # Prepara os dados para o K-Means (lista de pixels RGB)
        pixels = img_data.reshape(-1, 3)
        
        # Algoritmo K-Means para achar as 11 cores dominantes
        kmeans = KMeans(n_clusters=11, n_init=10)
        kmeans.fit(pixels)
        cores_rgb = kmeans.cluster_centers_.astype(int)

        # Converte RGB para Hexadecimal e atualiza a interface
        for i, rgb in enumerate(cores_rgb):
            hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
            self.cores[i] = hex_color
            self.botoes_cores[i].configure(fg_color=hex_color)
        
        print("🎨 Paleta extraída com sucesso da imagem!")

    def escolher_cor_manual(self, index):
        cor = colorchooser.askcolor(initialcolor=self.cores[index])[1]
        if cor:
            self.cores[index] = cor
            self.botoes_cores[index].configure(fg_color=cor)

    def executar_scripts(self):
        if not self.caminho_arquivo:
            print("❌ Erro: Selecione um arquivo .xlsx primeiro!")
            return

        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts = ["COG_category.py", "gene_ontology.py", "workflow_KEGG.py"] # Adicione o publisher.py aqui depois

        for script in scripts:
            script_path = os.path.join(current_dir, script)
            print(f"Running {script}...")
            # Envia o arquivo + as 11 cores
            subprocess.run(["python", script_path, self.caminho_arquivo] + self.cores)
        
        print("🏁 Todos os processos foram concluídos!")

if __name__ == "__main__":
    app = AppNoticias()
    app.mainloop()