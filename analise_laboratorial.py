# analise_laboratorial.py (Versão 7.30 - Correção de Legenda Duplicada e Posição na Aba 'Alterados' e Card de Exame)

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates 
import numpy as np
import random
from matplotlib.figure import Figure 
import datetime
import re 
from matplotlib import gridspec 
try:
    import mplcursors 
except ImportError:
    mplcursors = None 

# Configuração global de Matplotlib
plt.style.use('seaborn-v0_8-whitegrid') 

# --- Funções Auxiliares de Conversão ---

def _converter_idade_para_anos(idade_str):
    """
    Converte strings de idade (ex: '10d', '6m', '25') para um valor numérico em anos (float).
    Usada para processar a coluna 'idade' do CSV.
    """
    if pd.isna(idade_str):
        return np.nan
        
    idade_str = str(idade_str).strip().lower().replace(',', '.')
    
    match = re.match(r'^(\d+(\.\d+)?)\s*(d|m)$', idade_str)
    
    if match:
        valor = float(match.group(1))
        unidade = match.group(3)
        if unidade == 'd':
            return round(valor / 365.25, 4) 
        elif unidade == 'm':
            return round(valor / 12, 2)
    
    try:
        return float(idade_str)
    except ValueError:
        return np.nan
        
def _converter_idade_input_para_anos(idade_str):
    """
    Converte strings de idade de input manual (ex: '10d', '6m', '25') para int/float em ANOS.
    Usada para processar o filtro de Idade.
    """
    if not idade_str:
        return 0.0 
        
    idade_str = str(idade_str).strip().lower().replace(',', '.')
    
    match = re.match(r'^(\d+)\s*d$', idade_str)
    if match: # Idade em dias
        return float(match.group(1)) / 365.25
        
    match = re.match(r'^(\d+)\s*m$', idade_str)
    if match: # Idade em meses
        return float(match.group(1)) / 12.0 

    try:
        # Se for apenas número, assume anos.
        return float(idade_str)
    except ValueError:
             raise ValueError(f"Formato de idade inválido: {idade_str}. Use 'anos inteiros', 'Xd' (dias) ou 'Xm' (meses).")
             
def _formatar_idade_para_exibicao(idade):
    """Formata o valor de idade de volta para o formato de exibição (ex: 0.01 -> 5d)."""
    if idade == 0:
        return "0"
    if idade < 1:
        # Se menos de 30 dias, mostra em dias
        if idade * 365.25 < 30:
            return f"{round(idade * 365.25)}d"
        # Se menos de 1 ano, mostra em meses
        else:
             return f"{round(idade * 12)}m"
    return str(int(idade)) 

# --- Classes VRManager e PeriodSelector ---

