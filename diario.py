import os
import re
import tkinter as tk
from datetime import datetime

import janelas
import persistencia
import recursos
import tema

# clima "mesa do cientista": a lista vira uma folha de papel em cima da mesa (tema.MESA)
COR_FUNDO = tema.MESA["fundo"]
COR_PAPEL = tema.MESA["papel"]
COR_TINTA = tema.MESA["tinta"]
PASTA_DOS_ARQUIVOS = "diarios"   # os diários arquivados viram .txt nesta pasta, dentro do projeto
LIMITE_NA_TELA = 500             # a tela mostra só as anotações mais recentes (o resto continua salvo)


class TelaDiario(tk.Frame):
    def __init__(self, master, controlador):
        super().__init__(master, bg=COR_FUNDO)
        self.controlador = controlador
        recursos.aplicar_fundo_frame(self, "diario")

        tk.Label(self, text="📔 Diário de Anotações", fg=tema.MESA["texto"], bg=COR_FUNDO,
                 font=("Segoe UI", 14, "bold")).pack(pady=(12, 4))
        self.rotulo_total = tk.Label(self, text="", fg=tema.MESA["texto_suave"], bg=COR_FUNDO, font=("Segoe UI", 9))
        self.rotulo_total.pack(pady=(0, 6))

        botoes = tk.Frame(self, bg=COR_FUNDO)
        botoes.pack(side="bottom", pady=(0, 16))
        tk.Button(botoes, text="📦 Arquivar tudo (.txt)", command=self._arquivar, bg=tema.MESA["destaque"],
                  fg=tema.MESA["tinta"], relief="flat", padx=14, pady=4).pack(side="left", padx=6)
        tk.Button(botoes, text="🗑️ Limpar tudo", command=self._limpar, bg=tema.MESA["painel_claro"],
                  fg=tema.MESA["texto"], relief="flat", padx=14, pady=4).pack(side="left", padx=6)

        # padx grande: a folha fica no meio e a mesa do fundo aparece dos lados
        area = tk.Frame(self, bg=tema.MESA["painel"], padx=3, pady=3)
        area.pack(fill="both", expand=True, padx=150, pady=(4, 10))

        barra_rolagem = tk.Scrollbar(area)
        barra_rolagem.pack(side="right", fill="y")

        self.caixa_texto = tk.Text(area, bg=COR_PAPEL, fg=COR_TINTA, wrap="word",
                                    yscrollcommand=barra_rolagem.set, font=("Georgia", 10),
                                    padx=18, pady=14, relief="flat", state="disabled")
        self.caixa_texto.pack(side="left", fill="both", expand=True)
        self.caixa_texto.tag_configure("data", foreground="#7a4e2c", font=("Georgia", 9, "italic"))
        barra_rolagem.config(command=self.caixa_texto.yview)

        self._carregar_entradas()

    def _carregar_entradas(self):
        entradas = persistencia.listar_diario()
        self.rotulo_total.config(text=f"Registro de descobertas, fusões e anomalias — {len(entradas)} anotação(ões)")
        self.caixa_texto.config(state="normal")
        self.caixa_texto.delete("1.0", tk.END)
        if not entradas:
            self.caixa_texto.insert(tk.END, "Nenhuma anotação registrada ainda. "
                                              "Interações na colônia e fusões manuais geram entradas aqui.")
        for entrada in entradas[:LIMITE_NA_TELA]:
            data_curta = entrada["data"][:16].replace("T", " ")
            self.caixa_texto.insert(tk.END, f"[{data_curta}] ", "data")
            self.caixa_texto.insert(tk.END, f"{entrada['texto']}\n\n")
        if len(entradas) > LIMITE_NA_TELA:
            self.caixa_texto.insert(tk.END, f"… e mais {len(entradas) - LIMITE_NA_TELA} anotações antigas. "
                                            "Use “Arquivar tudo” para guardar num .txt.")
        self.caixa_texto.config(state="disabled")

    def _arquivar(self):
        entradas = persistencia.listar_diario()
        if not entradas:
            janelas.showinfo("Diário", "O diário já está vazio.")
            return
        pasta = os.path.join(persistencia.pasta_do_projeto(), PASTA_DOS_ARQUIVOS)
        os.makedirs(pasta, exist_ok=True)
        conta = re.sub(r"[^\w-]", "_", getattr(self.controlador, "usuario_atual", "conta"))
        caminho = os.path.join(pasta, f"diario_{conta}_{datetime.now():%Y-%m-%d_%H%M%S}.txt")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(f"Diário de Anotações — Colônia — conta {conta}\n")
            arquivo.write(f"Arquivado em {datetime.now():%d/%m/%Y %H:%M} • {len(entradas)} anotações\n\n")
            for entrada in reversed(entradas):   # do mais antigo para o mais novo
                arquivo.write(f"[{entrada['data'][:16].replace('T', ' ')}] {entrada['texto']}\n")
        persistencia.limpar_diario()
        self._carregar_entradas()
        janelas.showinfo("Diário arquivado", f"{len(entradas)} anotações salvas em:\n{caminho}\n\nO diário foi limpo.")

    def _limpar(self):
        if janelas.askyesno("Limpar diário", "Apagar TODAS as anotações do diário?\n"
                                             "(Para guardar uma cópia antes, use “Arquivar tudo”.)"):
            persistencia.limpar_diario()
            self._carregar_entradas()

    def atualizar_ao_exibir(self):
        self._carregar_entradas()
