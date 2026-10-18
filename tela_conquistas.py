import tkinter as tk

import persistencia
import recursos
import tema

# clima "laboratório holográfico" (tema.LAB)
COR_FUNDO = tema.LAB["fundo"]
COR_DESBLOQUEADA = tema.LAB["painel_claro"]
COR_BLOQUEADA = tema.LAB["painel"]
COR_TEXTO = tema.LAB["texto"]
COR_TEXTO_SUAVE = tema.LAB["texto_suave"]


class TelaConquistas(tk.Frame):
    def __init__(self, master, controlador):
        super().__init__(master, bg=COR_FUNDO)
        self.controlador = controlador
        recursos.aplicar_fundo_frame(self, "conquistas")

        tk.Label(self, text="🏅 Conquistas", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 14, "bold")).pack(pady=(12, 4))

        self.rotulo_progresso = tk.Label(self, text="", fg=COR_TEXTO_SUAVE, bg=COR_FUNDO,
                                          font=("Segoe UI", 10))
        self.rotulo_progresso.pack(pady=(0, 6))

        # filtro: mostra todas, só as feitas ou só as que faltam
        self.filtro = "Todas"
        barra_filtro = tk.Frame(self, bg=COR_FUNDO)
        barra_filtro.pack(pady=(0, 4))
        self.botoes_filtro = {}
        for nome in ("Todas", "Feitas", "Faltando"):
            botao = tk.Button(barra_filtro, text=nome, relief="flat", padx=14, takefocus=0,
                              command=lambda n=nome: self._escolher_filtro(n))
            botao.pack(side="left", padx=3)
            self.botoes_filtro[nome] = botao

        # padx grande: a lista fica no meio e o painel de troféus do fundo aparece dos lados
        area_lista = tk.Frame(self, bg=tema.LAB["borda"], padx=2, pady=2)
        area_lista.pack(fill="both", expand=True, padx=110, pady=(6, 24))

        barra_rolagem = tk.Scrollbar(area_lista)
        barra_rolagem.pack(side="right", fill="y")

        self.canvas = tk.Canvas(area_lista, bg=COR_FUNDO, highlightthickness=0,
                                 yscrollcommand=barra_rolagem.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra_rolagem.config(command=self.canvas.yview)

        self.frame_interno = tk.Frame(self.canvas, bg=COR_FUNDO)
        janela_lista = self.canvas.create_window((0, 0), window=self.frame_interno, anchor="nw")
        # a lista acompanha a largura do painel (senão as linhas ficam estreitas)
        self.canvas.bind("<Configure>", lambda evento: self.canvas.itemconfigure(janela_lista, width=evento.width))
        self.frame_interno.bind(
            "<Configure>", lambda evento: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind_all("<MouseWheel>", self._rolar, add="+")

        self._carregar_conquistas()

    def _rolar(self, evento):
        if getattr(self.controlador, "tela_visivel", None) is self:
            self.canvas.yview_scroll(-1 if evento.delta > 0 else 1, "units")

    def _escolher_filtro(self, nome):
        self.filtro = nome
        self._carregar_conquistas()
        self.canvas.yview_moveto(0)

    def _carregar_conquistas(self):
        for widget in self.frame_interno.winfo_children():
            widget.destroy()
        for nome, botao in self.botoes_filtro.items():
            ativo = nome == self.filtro
            botao.config(bg=tema.LAB["destaque"] if ativo else tema.LAB["painel_claro"], fg="white")

        conquistas = persistencia.listar_conquistas()
        total = len(conquistas)
        desbloqueadas = sum(1 for c in conquistas if c["desbloqueada"])
        self.rotulo_progresso.config(text=f"Desbloqueadas: {desbloqueadas} / {total}  •  faltam {total - desbloqueadas}")
        if self.filtro == "Feitas":
            conquistas = [c for c in conquistas if c["desbloqueada"]]
        elif self.filtro == "Faltando":
            conquistas = [c for c in conquistas if not c["desbloqueada"]]
        if not conquistas:
            tk.Label(self.frame_interno, text="Nada por aqui.", fg=COR_TEXTO_SUAVE, bg=COR_FUNDO,
                     font=("Segoe UI", 10, "italic")).pack(pady=20)

        categoria_atual = None
        for conquista in conquistas:
            if conquista["categoria"] != categoria_atual:
                categoria_atual = conquista["categoria"]
                tk.Label(self.frame_interno, text=categoria_atual, fg=tema.LAB["destaque_claro"], bg=COR_FUNDO,
                         font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))

            cor = COR_DESBLOQUEADA if conquista["desbloqueada"] else COR_BLOQUEADA
            linha = tk.Frame(self.frame_interno, bg=cor)
            linha.pack(fill="x", pady=2)

            icone = "✅" if conquista["desbloqueada"] else "🔒"
            nome = conquista["nome"] if conquista["desbloqueada"] else "???"
            descricao = (conquista["descricao"] if conquista["desbloqueada"]
                         else f"Conquista ainda não descoberta • categoria: {conquista['categoria']}")

            tk.Label(linha, text=icone, bg=cor, font=("Segoe UI", 11)).pack(side="left", padx=8, pady=6)
            texto_frame = tk.Frame(linha, bg=cor)
            texto_frame.pack(side="left", fill="x", expand=True, pady=6)
            tk.Label(texto_frame, text=nome, bg=cor, fg=COR_TEXTO, font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(texto_frame, text=descricao, bg=cor, fg=COR_TEXTO_SUAVE, font=("Segoe UI", 8),
                     anchor="w", wraplength=560).pack(fill="x")

    def atualizar_ao_exibir(self):
        self._carregar_conquistas()