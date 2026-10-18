import tkinter as tk

import bau_dados
import recursos
import sons
import tema

# clima "laboratório holográfico" (tema.LAB) — o fundo bau.png entra quando estiver pronto
COR_FUNDO = tema.LAB["fundo"]
COR_CARTAO = tema.LAB["painel"]
COR_CARTAO_MAXIMO = "#123d34"
COR_CARTAO_TRANCADO = "#141c26"
COR_TEXTO = tema.LAB["texto"]
COR_TEXTO_SUAVE = tema.LAB["texto_suave"]
COR_DESTAQUE = tema.LAB["destaque"]
COR_AVISO = tema.LAB["aviso"]
COLUNAS_UPGRADES = 5
COLUNAS_FRASCOS = 6


class TelaBau(tk.Frame):
    """📦 Baú do cientista: gaste Membrana em upgrades permanentes e frascos."""

    def __init__(self, master, controlador):
        super().__init__(master, bg=COR_FUNDO)
        self.controlador = controlador
        recursos.aplicar_fundo_frame(self, "bau")

        topo = tk.Frame(self, bg=COR_FUNDO)
        topo.pack(fill="x", padx=20, pady=(12, 2))
        tk.Label(topo, text="📦 Baú do Cientista", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        self.rotulo_saldo = tk.Label(topo, text="", fg=COR_AVISO, bg=COR_FUNDO, font=("Segoe UI", 15, "bold"))
        self.rotulo_saldo.pack(side="right")

        tk.Label(self, text="Ganhe Membrana unindo organismos iguais (+3), descobrindo espécies e completando "
                            "conquistas. Upgrades são permanentes; frascos são de uso único (herói ou vilão). "
                            "🔒 = liberado por um troféu.",
                 fg=COR_TEXTO_SUAVE, bg=COR_FUNDO, font=("Segoe UI", 9)).pack(padx=20, anchor="w")

        self.rotulo_status = tk.Label(self, text="", fg=COR_AVISO, bg=COR_FUNDO, font=("Segoe UI", 10, "italic"))
        self.rotulo_status.pack(pady=(4, 0))

        # área com rolagem (são muitos cartões)
        moldura = tk.Frame(self, bg=COR_FUNDO)
        moldura.pack(fill="both", expand=True, padx=10, pady=4)
        barra = tk.Scrollbar(moldura)
        barra.pack(side="right", fill="y")
        self.canvas = tk.Canvas(moldura, bg=COR_FUNDO, highlightthickness=0, yscrollcommand=barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra.config(command=self.canvas.yview)
        self.area = tk.Frame(self.canvas, bg=COR_FUNDO)
        self._janela_area = self.canvas.create_window((10, 0), window=self.area, anchor="nw")
        self.area.bind("<Configure>", lambda evento: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._rolar, add="+")
        self._montar()

    def _rolar(self, evento):
        if getattr(self.controlador, "tela_visivel", None) is self:
            self.canvas.yview_scroll(-1 if evento.delta > 0 else 1, "units")

    # ---------- montagem ----------

    def _titulo_secao(self, texto, linha):
        tk.Label(self.area, text=texto, fg=tema.LAB["destaque_claro"], bg=COR_FUNDO,
                 font=("Segoe UI", 12, "bold")).grid(row=linha, column=0, columnspan=COLUNAS_FRASCOS,
                                                     sticky="w", pady=(6, 2))

    def _montar(self):
        for widget in self.area.winfo_children():
            widget.destroy()
        saldo = bau_dados.saldo()
        self.rotulo_saldo.config(text=f"⬡ {saldo} Membrana")

        self._titulo_secao("🟦 Upgrades permanentes (até 3 níveis)", 0)
        upgrades = tk.Frame(self.area, bg=COR_FUNDO)
        upgrades.grid(row=1, column=0, sticky="w")
        for indice, dados in enumerate(bau_dados.UPGRADES):
            self._cartao_upgrade(upgrades, dados, saldo).grid(row=indice // COLUNAS_UPGRADES,
                                                               column=indice % COLUNAS_UPGRADES, padx=4, pady=4)

        self._titulo_secao("🧪 Frascos (uso único — escolha na barra embaixo da placa e clique no mapa)", 2)
        frascos = tk.Frame(self.area, bg=COR_FUNDO)
        frascos.grid(row=3, column=0, sticky="w")
        for indice, dados in enumerate(bau_dados.FRASCOS):
            self._cartao_frasco(frascos, dados, saldo).grid(row=indice // COLUNAS_FRASCOS,
                                                             column=indice % COLUNAS_FRASCOS, padx=4, pady=4)

    def _cartao_trancado(self, pai, dados, largura, altura):
        cartao = tk.Frame(pai, bg=COR_CARTAO_TRANCADO, width=largura, height=altura,
                          highlightthickness=1, highlightbackground="#2a3644")
        cartao.pack_propagate(False)
        tk.Label(cartao, text=f"{dados['emoji']} {dados['nome'].replace('Frasco ', '')}", fg="#6f8496",
                 bg=COR_CARTAO_TRANCADO, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
        tk.Label(cartao, text=dados["descricao"], fg="#5a6b7a", bg=COR_CARTAO_TRANCADO, font=("Segoe UI", 8),
                 wraplength=largura - 18, justify="left").pack(anchor="w", padx=8, pady=(4, 0))
        tk.Label(cartao, text=bau_dados.texto_bloqueio(dados), fg="#c9a24c", bg=COR_CARTAO_TRANCADO,
                 font=("Segoe UI", 8, "bold"), wraplength=largura - 18).pack(side="bottom", pady=8)
        return cartao

    def _cartao_upgrade(self, pai, dados, saldo):
        if not bau_dados.liberado(dados):
            return self._cartao_trancado(pai, dados, 178, 154)
        nivel = bau_dados.nivel(dados["chave"])
        maximo = nivel >= bau_dados.NIVEL_MAXIMO
        cor = COR_CARTAO_MAXIMO if maximo else COR_CARTAO
        cartao = tk.Frame(pai, bg=cor, width=178, height=154,
                          highlightthickness=1, highlightbackground=tema.LAB["borda"])
        cartao.pack_propagate(False)

        tk.Label(cartao, text=f"{dados['emoji']} {dados['nome']}", fg=COR_TEXTO, bg=cor,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
        bolinhas = "●" * nivel + "○" * (bau_dados.NIVEL_MAXIMO - nivel)
        tk.Label(cartao, text=f"Nível {bolinhas}", fg=COR_AVISO, bg=cor,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=8)
        tk.Label(cartao, text=dados["descricao"], fg=COR_TEXTO_SUAVE, bg=cor, font=("Segoe UI", 8),
                 wraplength=160, justify="left").pack(anchor="w", padx=8, pady=(2, 0))

        agora = bau_dados.texto_do_nivel(dados["chave"], nivel)
        if maximo:
            efeito = f"Agora: {agora}"
        else:
            efeito = f"Agora: {agora}\nPróximo: {bau_dados.texto_do_nivel(dados['chave'], nivel + 1)}"
        tk.Label(cartao, text=efeito, fg=COR_TEXTO, bg=cor, font=("Segoe UI", 8),
                 justify="left").pack(anchor="w", padx=8, pady=(2, 0))

        if maximo:
            tk.Label(cartao, text="✅ Máximo", fg="#7fe0b0", bg=cor,
                     font=("Segoe UI", 9, "bold")).pack(side="bottom", pady=6)
        else:
            preco = bau_dados.preco_do_proximo_nivel(dados["chave"])
            pode = saldo >= preco
            tk.Button(cartao, text=f"Comprar · {preco} ⬡", relief="flat", takefocus=0,
                      bg=COR_DESTAQUE if pode else tema.LAB["painel_claro"], fg="white" if pode else "#7f9fb5",
                      command=lambda chave=dados["chave"]: self._comprar_upgrade(chave)).pack(
                side="bottom", fill="x", padx=8, pady=6)
        return cartao

    def _cartao_frasco(self, pai, dados, saldo):
        if not bau_dados.liberado(dados):
            return self._cartao_trancado(pai, dados, 146, 156)
        cartao = tk.Frame(pai, bg=COR_CARTAO, width=146, height=156,
                          highlightthickness=1, highlightbackground=bau_dados.COR_DO_LADO[dados["lado"]])
        cartao.pack_propagate(False)
        tk.Label(cartao, text=f"{dados['emoji']} {dados['nome'].replace('Frasco ', '')}", fg=COR_TEXTO,
                 bg=COR_CARTAO, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
        tk.Label(cartao, text=dados["lado"].upper(), fg=bau_dados.COR_DO_LADO[dados["lado"]], bg=COR_CARTAO,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=8)
        tk.Label(cartao, text=dados["descricao"], fg=COR_TEXTO_SUAVE, bg=COR_CARTAO, font=("Segoe UI", 8),
                 wraplength=130, justify="left").pack(anchor="w", padx=8, pady=(2, 0))
        tk.Label(cartao, text=f"Você tem: {bau_dados.quantidade(dados['chave'])}", fg=COR_TEXTO, bg=COR_CARTAO,
                 font=("Segoe UI", 8, "bold")).pack(side="bottom", anchor="w", padx=8)
        preco = bau_dados.preco_frasco(dados["chave"])
        pode = saldo >= preco
        tk.Button(cartao, text=f"Comprar · {preco} ⬡", relief="flat", takefocus=0,
                  bg=COR_DESTAQUE if pode else tema.LAB["painel_claro"], fg="white" if pode else "#7f9fb5",
                  command=lambda chave=dados["chave"]: self._comprar_frasco(chave)).pack(
            side="bottom", fill="x", padx=8, pady=(4, 2))
        return cartao

    # ---------- compras ----------

    def _comprar_upgrade(self, chave):
        ok, mensagem = bau_dados.comprar_upgrade(chave)
        self._depois_da_compra(ok, mensagem)

    def _comprar_frasco(self, chave):
        ok, mensagem = bau_dados.comprar_frasco(chave)
        self._depois_da_compra(ok, mensagem)

    def _depois_da_compra(self, ok, mensagem):
        self.rotulo_status.config(text=("✅ " if ok else "❌ ") + mensagem,
                                  fg="#7fe0b0" if ok else "#ff8a8a")
        if ok:
            sons.tocar(sons.SOM_CONQUISTA)
        self._montar()

    def atualizar_ao_exibir(self):
        self.rotulo_status.config(text="")
        self._montar()
