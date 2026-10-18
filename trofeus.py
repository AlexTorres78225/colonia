import time
import tkinter as tk

import bau_dados
import persistencia
import recursos
import tema

COR_FUNDO = tema.TROFEUS["fundo"]
COR_PAINEL = tema.TROFEUS["painel"]
COR_TEXTO = tema.TROFEUS["texto"]
COR_TEXTO_SUAVE = tema.TROFEUS["texto_suave"]
COR_BLOQUEADO = tema.TROFEUS["bloqueado"]


class TelaTrofeus(tk.Frame):
    """🏆 Área de Troféus: cada vez que a colônia chega ao último estágio, um troféu e um ciclo novo."""

    def __init__(self, master, controlador):
        super().__init__(master, bg=COR_FUNDO)
        self.controlador = controlador
        recursos.aplicar_fundo_frame(self, "trofeus")

        tk.Label(self, text="🏆 Área de Troféus", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 15, "bold")).pack(pady=(14, 2))
        self.rotulo_ciclo = tk.Label(self, text="", fg=COR_TEXTO_SUAVE, bg=COR_FUNDO, font=("Segoe UI", 10))
        self.rotulo_ciclo.pack()

        self.canvas = tk.Canvas(self, width=900, height=250, bg=COR_FUNDO, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.lista = tk.Frame(self, bg=COR_PAINEL, padx=18, pady=12)
        self.lista.pack(padx=40, pady=(0, 20))
        self._montar()

    def _medalha(self, x, y, dados, conquistado, quando):
        raio = 62
        cor = dados["cor"] if conquistado else COR_BLOQUEADO
        self.canvas.create_oval(x - raio - 6, y - raio - 6, x + raio + 6, y + raio + 6, fill=COR_PAINEL,
                                outline=cor, width=3)
        self.canvas.create_oval(x - raio, y - raio, x + raio, y + raio, fill=cor, outline="")
        self.canvas.create_oval(x - raio + 14, y - raio + 14, x + raio - 14, y + raio - 14,
                                outline=COR_FUNDO if conquistado else "#4a4436", width=3)
        self.canvas.create_text(x, y, text="🏆" if conquistado else "🔒", font=("Segoe UI", 30),
                                fill=COR_FUNDO if conquistado else "#6a6252")
        self.canvas.create_text(x, y + raio + 22, text=dados["nome"], fill=COR_TEXTO if conquistado else "#7a7060",
                                font=("Segoe UI", 12, "bold"))
        legenda = time.strftime("%d/%m/%Y", time.localtime(quando)) if conquistado and quando else (
            "conquistado" if conquistado else "bloqueado")
        self.canvas.create_text(x, y + raio + 42, text=legenda, fill=COR_TEXTO_SUAVE, font=("Segoe UI", 8))

    def _montar(self):
        total = bau_dados.trofeus()
        if total >= bau_dados.TOTAL_TROFEUS:
            self.rotulo_ciclo.config(text="👑 MESTRE DA COLÔNIA — todos os troféus conquistados! A colônia segue livre.")
        else:
            proximo = bau_dados.TROFEUS[total]
            self.rotulo_ciclo.config(text=f"Ciclo {total + 1} de {bau_dados.TOTAL_TROFEUS}  •  Leve a colônia até a "
                                          f"Forma de Vida Suprema para ganhar o troféu de {proximo['nome']}.")

        self.canvas.delete("all")
        for indice, dados in enumerate(bau_dados.TROFEUS):
            quando = persistencia.obter_estatistica(f"trofeu_{indice + 1}_quando")
            self._medalha(100 + indice * 175, 95, dados, indice < total, quando)

        for widget in self.lista.winfo_children():
            widget.destroy()
        tk.Label(self.lista, text="O que cada troféu libera para o ciclo seguinte:", fg=COR_TEXTO, bg=COR_PAINEL,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        for indice, dados in enumerate(bau_dados.TROFEUS):
            feito = indice < total
            tk.Label(self.lista, text=f"{'✅' if feito else '🔒'}  {dados['emoji']} {dados['nome']}:  {dados['libera']}",
                     fg=COR_TEXTO if feito else COR_TEXTO_SUAVE, bg=COR_PAINEL,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=1)
        tk.Label(self.lista, text=f"A cada troféu o jogo reinicia num ciclo novo, com cores novas: a colônia e a "
                                  f"Geladeira recomeçam.\nVocê leva: upgrades do Baú, frascos, conquistas, troféus, o "
                                  f"Manual e {bau_dados.MEMBRANA_INICIAL} ⬡ + "
                                  f"{round(bau_dados.PARTE_DA_MEMBRANA_QUE_FICA * 100)}% da Membrana que sobrou.\n"
                                  "A reprodução fica um pouco mais difícil a cada ciclo.",
                 fg=COR_TEXTO_SUAVE, bg=COR_PAINEL, font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=(8, 0))

    def atualizar_ao_exibir(self):
        self._montar()
