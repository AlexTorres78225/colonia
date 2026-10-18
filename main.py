import importlib
import sys
import time
import tkinter as tk
import janelas

import persistencia
import recursos
import sons
import tema
import bau_dados
from conquistas import avaliar_e_desbloquear

VERSAO = "1.1"

# (nome, ícone, módulo, classe) — as classes são buscadas na hora (ver _preparar_visual)
TELAS = [
    ("Simulação", "🔬", "simulacao", "TelaSimulacao"),
    ("Área de Fusão", "⚗️", "fusao", "TelaFusao"),
    ("Área de Mutação", "🧬", "mutacao", "TelaMutacao"),
    ("Baú", "📦", "bau", "TelaBau"),
    ("Geladeira", "🧊", "geladeira", "TelaGeladeira"),
    ("Manual", "📖", "manual", "TelaManual"),
    ("Diário", "📔", "diario", "TelaDiario"),
    ("Conquistas", "🏅", "tela_conquistas", "TelaConquistas"),
    ("Troféus", "🏆", "trofeus", "TelaTrofeus"),
]
# módulos que guardam cores do tema quando são carregados, na ordem certa (placa antes das telas que a usam)
MODULOS_VISUAIS = ["janelas", "placa", "simulacao", "fusao", "mutacao", "bau", "geladeira", "manual", "diario",
                   "tela_conquistas", "trofeus", "tela_login"]


def _preparar_visual(ciclo):
    """Pinta o jogo com as cores do ciclo.

    Várias telas copiam as cores do tema quando o arquivo é carregado (COR_FUNDO = tema.LAB[...]).
    Por isso, depois de trocar as cores, esses arquivos são recarregados (importlib.reload).
    """
    tema.aplicar_ciclo(ciclo)
    for nome in MODULOS_VISUAIS:
        if nome in sys.modules:
            importlib.reload(sys.modules[nome])
        else:
            importlib.import_module(nome)
    recursos.limpar_cache()


def _ciclo_do_visual():
    """Ciclos 1 a 5 seguem os troféus; com os 5 troféus, o visual de Mestre (6)."""
    return bau_dados.trofeus() + 1