class VRManager(ttk.Toplevel):
    
    def __init__(self, master, exames_disponiveis, regras_vr):
        super().__init__(master)
        self.master = master
        self.regras_vr = regras_vr.copy() 
        self.exames_disponiveis = exames_disponiveis
        
        self.title("Gerenciar Valores de Referência (VRs)")
        self.geometry("800x450")
        self.transient(master) 
        self.grab_set() 
        
        self.setup_layout()

    def setup_layout(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # ----------------------------------------------------------------------
        # 1. Adicionar Nova Regra de Referência
        # ----------------------------------------------------------------------
        frame_adicionar = ttk.LabelFrame(main_frame, text="1. Adicionar Nova Regra de Referência", padding=10, bootstyle=PRIMARY)
        frame_adicionar.pack(fill=X, pady=10)

        input_frame = ttk.Frame(frame_adicionar, padding=5)
        input_frame.pack(fill=X, pady=5)
        
        ttk.Label(input_frame, text="Exame").grid(row=0, column=0, padx=5)
        ttk.Label(input_frame, text="Sexo").grid(row=0, column=1, padx=5)
        ttk.Label(input_frame, text="Idade Min (a/d/m)").grid(row=0, column=2, padx=5)
        ttk.Label(input_frame, text="Idade Max (a/d/m)").grid(row=0, column=3, padx=5)
        ttk.Label(input_frame, text="Ref Min").grid(row=0, column=4, padx=5)
        ttk.Label(input_frame, text="Ref Max").grid(row=0, column=5, padx=5)
        ttk.Label(input_frame, text="Ação").grid(row=0, column=6, padx=5) 

        self.exame_var = tk.StringVar(self)
        self.exame_var.set(self.exames_disponiveis[0] if self.exames_disponiveis else "SEM EXAMES")
        self.sexo_var = tk.StringVar(self)
        self.sexo_var.set("AMBOS")
        self.idade_min_var = tk.StringVar(self, value="0")
        self.idade_max_var = tk.StringVar(self, value="120")
        self.ref_min_var = tk.StringVar(self)
        self.ref_max_var = tk.StringVar(self)

        row_index = 1
        ttk.Combobox(input_frame, textvariable=self.exame_var, values=self.exames_disponiveis, state='readonly', width=12).grid(row=row_index, column=0, padx=5)
        ttk.Combobox(input_frame, textvariable=self.sexo_var, values=["AMBOS", "MASCULINO", "FEMININO"], state='readonly', width=8).grid(row=row_index, column=1, padx=5)
        ttk.Entry(input_frame, textvariable=self.idade_min_var, width=8).grid(row=row_index, column=2, padx=5)
        ttk.Entry(input_frame, textvariable=self.idade_max_var, width=8).grid(row=row_index, column=3, padx=5)
        ttk.Entry(input_frame, textvariable=self.ref_min_var, width=8).grid(row=row_index, column=4, padx=5)
        ttk.Entry(input_frame, textvariable=self.ref_max_var, width=8).grid(row=row_index, column=5, padx=5)
        ttk.Button(input_frame, text="+ Adicionar Regra", command=self.adicionar_regra_manual, bootstyle=SUCCESS).grid(row=row_index, column=6, padx=5)
        
        
        # ----------------------------------------------------------------------
        # 2. Regras Ativas (Tabela)
        # ----------------------------------------------------------------------
        frame_regras = ttk.LabelFrame(main_frame, text="Regras Ativas (Clique em uma regra e use o botão 'Remover')", padding=10, bootstyle=PRIMARY)
        frame_regras.pack(fill=X, pady=10)

        columns = ("Exame", "Sexo", "Idade Min", "Idade Max", "Ref Min", "Ref Max")
        self.tree = ttk.Treeview(frame_regras, columns=columns, show='headings', bootstyle=PRIMARY, height=5)
        
        for col in columns:
            self.tree.heading(col, text=col.replace(" ", "\n"))
            self.tree.column(col, width=80 if "Ref" in col else 100, anchor=CENTER)

        self.tree.pack(fill=X, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_treeview_select)
        
        ttk.Button(main_frame, text="Remover Regra Selecionada", command=self.remover_regra_selecionada, bootstyle=DANGER).pack(fill=X, pady=10)

        
        self.update_treeview()


    def on_treeview_select(self, event):
        pass
            
    def update_treeview(self):
        """Limpa e preenche o Treeview com as regras VR atuais."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for i, r in enumerate(self.regras_vr):
            
            idade_min_display = _formatar_idade_para_exibicao(r['idade_min'])
            idade_max_display = _formatar_idade_para_exibicao(r['idade_max'])

            self.tree.insert('', 'end', text=str(i), values=(
                r['exame'], r['sexo'], idade_min_display, idade_max_display, 
                f"{r['ref_min']:.2f}", f"{r['ref_max']:.2f}"
            ))
        
        
    def remover_regra_selecionada(self):
        """Remove a regra VR selecionada e atualiza os gráficos."""
        item_id = self.tree.focus()
        if not item_id:
            self.master.show_message("Aviso", "Selecione uma regra na tabela para remover.", type="warning")
            return
            
        row_index = int(self.tree.item(item_id, 'text')) 
        
        if 0 <= row_index < len(self.regras_vr):
            self.regras_vr.pop(row_index)
            self.update_treeview()
            self.master.show_message("Sucesso", "Regra removida e análise atualizada.")
            self.master.regras_vr = self.regras_vr 
            self.master.analisar_dados() 
        else:
             self.master.show_message("Erro", "Erro ao remover regra: índice inválido.", type="error")

            
    def adicionar_regra_manual(self):
        """Adiciona uma nova regra VR a partir dos campos de entrada."""
        try:
            idade_min_convertida = _converter_idade_input_para_anos(self.idade_min_var.get())
            idade_max_convertida = _converter_idade_input_para_anos(self.idade_max_var.get())

            nova_regra = {
                'exame': self.exame_var.get().upper(),
                'sexo': self.sexo_var.get().upper(),
                'idade_min': idade_min_convertida,
                'idade_max': idade_max_convertida,
                'ref_min': float(self.ref_min_var.get().replace(',', '.')),
                'ref_max': float(self.ref_max_var.get().replace(',', '.')),
            }
            
            if not nova_regra['exame'] or nova_regra['exame'] == "SEM EXAMES":
                 raise ValueError("Selecione ou digite um Exame válido.")
            if nova_regra['ref_min'] >= nova_regra['ref_max']:
                 raise ValueError("Ref Min deve ser menor que Ref Max.")
            if nova_regra['idade_min'] >= nova_regra['idade_max'] and nova_regra['idade_max'] != 0.0:
                 raise ValueError("Idade Min deve ser menor que Idade Max.")
                 
            self.regras_vr.append(nova_regra)
            self.update_treeview()
            self.master.show_message("Sucesso", "Regra adicionada e análise atualizada.")
            self.master.regras_vr = self.regras_vr 
            self.master.analisar_dados() 
            
            self.ref_min_var.set("")
            self.ref_max_var.set("")
            
        except ValueError as e:
            self.master.show_message("Erro de Entrada", f"Erro: {e}. Verifique se os campos numéricos estão corretos (use ponto para decimal).", type="error")
        except Exception as e:
            self.master.show_message("Erro", f"Erro desconhecido ao adicionar regra: {e}", type="error")


class PeriodSelector(ttk.Toplevel):
    
    def __init__(self, master, datas_disponiveis, callback):
        super().__init__(master)
        self.master = master
        self.datas_disponiveis = datas_disponiveis
        self.callback = callback
        
        self.title("Seleção de Período Personalizado")
        self.geometry("400x200") 
        self.transient(master) 
        self.grab_set() 
        self.resizable(False, False)
        
        self.data_inicio_var = tk.StringVar(self)
        self.data_fim_var = tk.StringVar(self)
        
        if self.datas_disponiveis:
             self.data_inicio_var.set(self.datas_disponiveis[0])
             self.data_fim_var.set(self.datas_disponiveis[-1])
        else:
             self.data_inicio_var.set("N/A")
             self.data_fim_var.set("N/A")

        self.setup_layout()

    def setup_layout(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(main_frame, text="Selecione o Período de Análise:", font=("Helvetica Neue", 12, "bold"), bootstyle=PRIMARY).pack(pady=(0, 15))

        frame_inicio = ttk.Frame(main_frame)
        frame_inicio.pack(fill=X, pady=5)
        ttk.Label(frame_inicio, text="Data de Início:", width=15).pack(side=LEFT)
        combo_inicio = ttk.Combobox(frame_inicio, textvariable=self.data_inicio_var, values=self.datas_disponiveis, state='readonly', bootstyle=INFO)
        combo_inicio.pack(side=RIGHT, fill=X, expand=True)

        frame_fim = ttk.Frame(main_frame)
        frame_fim.pack(fill=X, pady=5)
        ttk.Label(frame_fim, text="Data de Fim:", width=15).pack(side=LEFT)
        combo_fim = ttk.Combobox(frame_fim, textvariable=self.data_fim_var, values=self.datas_disponiveis, state='readonly', bootstyle=INFO)
        combo_fim.pack(side=RIGHT, fill=X, expand=True)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy, bootstyle=SECONDARY).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(btn_frame, text="Aplicar Filtro", command=self.aplicar_filtro, bootstyle=SUCCESS).pack(side=LEFT, fill=X, expand=True, padx=5)

    def aplicar_filtro(self):
        """Executa o callback com as datas selecionadas e fecha a janela."""
        data_inicio = self.data_inicio_var.get()
        data_fim = self.data_fim_var.get()
        
        if data_inicio == "N/A" or data_fim == "N/A":
             self.master.show_message("Aviso", "Nenhuma data disponível para seleção.", type="warning")
             self.destroy()
             return

        try:
            # Garante que o formato de leitura é o DD/MM/AAAA
            inicio_dt = datetime.datetime.strptime(data_inicio, '%d/%m/%Y').date()
            fim_dt = datetime.datetime.strptime(data_fim, '%d/%m/%Y').date()
            
            if inicio_dt > fim_dt:
                self.master.show_message("Erro", "A Data de Início não pode ser maior que a Data de Fim.", type="error")
                return

            self.callback(data_inicio, data_fim)
            self.destroy()
            
        except ValueError:
            self.master.show_message("Erro", "Ocorreu um erro ao processar as datas. Verifique o formato DD/MM/AAAA.", type="error")
            


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly") 

        # MODIFICAÇÃO SOLICITADA: Nome da aplicação na barra de título
        self.title("Metrion - Sistema de Análise Estatística")
        self.geometry("1400x900") 
        self.minsize(1200, 750) 

        self.df = None
        self.df_analise = None 
        self.regras_vr = [] 
        self.exames_disponiveis = []
        
        self.total_registros = tk.IntVar(value=0)
        # ALTERADO: Mudança de tk.IntVar para tk.StringVar para exibir o nome do exame
        self.exame_card_display = tk.StringVar(value="Nenhum") 
        self.idade_media = tk.StringVar(value="N/A")
        self.resultado_medio = tk.StringVar(value="N/A")

        self.exame_selecionado = tk.StringVar(self)
        self.exame_selecionado.set("Selecione o Exame") 
        # Garante que o card atualize quando o exame mudar
        self.exame_selecionado.trace_add("write", self.handle_exame_change) 

        self.aba_ativa = tk.StringVar(self, value="Análise Geral")
        self.aba_ativa.trace_add("write", self.handle_aba_change) 
        
        # Manter apenas "Completo" para o rádio button
        self.periodo_ativo = tk.StringVar(self, value="Completo")
        self.data_inicio = None 
        self.data_fim = None    
        self.datas_disponiveis = [] 
        self.periodo_display = tk.StringVar(self, value="Período: Completo") 
        
        self.idade_min_filtro_var = tk.StringVar(self, value="")
        self.idade_max_filtro_var = tk.StringVar(self, value="")
        self.idade_min_filtro = None 
        self.idade_max_filtro = None 
        self.faixa_idade_display = tk.StringVar(self, value="Faixa Etária: Completa")
        
        self.fig = None
        self.ax = None 
        self.canvas = None
        self.canvas_widget = None

        self.setup_dashboard_layout()

    def show_message(self, title, message, type="info"):
        """Exibe uma messagebox customizada."""
        if type == "error":
            tk.messagebox.showerror(title, message, icon='warning') 
        elif type == "warning":
            tk.messagebox.showwarning(title, message, icon='warning')
        else:
            tk.messagebox.showinfo(title, message, icon='info')
            
    def criar_card(self, parent_frame, titulo, valor_var, icone):
        """Cria um card de métricas."""
        card = ttk.Frame(parent_frame, padding="15 10", bootstyle=LIGHT, style='Card.TFrame')
        self.style.configure('Card.TFrame', background='white')
        
        main_content_frame = ttk.Frame(card)
        main_content_frame.pack(fill=BOTH, expand=True)

        ttk.Label(main_content_frame, text=icone, font=("Helvetica Neue", 36), bootstyle=INFO).pack(side=LEFT, padx=(0, 15), pady=0, anchor=CENTER)
        
        data_container_frame = ttk.Frame(main_content_frame)
        data_container_frame.pack(side=LEFT, fill=Y, expand=True)
        
        ttk.Label(data_container_frame, textvariable=valor_var, font=("Helvetica Neue", 28, "bold"), bootstyle=PRIMARY).pack(anchor=W, pady=(0, 0))
        ttk.Label(data_container_frame, text=titulo, font=("Helvetica Neue", 10), bootstyle=SECONDARY).pack(anchor=W, pady=(0, 0))
        
        return card
        
    def atualizar_menus_exame(self):
        """Atualiza o OptionMenu com a lista de exames disponíveis."""
        if not hasattr(self, 'menu_exames'):
            return 
            
        menu = self.menu_exames["menu"]
        menu.delete(0, "end")
        
        menu_items = self.exames_disponiveis if self.exames_disponiveis else ["Selecione o Exame"]

        if self.exame_selecionado.get() not in self.exames_disponiveis:
             self.exame_selecionado.set(menu_items[0])
            
        for exame in menu_items:
            menu.add_command(label=exame, command=tk._setit(self.exame_selecionado, exame))

    def atualizar_cards_metricas(self, df_data):
        """Calcula e atualiza os valores exibidos nos cards."""
        self.total_registros.set(len(df_data))
        
        if df_data.empty:
            # self.tipos_exames.set(0) # Linha antiga
            self.exame_card_display.set("Nenhum") # Novo
            self.idade_media.set("N/A")
            self.resultado_medio.set("N/A")
            return

        # Lógica para o card "Exame"
        selected_exame = self.exame_selecionado.get()
        if selected_exame != "Selecione o Exame":
            # Se um exame está selecionado (para plotagem), exibe o nome dele
            self.exame_card_display.set(selected_exame)
        else:
            # Se não, exibe a contagem de tipos de exames
            self.exame_card_display.set(f"{df_data['exame'].nunique()} Exames")
        
        idade_med = df_data['idade'].mean()
        self.idade_media.set(f"{idade_med:.0f} anos" if not pd.isna(idade_med) else "N/A")
        
        resultado_med = df_data['resultado'].mean()
        self.resultado_medio.set(f"{resultado_med:.2f}" if not pd.isna(resultado_med) else "N/A")


    def setup_dashboard_layout(self):
        # Frame principal
        main_dashboard_frame = ttk.Frame(self, padding="15", bootstyle=LIGHT)
        main_dashboard_frame.pack(fill=BOTH, expand=True)

        # -----------------------------------------------------
        # 1. Header 
        # -----------------------------------------------------
        header_frame = ttk.Frame(main_dashboard_frame, padding="15 10", bootstyle=LIGHT)
        header_frame.pack(fill=X, pady=(0, 20))
        
        # O código original (ttk.Label(header_frame, text="Sistema de Análise Estatística", ...)) foi removido
        
        # MODIFICAÇÃO SOLICITADA: Título "Metrion" (Azul) e Subtítulo (Cinza), ambos centralizados
        
        # Configuração dos Styles customizados para cor e alinhamento
        # Título: Azul, Centralizado, Sem Preenchimento (fundo do frame)
        # O self.style.lookup('TFrame', 'background') garante que o background seja o mesmo do frame, simulando "sem preenchimento"
        self.style.configure('MetrionTitle.TLabel', foreground='#0077b6', background=self.style.lookup('TFrame', 'background'), font=("Helvetica Neue", 36, "bold"))
        # Subtítulo: Cinza, Centralizado, Sem Preenchimento (fundo do frame)
        self.style.configure('MetrionSubtitle.TLabel', foreground='gray', background=self.style.lookup('TFrame', 'background'), font=("Helvetica Neue", 16))
        
        # Frame Container para centralizar o título, ocupando todo o espaço restante à esquerda do action_frame
        title_container = ttk.Frame(header_frame, bootstyle=LIGHT)
        title_container.pack(side=LEFT, fill=X, expand=True) 

        # Título Principal: Metrion
        ttk.Label(title_container, text="Metrion", style='MetrionTitle.TLabel').pack(anchor=CENTER)

        # Subtítulo: Sistema de Análise Estatística
        ttk.Label(title_container, text="Sistema de Análise Estatística", style='MetrionSubtitle.TLabel').pack(anchor=CENTER)
        
        # FIM DA MODIFICAÇÃO
        
        action_frame = ttk.Frame(header_frame)
        action_frame.pack(side=RIGHT)
        
        # REMOVIDO: ttk.Button(action_frame, text="Iniciar Análise", command=self.analisar_dados, bootstyle=SUCCESS).pack(side=RIGHT, padx=5)
        ttk.Button(action_frame, text="Gerenciar Valores de Referência (VR)", command=self.abrir_manager_vr, bootstyle=INFO).pack(side=RIGHT, padx=5)
        

        # -----------------------------------------------------
        # 2. Upload e Status do Arquivo 
        # -----------------------------------------------------
        upload_frame = ttk.Frame(main_dashboard_frame, padding="10", bootstyle=LIGHT, style='Upload.TFrame')
        upload_frame.pack(fill=X, pady=(0, 20))
        self.style.configure('Upload.TFrame', background='white', bordercolor='#dddddd', borderwidth=1)
        
        ttk.Button(upload_frame, text="Upload CSV", command=self.carregar_arquivo, bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))
        self.lbl_arquivo = ttk.Label(upload_frame, text="Nenhum arquivo carregado", bootstyle=SECONDARY)
        self.lbl_arquivo.pack(side=LEFT)
        
        # INSTRUÇÃO REMOVIDA: Era aqui que ficava "Clique em 'Iniciar Análise'"

        # -----------------------------------------------------
        # 3. Cards de Métricas 
        # -----------------------------------------------------
        cards_frame = ttk.Frame(main_dashboard_frame, padding="0", bootstyle=LIGHT)
        cards_frame.pack(fill=X, pady=(0, 20))
        
        card_container = ttk.Frame(cards_frame)
        card_container.pack(fill=X, expand=True)
        
        self.criar_card(card_container, "Total de Registros", self.total_registros, "📈").pack(side=LEFT, fill=X, expand=True, padx=5)
        # ALTERADO: Mudança do título e da variável para exibir o nome do exame.
        self.criar_card(card_container, "Exame", self.exame_card_display, "🧪").pack(side=LEFT, fill=X, expand=True, padx=5)
        self.criar_card(card_container, "Idade Média", self.idade_media, "👤").pack(side=LEFT, fill=X, expand=True, padx=5)
        self.criar_card(card_container, "Resultado Médio", self.resultado_medio, "🔬").pack(side=LEFT, fill=X, expand=True, padx=5)


        # -----------------------------------------------------
        # 4. Filtros de Navegação (Abas), Período e Idade
        # -----------------------------------------------------
        filter_frame = ttk.Frame(main_dashboard_frame, padding="10", bootstyle=LIGHT, relief=FLAT, borderwidth=1, style='Filter.TFrame')
        filter_frame.pack(fill=X, pady=(0, 15))
        
        self.style.configure('Filter.TFrame', background='white', bordercolor='#dddddd', borderwidth=1)
        
        # --- 4.1. Filtro de Abas ---
        aba_options = ["Análise Geral", "Por Sexo", "Por Idade", "Temporal", "Alterados", "Qualidade"]
        tabs_frame = ttk.Frame(filter_frame)
        tabs_frame.pack(side=LEFT)
        
        for i, aba in enumerate(aba_options):
            btn = ttk.Radiobutton(tabs_frame, text=aba, value=aba, variable=self.aba_ativa, 
                                  command=self.atualizar_grafico, bootstyle=(TOOLBUTTON, INFO if aba == "Análise Geral" else SECONDARY))
            btn.pack(side=LEFT, padx=3)
        
        ttk.Separator(filter_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10) 
        
        # --- 4.2. Filtro de Período (Apenas Completo e Custom) ---
        period_frame = ttk.Frame(filter_frame, padding=(10, 0)) 
        period_frame.pack(side=LEFT, padx=20, fill=Y)

        # Apenas "Completo" como Radio Button
        period_options = ["Completo"]
        for periodo in period_options:
            btn = ttk.Radiobutton(period_frame, text=periodo, value=periodo, 
                                  variable=self.periodo_ativo, 
                                  command=self.analisar_dados, 
                                  bootstyle=(TOOLBUTTON, SUCCESS))
            btn.pack(side=LEFT, padx=3)
            
        ttk.Button(period_frame, text="Escolher Período", 
                   command=self.abrir_seletor_periodo, bootstyle=INFO, width=15).pack(side=LEFT, padx=10)
                   
        ttk.Separator(filter_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10) 
                   
        # --- 4.3. Filtro de Idade ---
        idade_filter_frame = ttk.Frame(filter_frame)
        idade_filter_frame.pack(side=LEFT, padx=10, fill=Y)

        ttk.Label(idade_filter_frame, text="Faixa Etária (a/d/m):", bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 5))
        
        ttk.Entry(idade_filter_frame, textvariable=self.idade_min_filtro_var, width=5, justify=CENTER).pack(side=LEFT, padx=3)
        ttk.Label(idade_filter_frame, text="até").pack(side=LEFT)
        ttk.Entry(idade_filter_frame, textvariable=self.idade_max_filtro_var, width=5, justify=CENTER).pack(side=LEFT, padx=3)
        
        ttk.Button(idade_filter_frame, text="Aplicar", command=self.aplicar_filtro_idade, bootstyle=INFO, width=7).pack(side=LEFT, padx=(10, 3))
        ttk.Button(idade_filter_frame, text="Limpar", command=self.remover_filtro_idade, bootstyle=SECONDARY, width=7).pack(side=LEFT)


        # -----------------------------------------------------
        # 5. Painel de Visualização (Gráfico) 
        # -----------------------------------------------------
        self.chart_container = ttk.Frame(main_dashboard_frame, padding="15", bootstyle=LIGHT, relief=FLAT, borderwidth=1, style='Filter.TFrame')
        self.chart_container.pack(fill=BOTH, expand=True)

        self.chart_title = ttk.Label(self.chart_container, text="Dashboard de Análise", font=("Helvetica Neue", 14, "bold"), bootstyle=PRIMARY)
        self.chart_title.pack(anchor=W)
        
        subtitle_frame = ttk.Frame(self.chart_container)
        subtitle_frame.pack(fill=X, pady=(0, 5))

        self.chart_subtitle_periodo = ttk.Label(subtitle_frame, textvariable=self.periodo_display, font=("Helvetica Neue", 10), bootstyle=SECONDARY)
        self.chart_subtitle_periodo.pack(side=LEFT, padx=(0, 15))
        
        self.chart_subtitle_idade = ttk.Label(subtitle_frame, textvariable=self.faixa_idade_display, font=("Helvetica Neue", 10), bootstyle=SECONDARY)
        self.chart_subtitle_idade.pack(side=LEFT)

        self.control_frame = ttk.Frame(self.chart_container)
        self.control_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Label(self.control_frame, text="Exame:", bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        # self.exame_selecionado.trace_add("write", self.atualizar_grafico) # Removido para usar handle_exame_change que chama atualizar_grafico e atualiza cards
        self.menu_exames = ttk.OptionMenu(self.control_frame, self.exame_selecionado, 
                                          "Selecione o Exame", "Selecione o Exame", bootstyle=INFO)
        self.menu_exames.pack(side=LEFT)
        
        # Frame para hospedar o gráfico
        self.plot_frame = ttk.Frame(self.chart_container)
        self.plot_frame.pack(fill=BOTH, expand=True)
        
        # Setup inicial do layout (single plot)
        self._setup_plot_area(single_plot=True)

    def _setup_plot_area(self, single_plot=True):
        """
        Prepara a figura, o eixo e o canvas.
        Garante que o canvas anterior seja destruído e um novo criado.
        """
        # 1. Destrói o canvas anterior (widget e referência)
        if self.canvas_widget:
            self.canvas_widget.destroy()
            self.canvas_widget = None
            self.canvas = None
            
        # 2. Cria uma nova figura
        self.fig = Figure(figsize=(12, 7), dpi=100)
        
        # 3. Adiciona o subplot/eixo principal se for single-plot
        if single_plot:
            self.ax = self.fig.add_subplot(111)
            # Para manter a compatibilidade com a estrutura anterior
            self.axes = {'ax': self.ax} 
        else:
            # Para multi-plot, os subplots (axes) serão criados dentro das funções de plotagem
            self.ax = None 
            self.axes = {} 
            
        # 4. Cria e empacota o novo canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=BOTH, expand=True)


    def _cleanup_plot_frame(self):
        """Limpa apenas as referências internas para garantir que _setup_plot_area recrie o canvas."""
        self.ax = None
        self.axes = {}

    def handle_aba_change(self, *args):
        """Chama a atualização do gráfico quando a aba muda."""
        if not self.df_analise:
            return
        
        self.atualizar_grafico()

    def handle_exame_change(self, *args):
        """Chama a atualização do gráfico E DOS CARDS quando o exame muda."""
        if not self.df_analise:
            return
            
        # Atualiza os cards (para refletir o novo exame selecionado)
        self.atualizar_cards_metricas(self.df_analise)
        # Atualiza o gráfico
        self.atualizar_grafico()
        
    def carregar_arquivo(self):
        """Abre a caixa de diálogo para carregar o arquivo CSV."""
        filepath = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        if not filepath:
            return
            
        try:
            self.df = pd.read_csv(filepath, encoding='utf-8', sep=';', low_memory=False)
            self.lbl_arquivo.config(text=f"Arquivo carregado: {filepath.split('/')[-1]}", bootstyle=SUCCESS)
            self.df.columns = [col.lower().strip() for col in self.df.columns]
            
            # CHAVE: Inicia a análise imediatamente após o carregamento
            self.analisar_dados(primeiro_carregamento=True)
            self.show_message("Sucesso", "Dados carregados, pré-processados e análise iniciada.")

        except FileNotFoundError:
            self.show_message("Erro", "Arquivo não encontrado.", type="error")
        except Exception as e:
            self.show_message("Erro", f"Erro ao ler arquivo CSV. Verifique o formato (separador ';'). Detalhe: {e}", type="error")

    def abrir_seletor_periodo(self):
        """Abre a janela de seleção de período personalizado."""
        if not self.datas_disponiveis:
            self.show_message("Aviso", "Nenhum dado carregado para seleção de período.", type="warning")
            return
            
        PeriodSelector(self, self.datas_disponiveis, self.set_periodo_personalizado)

    def set_periodo_personalizado(self, data_inicio_str, data_fim_str):
        """Define o período personalizado e dispara a análise."""
        self.data_inicio = datetime.datetime.strptime(data_inicio_str, '%d/%m/%Y').date()
        self.data_fim = datetime.datetime.strptime(data_fim_str, '%d/%m/%Y').date()
        
        self.periodo_ativo.set(f"Custom: {data_inicio_str} a {data_fim_str}") 
        self.analisar_dados()

    def aplicar_filtro_idade(self):
        """Aplica o filtro de faixa etária inserido pelo usuário."""
        min_str = self.idade_min_filtro_var.get()
        max_str = self.idade_max_filtro_var.get()
        
        try:
            min_val = _converter_idade_input_para_anos(min_str) if min_str else 0.0
            max_val = _converter_idade_input_para_anos(max_str) if max_str else 120.0 # Valor alto padrão para 'até'

            if min_val >= max_val and max_str: # Se max_str foi preenchido, min deve ser menor que max
                self.show_message("Erro", "Idade Mínima deve ser menor que a Idade Máxima.", type="error")
                return
            
            # Se a idade máxima não foi preenchida (max_str vazio), redefina para None para não filtrar pelo 120.0 padrão.
            self.idade_min_filtro = min_val if min_str else None
            self.idade_max_filtro = max_val if max_str else None
            
            self.analisar_dados()
            
        except ValueError as e:
            self.show_message("Erro de Idade", str(e), type="error")

    def remover_filtro_idade(self):
        """Remove o filtro de faixa etária."""
        self.idade_min_filtro_var.set("")
        self.idade_max_filtro_var.set("")
        self.idade_min_filtro = None
        self.idade_max_filtro = None
        self.analisar_dados()

    def classificar_resultado(self, row):
        """Classifica o resultado como 'NORMAL', 'ALTO' ou 'BAIXO' com base nas regras VR."""
        exame = row['exame']
        sexo = row['sexo']
        idade = row['idade']
        resultado = row['resultado']

        if pd.isna(resultado) or pd.isna(idade) or pd.isna(sexo):
            return 'N/A'

        regras_aplicaveis = [
            r for r in self.regras_vr 
            if r['exame'] == exame and 
               r['idade_min'] <= idade <= r['idade_max'] and 
               (r['sexo'] == sexo or r['sexo'] == 'AMBOS')
        ]
        
        if not regras_aplicaveis:
            return 'SEM VR'

        regras_sexo = [r for r in regras_aplicaveis if r['sexo'] == sexo]
        regras_ambos = [r for r in regras_aplicaveis if r['sexo'] == 'AMBOS']
        
        # Prioriza regras específicas de sexo sobre regras de "AMBOS"
        regras_a_usar = regras_sexo if regras_sexo else regras_ambos
        
        if not regras_a_usar:
            return 'SEM VR'

        # Se houver mais de uma regra aplicável (ex: uma de "AMBOS" e uma de "MASCULINO"), 
        # a classificação usa os limites mais abrangentes entre as regras mais específicas (sexo) ou genéricas (ambos).
        # Neste caso, para simplificar e garantir a detecção de anormalidade, 
        # usaremos o menor ref_min e o maior ref_max de todas as regras aplicáveis.
        
        ref_min = min(r['ref_min'] for r in regras_a_usar)
        ref_max = max(r['ref_max'] for r in regras_a_usar)

        if ref_min <= resultado <= ref_max:
            return 'NORMAL'
        elif resultado < ref_min:
            return 'BAIXO'
        else:
            return 'ALTO'

    def analisar_dados(self, primeiro_carregamento=False):
        """Pré-processa, filtra e analisa os dados brutos."""
        if self.df is None:
            if primeiro_carregamento:
                return
            self.show_message("Aviso", "Nenhum arquivo de dados carregado.", type="warning")
            return
            
        df_temp = self.df.copy()

        # 1. Pré-processamento e Limpeza
        
        if 'data' in df_temp.columns:
            try:
                # CORRIGIDO: Tentativa primária usando o formato brasileiro DD/MM/AAAA
                df_temp['data'] = pd.to_datetime(df_temp['data'], format='%d/%m/%Y', errors='coerce').dt.date
            except Exception:
                # Tenta inferir se falhar
                df_temp['data'] = pd.to_datetime(df_temp['data'], errors='coerce').dt.date
            df_temp.dropna(subset=['data'], inplace=True)
            self.datas_disponiveis = sorted([d.strftime('%d/%m/%Y') for d in df_temp['data'].unique()])

        if 'idade' in df_temp.columns:
            df_temp['idade'] = df_temp['idade'].apply(_converter_idade_para_anos)

        if 'resultado' in df_temp.columns:
            df_temp['resultado'] = df_temp['resultado'].astype(str).str.replace(',', '.', regex=False)
            df_temp['resultado'] = pd.to_numeric(df_temp['resultado'], errors='coerce')
        
        if 'sexo' in df_temp.columns:
            df_temp['sexo'] = df_temp['sexo'].astype(str).str.upper().str.strip().str[0].replace({'M': 'MASCULINO', 'F': 'FEMININO'})

        df_temp.dropna(subset=['exame', 'resultado'], inplace=True)
        
        self.exames_disponiveis = sorted(df_temp['exame'].unique().tolist())
        self.atualizar_menus_exame()


        # 2. Aplicação de Filtros
        
        # --- 2.1. Filtro de Faixa Etária ---
        if self.idade_min_filtro is not None:
            df_temp = df_temp[df_temp['idade'] >= self.idade_min_filtro]
        if self.idade_max_filtro is not None:
            df_temp = df_temp[df_temp['idade'] <= self.idade_max_filtro]
            
        # Atualização do display do filtro de idade
        min_disp = _formatar_idade_para_exibicao(self.idade_min_filtro) if self.idade_min_filtro is not None else "0"
        
        if self.idade_max_filtro is not None:
            max_disp = _formatar_idade_para_exibicao(self.idade_max_filtro)
        elif self.idade_max_filtro_var.get() == "" and self.idade_min_filtro is not None:
             max_disp = "MAX"
        else:
             max_disp = "MAX"
             
        if self.idade_min_filtro is not None or self.idade_max_filtro is not None:
            self.faixa_idade_display.set(f"Faixa Etária: {min_disp} a {max_disp}")
        else:
            self.faixa_idade_display.set("Faixa Etária: Completa")
            
        # --- 2.2. Filtro de Período ---
        periodo = self.periodo_ativo.get()
        if 'Custom:' in periodo:
            # Período customizado
            data_inicio_filtro = self.data_inicio
            data_fim_filtro = self.data_fim
            periodo_display = f"Período: {data_inicio_filtro.strftime('%d/%m/%Y')} a {data_fim_filtro.strftime('%d/%m/%Y')}"
        else:
            # Completo (opção padrão)
            data_inicio_filtro = df_temp['data'].min() if not df_temp.empty else None
            data_fim_filtro = df_temp['data'].max() if not df_temp.empty else None
            self.data_inicio = data_inicio_filtro
            self.data_fim = data_fim_filtro
            periodo_display = "Período: Completo"
            
        self.periodo_display.set(periodo_display)

        if self.data_inicio and self.data_fim and 'data' in df_temp.columns:
            df_temp = df_temp[
                (df_temp['data'] >= self.data_inicio) & 
                (df_temp['data'] <= self.data_fim)
            ]
        
        self.df_analise = df_temp.copy()

        # 3. Classificação VR
        if self.regras_vr and not self.df_analise.empty:
            self.df_analise['status_vr'] = self.df_analise.apply(self.classificar_resultado, axis=1)
        else:
            self.df_analise['status_vr'] = 'SEM VR'
            
        # 4. Atualiza Métricas e Gráfico
        self.atualizar_cards_metricas(self.df_analise)
        self.atualizar_grafico()


    def atualizar_grafico(self, *args):
        """Plota o gráfico apropriado baseado na aba ativa e no exame selecionado."""
        exame = self.exame_selecionado.get()
        aba = self.aba_ativa.get()

        # Atualiza os cards (necessário aqui também, pois a seleção do exame os afeta)
        if self.df_analise is not None:
             self.atualizar_cards_metricas(self.df_analise)

        if self.df_analise is None or self.df_analise.empty or exame == "Selecione o Exame":
            self._setup_plot_area(single_plot=True)
            self.ax.text(0.5, 0.5, 'Nenhum dado ou exame selecionado para plotagem.', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=14, color='gray')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.fig.tight_layout()
            self.canvas.draw()
            self.chart_title.config(text="Dashboard de Análise")
            return

        df_exame = self.df_analise[self.df_analise['exame'] == exame].copy()
        
        if df_exame.empty:
            self._setup_plot_area(single_plot=True)
            self.ax.text(0.5, 0.5, f'Nenhum registro para o exame "{exame}" após a filtragem.', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=14, color='gray')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.fig.tight_layout()
            self.canvas.draw()
            self.chart_title.config(text="Dados Insuficientes")
            return
            
        self.chart_title.config(text=f"Análise: {exame} - {aba}")

        # Executa a plotagem de acordo com a aba (configura o layout antes de plotar)
        if aba in ["Análise Geral", "Por Idade", "Temporal", "Qualidade"]:
            # Configura para layout customizado ou single plot, dependendo da aba
            self._setup_plot_area(single_plot=(aba != "Qualidade"))
            
            if aba == "Análise Geral":
                self.plot_dotplot_geral(df_exame, exame)
            elif aba == "Por Idade":
                self.plot_histograma_idade(df_exame, exame)
            elif aba == "Temporal":
                self.plot_tendencia_temporal(df_exame, exame)
            elif aba == "Qualidade":
                # Redefinir para garantir que o layout customizado da qualidade seja usado
                self._setup_plot_area(single_plot=False)
                self.plot_qualidade_metrics(df_exame, exame)

        elif aba == "Alterados":
             # USO DE PERSONALIZAÇÃO: A aba Alterados usará a segmentação Normal vs. Alterado, conforme solicitada pelo usuário.
             self._setup_plot_area(single_plot=False) # Configura para multi-plot
             self.plot_status_multi_bar(df_exame, exame)
             
        elif aba == "Por Sexo":
             self._setup_plot_area(single_plot=False) # Configura para multi-plot
             self.plot_dotplot_separado_sexo(df_exame, exame)
             
        self.canvas.draw()


    def abrir_manager_vr(self):
        """Abre a janela de gerenciamento de Valores de Referência."""
        if self.df is None:
            self.show_message("Aviso", "Carregue o arquivo CSV primeiro.", type="warning")
            return
            
        VRManager(self, self.exames_disponiveis, self.regras_vr)

    # --- Funções de Plotagem ---
    
    def _limpar_grafico(self, ax, title):
        """Função auxiliar para limpar o eixo e definir o título."""
        ax.clear()
        ax.set_title(title, fontsize=14, fontweight='bold', color='#333333', pad=15)
        
    def plot_status_multi_bar(self, df_exame, exame):
        """
        Plota um gráfico de barras comparando 'NORMAL' vs 'ALTO' e 'BAIXO' ('ALTERADO').
        Exclui 'SEM VR' e 'N/A'.
        """
        df_plot = df_exame.copy()
        
        # Agrupa 'ALTO' e 'BAIXO' em 'ALTERADO'
        df_plot['status_agrupado'] = df_plot['status_vr'].apply(
            lambda x: 'NORMAL' if x == 'NORMAL' else ('ALTERADO' if x in ['ALTO', 'BAIXO'] else None)
        )
        
        df_plot.dropna(subset=['status_agrupado'], inplace=True)
        if df_plot.empty:
            self._setup_plot_area(single_plot=True)
            self._limpar_grafico(self.ax, f"Distribuição de Status VR para {exame}")
            self.ax.text(0.5, 0.5, 'Dados insuficientes ou sem classificação VR para esta análise.', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=12, color='gray')
            return

        status_counts = df_plot['status_agrupado'].value_counts(normalize=True).sort_index() * 100
        
        # Configurar para single plot (um único gráfico de barras)
        self._setup_plot_area(single_plot=True)
        self._limpar_grafico(self.ax, f"Distribuição de Status VR para {exame} (NORMAL vs ALTERADO)")
        
        cores = {'NORMAL': '#28a745', 'ALTERADO': '#dc3545'} 
        status_labels = status_counts.index.tolist()
        status_values = status_counts.values
        bar_colors = [cores.get(s, 'gray') for s in status_labels]

        bars = self.ax.bar(status_labels, status_values, color=bar_colors, width=0.5)
        
        self.ax.set_ylabel("Porcentagem (%)")
        self.ax.set_xlabel("Status de Referência")
        
        # Adiciona rótulos de porcentagem nas barras
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                    f'{height:.1f}%',
                    ha='center', va='bottom')

        self.ax.set_ylim(0, 100)
        self.fig.tight_layout()


    def plot_dotplot_geral(self, df_exame, exame):
        """Plota a distribuição geral dos resultados com VR e destaque de status."""
        self._limpar_grafico(self.ax, f"Distribuição Geral dos Resultados: {exame}")
        
        df_plot = df_exame[df_exame['status_vr'].isin(['NORMAL', 'ALTO', 'BAIXO'])].copy()
        if df_plot.empty:
            self.ax.text(0.5, 0.5, 'Nenhum resultado com VR definido para plotagem.', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=12, color='gray')
            return

        # Cores para cada status
        color_map = {'NORMAL': '#28a745', 'BAIXO': '#dc3545', 'ALTO': '#dc3545'} 
        
        # Adiciona uma pequena dispersão aleatória para visualizar pontos sobrepostos (jitter)
        x_jitter = np.random.normal(0, 0.05, size=len(df_plot)) 

        # Plota os pontos
        scatter = self.ax.scatter(x_jitter, df_plot['resultado'], 
                                  c=[color_map.get(s, 'gray') for s in df_plot['status_vr']], 
                                  alpha=0.6, s=50, edgecolors='none')

        # Desenha a caixa de Valores de Referência se houver
        if self.regras_vr:
            regras_exame = [r for r in self.regras_vr if r['exame'] == exame]
            if regras_exame:
                 # Usa o menor limite inferior e o maior limite superior entre todas as regras
                 ref_min_global = min(r['ref_min'] for r in regras_exame)
                 ref_max_global = max(r['ref_max'] for r in regras_exame)

                 # Linhas de referência
                 self.ax.axhline(ref_min_global, color='#0077b6', linestyle='--', linewidth=1, label='VR Min')
                 self.ax.axhline(ref_max_global, color='#0077b6', linestyle='--', linewidth=1, label='VR Max')

                 # Área de referência (opcional, para visualização clara)
                 # self.ax.axhspan(ref_min_global, ref_max_global, color='blue', alpha=0.1, label='Faixa VR')

        self.ax.set_xticks([]) # Remove o eixo X numérico, mantendo o eixo Y de resultado
        self.ax.set_ylabel("Resultado")
        
        # Cria a legenda manual para os status
        handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='NORMAL', markerfacecolor=color_map['NORMAL'], markersize=10),
            plt.Line2D([0], [0], marker='o', color='w', label='ALTERADO (Alto/Baixo)', markerfacecolor=color_map['ALTO'], markersize=10),
        ]
        
        self.ax.legend(handles=handles, loc='upper right', title="Status VR")
        self.fig.tight_layout()


    def plot_dotplot_separado_sexo(self, df_exame, exame):
        """Plota a distribuição dos resultados separados por sexo."""
        
        # Prepara a figura para 2 subplots (1 linha, 2 colunas)
        self.fig.clear()
        gs = gridspec.GridSpec(1, 2, figure=self.fig)
        ax_m = self.fig.add_subplot(gs[0, 0])
        ax_f = self.fig.add_subplot(gs[0, 1])
        
        self.axes = {'MASCULINO': ax_m, 'FEMININO': ax_f}
        
        df_plot = df_exame[df_exame['status_vr'].isin(['NORMAL', 'ALTO', 'BAIXO'])].copy()
        df_m = df_plot[df_plot['sexo'] == 'MASCULINO']
        df_f = df_plot[df_plot['sexo'] == 'FEMININO']

        # Cores para cada status
        color_map = {'NORMAL': '#28a745', 'BAIXO': '#dc3545', 'ALTO': '#dc3545'}
        
        max_y = df_plot['resultado'].max() * 1.1 if not df_plot.empty else 100
        min_y = df_plot['resultado'].min() * 0.9 if not df_plot.empty else 0

        # Regras de VR aplicáveis
        regras_exame = [r for r in self.regras_vr if r['exame'] == exame]
        
        # Plot Masculino
        self._limpar_grafico(ax_m, f"{exame} - MASCULINO")
        if not df_m.empty:
            x_jitter = np.random.normal(0, 0.05, size=len(df_m)) 
            ax_m.scatter(x_jitter, df_m['resultado'], 
                        c=[color_map.get(s, 'gray') for s in df_m['status_vr']], 
                        alpha=0.6, s=50, edgecolors='none')
        
        # Adiciona linhas de VR para Masculino
        regras_m = [r for r in regras_exame if r['sexo'] in ['MASCULINO', 'AMBOS']]
        if regras_m:
             ref_min_m = min(r['ref_min'] for r in regras_m)
             ref_max_m = max(r['ref_max'] for r in regras_m)
             ax_m.axhline(ref_min_m, color='#0077b6', linestyle='--', linewidth=1)
             ax_m.axhline(ref_max_m, color='#0077b6', linestyle='--', linewidth=1)
        
        ax_m.set_xticks([])
        ax_m.set_ylabel("Resultado")
        ax_m.set_ylim(min_y, max_y)

        # Plot Feminino
        self._limpar_grafico(ax_f, f"{exame} - FEMININO")
        if not df_f.empty:
            x_jitter = np.random.normal(0, 0.05, size=len(df_f)) 
            ax_f.scatter(x_jitter, df_f['resultado'], 
                        c=[color_map.get(s, 'gray') for s in df_f['status_vr']], 
                        alpha=0.6, s=50, edgecolors='none')

        # Adiciona linhas de VR para Feminino
        regras_f = [r for r in regras_exame if r['sexo'] in ['FEMININO', 'AMBOS']]
        if regras_f:
             ref_min_f = min(r['ref_min'] for r in regras_f)
             ref_max_f = max(r['ref_max'] for r in regras_f)
             ax_f.axhline(ref_min_f, color='#0077b6', linestyle='--', linewidth=1)
             ax_f.axhline(ref_max_f, color='#0077b6', linestyle='--', linewidth=1)

        ax_f.set_xticks([])
        ax_f.set_ylabel("Resultado")
        ax_f.set_ylim(min_y, max_y)
        
        # Cria a legenda manual para os status (apenas uma vez)
        handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='NORMAL', markerfacecolor=color_map['NORMAL'], markersize=10),
            plt.Line2D([0], [0], marker='o', color='w', label='ALTERADO (Alto/Baixo)', markerfacecolor=color_map['ALTO'], markersize=10),
            plt.Line2D([0], [0], color='#0077b6', linestyle='--', linewidth=1, label='Faixa VR'),
        ]
        
        # Coloca a legenda fora dos subplots
        self.fig.legend(handles=handles, loc='upper right', bbox_to_anchor=(1.0, 1.0))

        self.fig.tight_layout(rect=[0, 0, 0.9, 1]) # Ajusta para dar espaço à legenda


    def plot_histograma_idade(self, df_exame, exame):
        """Plota o histograma da distribuição de idade com destaque para resultados alterados."""
        self._limpar_grafico(self.ax, f"Distribuição de Idade por Status VR para {exame}")

        df_plot = df_exame[df_exame['status_vr'].isin(['NORMAL', 'ALTO', 'BAIXO'])].copy()
        
        if df_plot.empty:
            self.ax.text(0.5, 0.5, 'Nenhum resultado com VR definido para plotagem.', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=12, color='gray')
            return

        # Agrupa 'ALTO' e 'BAIXO' em 'ALTERADO' para a legenda
        df_plot['status_plot'] = df_plot['status_vr'].apply(
            lambda x: 'NORMAL' if x == 'NORMAL' else 'ALTERADO'
        )
        
        ages_normal = df_plot[df_plot['status_plot'] == 'NORMAL']['idade'].dropna().values
        ages_alterado = df_plot[df_plot['status_plot'] == 'ALTERADO']['idade'].dropna().values
        
        # Define os bins
        max_age = int(df_plot['idade'].max()) if not df_plot['idade'].empty else 1
        bins = np.arange(0, max_age + 5, 5) if max_age > 10 else 5

        # Plota os histogramas (um empilhado sobre o outro)
        self.ax.hist([ages_normal, ages_alterado], bins=bins, stacked=True, 
                     color=['#28a745', '#dc3545'], 
                     label=['NORMAL', 'ALTERADO'], edgecolor='black')

        self.ax.set_xlabel("Idade (anos)")
        self.ax.set_ylabel("Frequência")
        self.ax.legend(title="Status VR")
        self.fig.tight_layout()


    def plot_tendencia_temporal(self, df_exame, exame):
        """Plota a tendência temporal dos resultados com uma média móvel."""
        self._limpar_grafico(self.ax, f"Tendência Temporal dos Resultados: {exame}")

        df_plot = df_exame.copy()
        df_plot.dropna(subset=['data', 'resultado'], inplace=True)

        if df_plot.empty:
            self.ax.text(0.5, 0.5, 'Nenhum dado temporal disponível para plotagem.', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=12, color='gray')
            return
            
        df_plot.sort_values('data', inplace=True)

        # Plota resultados individuais
        self.ax.plot(df_plot['data'], df_plot['resultado'], 
                     marker='o', linestyle='', alpha=0.4, label='Resultados Individuais', color='#0077b6')

        # Calcula e plota a média móvel (rolling mean) - janela de 30 dias
        df_plot['data_dt'] = pd.to_datetime(df_plot['data'])
        df_plot.set_index('data_dt', inplace=True)
        
        # Calcula a média móvel da 'resultado' usando uma janela de 30 dias
        rolling_mean = df_plot['resultado'].rolling(window='30D').mean()
        
        self.ax.plot(rolling_mean.index.to_numpy(), rolling_mean.values, 
                     linestyle='-', color='#dc3545', linewidth=2, label='Média Móvel (30 dias)')

        # Configuração do eixo X (Datas)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.fig.autofmt_xdate()

        self.ax.set_xlabel("Data")
        self.ax.set_ylabel("Resultado")
        self.ax.legend(loc='upper left')
        self.fig.tight_layout()


    def plot_qualidade_metrics(self, df_exame, exame):
        """
        Plota métricas de qualidade em um layout de 2x2:
        1. Histograma de Frequência (VR Status)
        2. Tabela de Estatísticas Descritivas
        3. Histograma de Frequência (Sexo)
        """
        
        # Prepara a figura para 2 subplots (2 linhas, 2 colunas)
        self.fig.clear()
        gs = gridspec.GridSpec(2, 2, figure=self.fig, hspace=0.4, wspace=0.3)
        ax_status = self.fig.add_subplot(gs[0, 0])
        ax_stats = self.fig.add_subplot(gs[0, 1])
        ax_sexo = self.fig.add_subplot(gs[1, 0])
        ax_empty = self.fig.add_subplot(gs[1, 1])
        
        self.axes = {'status': ax_status, 'stats': ax_stats, 'sexo': ax_sexo, 'empty': ax_empty}
        
        # 1. Histograma de Frequência (VR Status)
        self._limpar_grafico(ax_status, "Distribuição de Status VR")
        status_counts = df_exame['status_vr'].value_counts()
        
        status_colors = {'NORMAL': '#28a745', 'BAIXO': '#dc3545', 'ALTO': '#dc3545', 'SEM VR': 'lightgray', 'N/A': 'darkgray'}
        bar_colors = [status_colors.get(s, 'gray') for s in status_counts.index]
        
        ax_status.bar(status_counts.index, status_counts.values, color=bar_colors)
        ax_status.set_ylabel("Frequência")
        ax_status.tick_params(axis='x', rotation=30)
        
        
        # 2. Tabela de Estatísticas Descritivas
        self._limpar_grafico(ax_stats, "Estatísticas Descritivas")
        ax_stats.axis('off')
        
        df_desc = df_exame['resultado'].describe().reset_index()
        df_desc.columns = ['Métrica', 'Valor']
        
        # Adiciona Coeficiente de Variação (CV)
        if df_desc.loc[df_desc['Métrica'] == 'mean', 'Valor'].iloc[0] != 0:
            cv = (df_desc.loc[df_desc['Métrica'] == 'std', 'Valor'].iloc[0] / df_desc.loc[df_desc['Métrica'] == 'mean', 'Valor'].iloc[0]) * 100
            cv_row = pd.DataFrame([['cv', cv]], columns=['Métrica', 'Valor'])
            df_table = pd.concat([df_desc, cv_row], ignore_index=True)
        else:
            df_table = df_desc
        
        df_table.rename(columns={'Métrica': 'Estatística'}, inplace=True)
        
        # Mapeamento para nomes em português
        pt_names = {
            'count': 'N Amostras', 'mean': 'Média (x̄)', 'std': 'Desvio Padrão', 
            'min': 'Mínimo', '25%': 'Q1', '50%': 'Mediana (Q2)', '75%': 'Q3', 'max': 'Máximo', 'cv': 'CV (%)'
        }
        df_table['Estatística'] = df_table['Estatística'].replace(pt_names)
        df_table['Valor'] = df_table['Valor'].apply(lambda x: f"{x:.2f}")

        # Desenha a tabela usando o Matplotlib Table
        table = ax_stats.table(cellText=df_table.values, 
                               colLabels=df_table.columns, 
                               loc='center', 
                               cellLoc='center',
                               colColours=["#0077b6", "#0077b6"], 
                               colWidths=[0.4, 0.4])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)
        
        # Estilo dos cabeçalhos
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#0077b6')
            cell.set_edgecolor('lightgray')
        
        # 3. Histograma de Frequência (Sexo)
        self._limpar_grafico(ax_sexo, "Distribuição de Sexo")
        sex_counts = df_exame['sexo'].value_counts()
        sex_colors = {'MASCULINO': '#17a2b8', 'FEMININO': '#e83e8c'} 
        bar_colors_sex = [sex_colors.get(s, 'gray') for s in sex_counts.index]
        
        ax_sexo.bar(sex_counts.index, sex_counts.values, color=bar_colors_sex)
        ax_sexo.set_ylabel("Frequência")
        ax_sexo.tick_params(axis='x', rotation=30)
        
        # 4. Eixo Vazio (Texto informativo)
        self._limpar_grafico(ax_empty, "Informação")
        ax_empty.axis('off')
        ax_empty.text(0.5, 0.7, f'Exame: {exame}', ha='center', va='center', fontsize=12, color='#333333')
        ax_empty.text(0.5, 0.4, 'O Coeficiente de Variação (CV)\nindica a precisão do resultado.', ha='center', va='center', fontsize=10, color='gray')
        
        self.fig.tight_layout()