class App(tk.Tk):
    def __init__(self, usuario_atual="Cientista", ciclo_novo=False):
        super().__init__()
        recursos.limpar_cache()
        self.usuario_atual = usuario_atual
        self.voltar_ao_login = False
        self.reiniciar = False           # True depois de um troféu: o jogo reabre com as cores novas
        self._trofeu_agendado = False
        self.title(f"Colônia v{VERSAO} — Projeto 018 — {usuario_atual}")
        self.geometry("1180x700")
        self.minsize(1180, 700)          # menor que isso, os botões não cabem
        self.configure(bg=tema.LAB["fundo"])
        self.state("zoomed")             # abre maximizado (ocupa a tela, com a barra do Windows)
        self.bind("<F11>", self._alternar_tela_cheia)
        self.bind("<Escape>", lambda evento: self.attributes("-fullscreen", False))

        self.container = tk.Frame(self, bg=tema.LAB["fundo"])
        self.container.pack(side="right", fill="both", expand=True)

        self.barra_lateral = tk.Frame(self, bg=tema.LAB["painel"], width=200)
        self.barra_lateral.pack(side="left", fill="y")
        self.barra_lateral.pack_propagate(False)

        self.telas = {}
        self.botoes = {}
        self._montar_barra_lateral()
        self._criar_telas()
        self.mostrar_tela("Simulação")
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        if ciclo_novo:
            self.telas["Simulação"].comecar_ciclo_novo()

    def _alternar_tela_cheia(self, evento=None):
        """F11: tela cheia de verdade (some até a barra do Windows). Esc ou F11 de novo para sair."""
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _montar_barra_lateral(self):
        tk.Label(self.barra_lateral, text="🦠 Colônia", fg=tema.LAB["texto"], bg=tema.LAB["painel"],
                 font=("Segoe UI", 13, "bold")).pack(pady=(18, 2))
        self.rotulo_jogador = tk.Label(self.barra_lateral, text="", fg=tema.LAB["texto_suave"],
                                       bg=tema.LAB["painel"], font=("Segoe UI", 9), justify="center")
        self.rotulo_jogador.pack(pady=(0, 12))

        for nome, icone, _modulo, _classe in TELAS:
            botao = tk.Button(
                self.barra_lateral, text=f"{icone}  {nome}", anchor="w",
                bg=tema.LAB["fundo"], fg=tema.LAB["texto"], activebackground=tema.LAB["painel_claro"],
                relief="flat", font=("Segoe UI", 10),
                padx=14, pady=8, takefocus=0, command=lambda n=nome: self.mostrar_tela(n),
            )
            botao.pack(fill="x", padx=10, pady=2)
            self.botoes[nome] = botao

        tk.Label(self.barra_lateral, text=f"v{VERSAO}", fg=tema.LAB["texto_suave"], bg=tema.LAB["painel"],
                 font=("Segoe UI", 8)).pack(side="bottom", pady=(0, 6))
        tk.Button(
            self.barra_lateral, text="🚪  Sair da conta", anchor="w",
            bg=tema.LAB["perigo"], fg="white", relief="flat", font=("Segoe UI", 10),
            padx=14, pady=8, takefocus=0, command=self._sair_da_conta,
        ).pack(side="bottom", fill="x", padx=10, pady=(8, 4))
        self._atualizar_barra_lateral()

    def _atualizar_barra_lateral(self):
        """Mostra o troféu atual embaixo do nome e o cadeado da Área de Mutação."""
        total = bau_dados.trofeus()
        if total >= bau_dados.TOTAL_TROFEUS:
            titulo = "👑 Mestre da Colônia"
        elif total:
            titulo = f"{bau_dados.TROFEUS[total - 1]['emoji']} {total} troféu(s) • ciclo {total + 1}"
        else:
            titulo = "ciclo 1 de 5"
        self.rotulo_jogador.config(text=f"🧑‍🔬 {self.usuario_atual}\n{titulo}")
        cadeado = "" if bau_dados.mutacao_liberada() else "  🔒"
        self.botoes["Área de Mutação"].config(text=f"🧬  Área de Mutação{cadeado}")

    def _criar_telas(self):
        for nome, _icone, modulo, classe in TELAS:
            tela = getattr(sys.modules[modulo], classe)(self.container, self)
            tela.place(x=0, y=0, relwidth=1, relheight=1)
            self.telas[nome] = tela

    def mostrar_tela(self, nome):
        if nome == "Área de Mutação" and not bau_dados.mutacao_liberada():
            janelas.showinfo("Área de Mutação 🔒", "Esta área está selada.\n\nLeve a colônia até a Forma de Vida "
                                                  "Suprema e ganhe o troféu de 🌲 Madeira para abri-la.")
            return
        for nome_botao, botao in self.botoes.items():
            botao.config(bg=tema.LAB["ativo"] if nome_botao == nome else tema.LAB["fundo"])
        tela = self.telas[nome]
        self.tela_visivel = tela
        tela.tkraise()
        if hasattr(tela, "atualizar_ao_exibir"):
            tela.atualizar_ao_exibir()

    # ---------- troféus ----------

    def conquistar_trofeu(self):
        """A colônia chegou ao último estágio: ganha o próximo troféu e (até o Diamante) começa um ciclo novo."""
        self._trofeu_agendado = False
        ja_tinha = bau_dados.trofeus()
        if ja_tinha >= bau_dados.TOTAL_TROFEUS:
            return  # já é Mestre da Colônia: o jogo segue livre
        dados = bau_dados.TROFEUS[ja_tinha]
        # congela a placa enquanto a comemoração está na tela (ninguém mais se funde por trás)
        for tela in self.telas.values():
            if hasattr(tela, "parar_loop"):
                tela.parar_loop()
                tela._salvar_posicoes()
        persistencia.incrementar_estatistica("trofeus")
        persistencia.incrementar_estatistica(f"trofeu_{ja_tinha + 1}_quando", int(time.time()))
        persistencia.adicionar_entrada_diario(f"🏆 Troféu de {dados['nome']} conquistado! Liberou: {dados['libera']}.")
        avaliar_e_desbloquear({})
        sons.tocar(sons.SOM_TROFEU)

        ultimo = ja_tinha + 1 >= bau_dados.TOTAL_TROFEUS
        levou = bau_dados.membrana_que_fica()
        self._mostrar_comemoracao(dados, ja_tinha + 1, ultimo, levou)

        if not ultimo:
            persistencia.recomecar_ciclo(bau_dados.MEMBRANA_INICIAL, levou)
            persistencia.adicionar_entrada_diario(f"🌱 Começou o ciclo {ja_tinha + 2}. Boa sorte!")
        # reabre o jogo já com as cores do ciclo novo
        self.reiniciar = True
        self._ao_fechar()

    def _mostrar_comemoracao(self, dados, numero, ultimo, levou):
        """Janela de festa do troféu: o que conquistou, o que leva para o próximo ciclo e um boa sorte."""
        fundo, painel = tema.TROFEUS["fundo"], tema.TROFEUS["painel"]
        texto, suave = tema.TROFEUS["texto"], tema.TROFEUS["texto_suave"]
        janela = tk.Toplevel(self)
        janela.title(f"🏆 Troféu de {dados['nome']}!")
        janela.configure(bg=fundo, highlightbackground=dados["cor"], highlightthickness=4)
        janela.resizable(False, False)
        janela.transient(self)

        tk.Label(janela, text=dados["emoji"], bg=fundo, fg=dados["cor"], font=("Segoe UI Emoji", 54)).pack(
            pady=(18, 0))
        tk.Label(janela, text="🎉 VOCÊ AVANÇOU! 🎉", bg=fundo, fg=dados["cor"],
                 font=("Segoe UI", 20, "bold")).pack()
        tk.Label(janela, text=f"Você conquistou o troféu de {dados['emoji']} {dados['nome']}  ({numero} de "
                              f"{bau_dados.TOTAL_TROFEUS})", bg=fundo, fg=texto, font=("Segoe UI", 12, "bold")).pack(
            pady=(6, 2))
        tk.Label(janela, text=f"Liberado: {dados['libera']}", bg=fundo, fg=suave, font=("Segoe UI", 10),
                 wraplength=480).pack(pady=(0, 12))

        caixa = tk.Frame(janela, bg=painel, padx=20, pady=12)
        caixa.pack(padx=28, fill="x")
        if ultimo:
            linhas = ["👑 Agora você é MESTRE DA COLÔNIA!",
                      "Todos os troféus foram conquistados.",
                      "",
                      "O jogo vai reabrir com as cores de cristal do Mestre.",
                      "A sua colônia continua do jeito que está: jogue livremente."]
            frase_final, texto_botao = "🍀 Obrigado por jogar, cientista!", "Continuar ▶"
        else:
            linhas = [f"🔄 O jogo vai reiniciar no ciclo {numero + 1}, com cores novas.",
                      "🧫 A colônia e a Geladeira começam do zero.",
                      "",
                      "Você leva com você:",
                      "   ⬆️ todos os upgrades do Baú",
                      "   🧪 os frascos que você comprou",
                      f"   ⬡ {bau_dados.MEMBRANA_INICIAL} de Membrana + {levou} que sobraram deste ciclo",
                      f"   📖 o Manual (o ciclo {numero} fica guardado nele)",
                      "   🏅 conquistas e 🏆 troféus",
                      "",
                      "A reprodução fica um pouco mais difícil a cada ciclo."]
            frase_final, texto_botao = "🍀 Boa sorte, cientista!", f"Começar o ciclo {numero + 1} ▶"
        tk.Label(caixa, text="\n".join(linhas), bg=painel, fg=texto, font=("Segoe UI", 10),
                 justify="left").pack(anchor="w")

        tk.Label(janela, text=frase_final, bg=fundo, fg=dados["cor"], font=("Segoe UI", 15, "bold")).pack(
            pady=(14, 8))
        botao = tk.Button(janela, text=texto_botao, command=janela.destroy, bg=dados["cor"], fg=fundo,
                          activebackground=texto, relief="flat", font=("Segoe UI", 11, "bold"), padx=22, pady=6)
        botao.pack(pady=(0, 20))
        janela.bind("<Return>", lambda evento: janela.destroy())

        janela.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - janela.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - janela.winfo_height()) // 3
        janela.geometry(f"+{max(0, x)}+{max(0, y)}")
        janela.grab_set()
        botao.focus_set()
        janela.wait_window()

    def _ao_fechar(self):
        for tela in self.telas.values():
            if hasattr(tela, "parar_loop"):
                tela.parar_loop()
                tela._salvar_posicoes()
        persistencia.fechar_conexao()
        self.destroy()

    def _sair_da_conta(self):
        if janelas.askyesno("Sair da conta", f"Sair da conta de {self.usuario_atual}?\n"
                                             "O progresso já está salvo."):
            self.voltar_ao_login = True
            self._ao_fechar()


def _abrir_aplicativo_principal(nome_usuario):
    # Cada conta tem o próprio save: abre o arquivo dela antes de montar o jogo.
    persistencia.abrir_save(nome_usuario)
    ciclo_novo = False
    while True:
        _preparar_visual(_ciclo_do_visual())
        app = App(usuario_atual=nome_usuario, ciclo_novo=ciclo_novo)
        app.mainloop()
        if not app.reiniciar:
            break
        # ganhou um troféu: reabre o jogo com as cores do ciclo novo
        ciclo_novo = bau_dados.trofeus() < bau_dados.TOTAL_TROFEUS
    if app.voltar_ao_login:
        # o jogo fechou pelo botão "Sair da conta": volta para a tela de login (com as cores normais)
        _preparar_visual(1)
        from tela_login import iniciar_fluxo_login
        iniciar_fluxo_login(_abrir_aplicativo_principal)


if __name__ == "__main__":
    persistencia.conectar_contas()
    _preparar_visual(1)
    from tela_login import iniciar_fluxo_login
    iniciar_fluxo_login(_abrir_aplicativo_principal)
