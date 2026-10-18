import tkinter as tk

import persistencia
import recursos
import tema
import bau_dados
from organismo import Organismo
from comportamento import COMPORTAMENTOS
from evolucao_dados import (TOTAL_ESTAGIOS, BLOCOS, dados_completos_estagio, receitas_fusao_do_estagio,
                            tamanho_do_estagio)

# clima "mesa do cientista": madeira, couro e papel (tema.MESA)
COR_FUNDO = tema.MESA["fundo"]
COR_DESCOBERTO = tema.MESA["painel"]
COR_BLOQUEADO = tema.MESA["bloqueado"]
COR_BORDA_CELULA = tema.MESA["painel_claro"]
COR_TEXTO = tema.MESA["texto"]
COR_TEXTO_SUAVE = tema.MESA["texto_suave"]
COLUNAS = 5


def desenhar_organismo(canvas, estagio, x, y, raio):
    """Desenha o organismo do estágio usando o mesmo PNG da simulação."""
    organismo = Organismo(
        id_banco=None, estagio=estagio, x=x, y=y, velocidade_mod=1.0,
        tamanho_mod=raio / tamanho_do_estagio(estagio), comportamento="Calmo",
    )
    organismo.criar_no_canvas(canvas)
    return organismo


def desenhar_silhueta(canvas, x, y, raio):
    canvas.create_oval(x - raio, y - raio, x + raio, y + raio, fill=COR_BLOQUEADO, outline=COR_BORDA_CELULA, width=2)
    canvas.create_text(x, y, text="?", fill=COR_TEXTO_SUAVE, font=("Segoe UI", int(raio * 0.9), "bold"))


def texto_como_jogar():
    linhas = [
        "🎯 OBJETIVO",
        f"Levar a colônia pelos {TOTAL_ESTAGIOS} estágios até a Forma de Vida Suprema. Cada vez que você chega lá,",
        "ganha um 🏆 troféu (Madeira → Bronze → Prata → Ouro → Diamante) e começa um ciclo novo.",
        "",
        "🧫 A PLACA (tela Simulação)",
        "• Dois organismos do MESMO estágio que se encostam se fundem e viram o estágio seguinte (+3 ⬡).",
        "• Cada evolução deixa o organismo maior: os primeiros estágios são pequenos e os últimos são grandes.",
        "• Grupos: " + "  •  ".join(f"{b['emoji']} {b['nome']} ({b['inicio']}–{b['fim']})" for b in BLOCOS),
        f"• “+ Organismo” custa {bau_dados.CUSTO_ORGANISMO} ⬡. Ficou sem Membrana? Clique num organismo: ele “brota” +1 ⬡.",
        "  Sem Membrana e com a placa vazia, o “+ Organismo” sai de graça.",
        "• “Nasce:” (ao lado do “+ Organismo”): clique no desenho do estágio que vai nascer. A 🧬 Cultura Avançada",
        "  do Baú destranca os estágios 2, 3 e 4 (🔒).",
        "• Na placa ninguém se reproduz. Para ter mais organismos, use a Área de Fusão.",
        "",
        "⚗️ A ÁREA DE FUSÃO",
        "• Leve organismos para lá pelo botão direito → “Coletar para a Área de Fusão”.",
        "• Lá, dois iguais que se encostam podem ter um filhote (reprodução, +1 ⬡). Eles não se fundem lá.",
        "• “Soltar na placa” devolve o organismo para a Simulação, onde ele pode se fundir.",
        "",
        "🧬 A ÁREA DE MUTAÇÃO  (abre com o troféu de 🌲 Madeira)",
        "• Clique em 2 do mesmo estágio e aperte “Tentar Fusão”: se um deles tiver o comportamento que a",
        "  receita pede, nasce uma 🧬 Mutação. As receitas de cada estágio aparecem na ficha dele.",
        "• Duas Mutações do mesmo estágio que se encostam lá se fundem e pulam +2 estágios!",
        "",
        "🏆 TROFÉUS E CICLOS",
    ]
    for numero, trofeu in enumerate(bau_dados.TROFEUS, start=1):
        linhas.append(f"  {trofeu['emoji']} {numero}º — {trofeu['nome']}: libera {trofeu['libera']}")
    linhas += [
        "• A cada troféu, o jogo reinicia num ciclo novo com cores novas. A colônia e a Geladeira recomeçam.",
        f"• Você leva: upgrades do Baú, frascos, conquistas, troféus, {bau_dados.MEMBRANA_INICIAL} ⬡ + "
        f"{round(bau_dados.PARTE_DA_MEMBRANA_QUE_FICA * 100)}% da Membrana",
        "  que sobrou, e este Manual (cada ciclo ganha uma página; arraste para o lado). A reprodução fica mais difícil.",
        "",
        "🧠 COMPORTAMENTOS",
    ]
    for nome, dados in COMPORTAMENTOS.items():
        if dados.get("ia"):
            origem = "IA — começa a nascer depois do troféu de Prata"
        else:
            origem = "nasce assim" if dados["natural"] else "só pela ação do cientista"
        linhas.append(f"{dados['emoji']} {nome}  ({origem})  —  velocidade ×{dados['velocidade_mult']}, "
                      f"tamanho ×{dados['tamanho_mult']}")
        linhas.append(f"     {dados['descricao']}")
    linhas += [
        "",
        "🏷️ SELOS",
        "❓ amarelo  →  espécie nova! Aparece por alguns segundos no primeiro organismo de um estágio.",
        "❗ vermelho  →  interferência do cientista ou IA: Infectado, Mutação, Guardião, Predador ou Simbionte.",
        "",
        "🖱️ CONTROLES",
        "• Arrastar com o botão esquerdo: move um organismo (ou a visão, se clicar no fundo).",
        "• Clique simples: na placa, inspeciona; na Área de Mutação, seleciona para a fusão.",
        "• Botão direito: menu (inspecionar, coletar, soltar, infectar, destruir).",
        "• Roda do mouse ou botões − / +: zoom de 100% a 300% (a 🔭 Lente Potente do Baú vai até 500%).",
        "• Setas do teclado: andam pelo mapa, que é maior que a tela.",
        "• Minimapa (canto de baixo): mostra o mapa inteiro; clique nele para ir até um lugar.",
        "• Espaço ou botão ⏸: pausa e continua.  •  Botão ⏩: velocidade 1× / 2× / 4×.",
        "• F11: tela cheia  •  Esc: sai da tela cheia (ou cancela a mira de um frasco).",
        "",
        "📦 BAÚ E MEMBRANA ⬡",
        "• Unir dois organismos iguais rende +3 Membrana. Espécies novas e conquistas também rendem.",
        "• Upgrades (permanentes, até 3 níveis, sempre bons). Alguns só aparecem depois de certo troféu (🔒).",
        "• Frascos (uso único): você escolhe ser herói ou vilão. Compre no Baú, escolha o frasco na",
        "  barra embaixo da placa e clique no mapa. Esc ou botão direito cancela.",
        "  💧 Nutritivo • 💉 Antídoto • ✨ Evolutivo (herói)   ☣️ Corrompido • 💀 Antibiótico (vilão)",
        "  🔁 Reverso (aposta)   •   depois do troféu de Bronze: 🦠 Praga • 🧨 Instável • 🌪 Caos (vilão)",
        "• O ✨ Evolutivo fica +20 ⬡ mais caro a cada compra no mesmo ciclo.",
        "",
        "🧊 GELADEIRA, 📔 DIÁRIO e 🏅 CONQUISTAS",
        "• Geladeira: guarda até 6 cenários da sua colônia para carregar depois.",
        "• Diário: anota descobertas, fusões e infecções. “Arquivar tudo” salva um .txt e limpa a lista.",
        "• Conquistas: use o filtro Todas / Feitas / Faltando.",
        "• Cada conta tem o seu próprio progresso.",
    ]
    return "\n".join(linhas)


class TelaManual(tk.Frame):
    """Manual de Coleção: uma página por ciclo, lado a lado. Os ciclos já jogados nunca somem."""

    LARGURA_CELULA = 168
    ALTURA_CELULA = 110

    def __init__(self, master, controlador):
        super().__init__(master, bg=COR_FUNDO)
        self.controlador = controlador
        recursos.aplicar_fundo_frame(self, "manual")
        self._desenhos = []
        self._ultimo_estado = None
        self._paginas = []
        self._arraste_inicio = None
        self._arrastou = False

        topo = tk.Frame(self, bg=COR_FUNDO)
        topo.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(topo, text="📖 Manual de Coleção", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Button(topo, text="❔ Como jogar", command=self._abrir_como_jogar, bg=tema.MESA["destaque"], fg=tema.MESA["tinta"],
                  relief="flat", padx=12).pack(side="right")
        tk.Button(topo, text="▶", command=lambda: self._pular_pagina(1), bg=tema.MESA["painel_claro"], fg=COR_TEXTO,
                  relief="flat", width=3).pack(side="right", padx=(4, 12))
        tk.Button(topo, text="◀", command=lambda: self._pular_pagina(-1), bg=tema.MESA["painel_claro"], fg=COR_TEXTO,
                  relief="flat", width=3).pack(side="right")

        self.rotulo_progresso = tk.Label(self, text="", fg=COR_TEXTO_SUAVE, bg=COR_FUNDO,
                                          font=("Segoe UI", 10))
        self.rotulo_progresso.pack(pady=(0, 6))

        # faixa que anda para o lado: um Canvas com um Frame dentro (cada ciclo é uma página)
        self.barra = tk.Scrollbar(self, orient="horizontal")
        self.barra.pack(side="bottom", fill="x", padx=14, pady=(0, 8))
        self.canvas_faixa = tk.Canvas(self, bg=COR_FUNDO, highlightthickness=0, xscrollcommand=self.barra.set)
        self.canvas_faixa.pack(fill="both", expand=True, padx=14, pady=4)
        self.barra.config(command=self.canvas_faixa.xview)
        self.faixa = tk.Frame(self.canvas_faixa, bg=COR_FUNDO)
        self.canvas_faixa.create_window(0, 0, window=self.faixa, anchor="nw")
        self.faixa.bind("<Configure>", lambda evento: self.canvas_faixa.config(
            scrollregion=self.canvas_faixa.bbox("all")))
        self._ligar_arraste(self.canvas_faixa)

        self._montar_paginas()

    # ---------- arrastar para o lado ----------

    def _ligar_arraste(self, widget, estagio=None):
        widget.bind("<ButtonPress-1>", self._comecar_arraste)
        widget.bind("<B1-Motion>", self._arrastar)
        widget.bind("<ButtonRelease-1>", lambda evento: self._soltar(estagio))
        widget.bind("<MouseWheel>", self._rodinha)

    def _comecar_arraste(self, evento):
        self._arraste_inicio = evento.x_root
        self._arrastou = False
        self.canvas_faixa.scan_mark(evento.x_root, 0)

    def _arrastar(self, evento):
        if self._arraste_inicio is None:
            return
        if abs(evento.x_root - self._arraste_inicio) > 6:
            self._arrastou = True
        self.canvas_faixa.scan_dragto(evento.x_root, 0, gain=1)

    def _soltar(self, estagio):
        # um clique sem arrastar num organismo descoberto abre a ficha dele
        if estagio is not None and not self._arrastou:
            self._mostrar_detalhe(estagio)
        self._arraste_inicio = None

    def _rodinha(self, evento):
        self.canvas_faixa.xview_scroll(-1 if evento.delta > 0 else 1, "units")

    def _pular_pagina(self, direcao):
        if not self._paginas:
            return
        esquerda = self.canvas_faixa.canvasx(0)
        # a página que está mais perto da borda esquerda é a "atual"
        atual = min(range(len(self._paginas)), key=lambda i: abs(self._paginas[i].winfo_x() - esquerda))
        self._ir_para_pagina(max(0, min(len(self._paginas) - 1, atual + direcao)))

    def _ir_para_pagina(self, indice):
        self.update_idletasks()
        largura_total = max(1, self.faixa.winfo_width())
        self.canvas_faixa.xview_moveto(self._paginas[indice].winfo_x() / largura_total)

    # ---------- páginas ----------

    def _montar_paginas(self):
        por_ciclo = persistencia.listar_descobertas_por_ciclo()
        ciclo_atual = persistencia.ciclo_atual()
        estado = (ciclo_atual, tuple(sorted((c, tuple(sorted(e))) for c, e in por_ciclo.items())))
        if estado == self._ultimo_estado:
            return  # nada mudou: não precisa redesenhar as 125 fichas
        self._ultimo_estado = estado

        for widget in self.faixa.winfo_children():
            widget.destroy()
        self._desenhos = []
        self._paginas = []

        total_geral = len(set().union(*por_ciclo.values())) if por_ciclo else 0
        self.rotulo_progresso.config(
            text=f"Ciclo atual: {len(por_ciclo.get(ciclo_atual, ()))} / {TOTAL_ESTAGIOS}   •   "
                 f"Espécies já vistas: {total_geral} / {TOTAL_ESTAGIOS}   •   "
                 "Arraste para o lado (ou ◀ ▶) para ver os outros ciclos   •   Clique num organismo para ver a ficha")

        for ciclo in range(1, persistencia.TOTAL_CICLOS + 1):
            self._montar_pagina(ciclo, por_ciclo.get(ciclo, set()), ciclo_atual)

    def _montar_pagina(self, ciclo, descobertos, ciclo_atual):
        trofeu = bau_dados.TROFEUS[ciclo - 1]
        fechado = ciclo < ciclo_atual or bau_dados.trofeus() >= ciclo
        if fechado:
            situacao = f"✔ troféu de {trofeu['nome']} conquistado"
        elif ciclo == ciclo_atual:
            situacao = "▶ ciclo atual"
        else:
            situacao = "🔒 ainda vai chegar"

        pagina = tk.Frame(self.faixa, bg=COR_FUNDO, padx=14)
        pagina.pack(side="left", anchor="n")
        self._paginas.append(pagina)
        self._ligar_arraste(pagina)
        cabecalho = tk.Label(pagina, text=f"{trofeu['emoji']}  Ciclo {ciclo}  —  {len(descobertos)} / "
                                          f"{TOTAL_ESTAGIOS}   •   {situacao}",
                             fg=trofeu["cor"] if ciclo <= ciclo_atual else COR_TEXTO_SUAVE, bg=tema.MESA["painel"],
                             font=("Segoe UI", 11, "bold"), pady=4)
        cabecalho.pack(fill="x", pady=(0, 6))
        self._ligar_arraste(cabecalho)
        grade = tk.Frame(pagina, bg=COR_FUNDO)
        grade.pack()
        self._ligar_arraste(grade)

        for estagio in range(1, TOTAL_ESTAGIOS + 1):
            dados = dados_completos_estagio(estagio)
            descoberto = estagio in descobertos
            cor = COR_DESCOBERTO if descoberto else COR_BLOQUEADO

            celula = tk.Frame(grade, bg=cor, width=self.LARGURA_CELULA, height=self.ALTURA_CELULA,
                               highlightbackground=COR_BORDA_CELULA, highlightthickness=1)
            celula.grid(row=(estagio - 1) // COLUNAS, column=(estagio - 1) % COLUNAS, padx=4, pady=4)
            celula.grid_propagate(False)
            celula.pack_propagate(False)

            desenho = tk.Canvas(celula, width=70, height=62, bg=cor, highlightthickness=0)
            desenho.pack(pady=(4, 0))
            if descoberto:
                self._desenhos.append(desenhar_organismo(desenho, estagio, 35, 31, 27))
                texto_nome = dados["nome"]
                texto_bloco = f"#{estagio:02d} • {dados['bloco']}"
            else:
                desenhar_silhueta(desenho, 35, 31, 22)
                texto_nome = "???"
                texto_bloco = f"#{estagio:02d}"

            tk.Label(celula, text=texto_nome, bg=cor, fg=COR_TEXTO, font=("Segoe UI", 8, "bold"),
                     wraplength=160).pack()
            tk.Label(celula, text=texto_bloco, bg=cor, fg=COR_TEXTO_SUAVE, font=("Segoe UI", 7)).pack()

            alvo = estagio if descoberto else None
            self._ligar_arraste(celula, alvo)
            for filho in celula.winfo_children():
                self._ligar_arraste(filho, alvo)
                if descoberto:
                    filho.config(cursor="hand2")

    def _mostrar_detalhe(self, estagio):
        dados = dados_completos_estagio(estagio)
        receitas = receitas_fusao_do_estagio(estagio)
        texto_receitas = "\n".join(
            f"  • {r['nome']}\n     (um dos dois precisa ser {COMPORTAMENTOS[r['comportamento_exigido']]['emoji']} "
            f"{r['comportamento_exigido']})" for r in receitas
        )

        janela = tk.Toplevel(self)
        janela.title(f"Estágio {estagio} — {dados['nome']}")
        janela.configure(bg=COR_FUNDO)
        janela.resizable(False, False)
        janela.transient(self.winfo_toplevel())

        desenho = tk.Canvas(janela, width=200, height=200, bg=COR_DESCOBERTO, highlightthickness=0)
        desenho.pack(padx=20, pady=(20, 10))
        janela._organismo = desenhar_organismo(desenho, estagio, 100, 100, 80)

        tk.Label(janela, text=f"{dados['emoji']}  {dados['nome']}", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 13, "bold")).pack()
        tk.Label(janela, text=f"Estágio {estagio} de {TOTAL_ESTAGIOS}   •   Grupo: {dados['bloco']}   •   "
                              f"Tamanho: {round(dados['tamanho'] * 2)} px",
                 fg=COR_TEXTO_SUAVE, bg=COR_FUNDO, font=("Segoe UI", 9)).pack(pady=(2, 10))
        tk.Label(janela, text=f"Receitas de fusão manual:\n{texto_receitas}", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 9), justify="left").pack(padx=20, anchor="w")
        tk.Button(janela, text="Fechar", command=janela.destroy, bg=COR_BORDA_CELULA, fg=COR_TEXTO,
                  relief="flat", padx=14).pack(pady=14)

    def _abrir_como_jogar(self):
        janela = tk.Toplevel(self)
        janela.title("Como jogar — Colônia")
        janela.configure(bg=COR_FUNDO)
        janela.geometry("760x560")
        janela.transient(self.winfo_toplevel())

        barra = tk.Scrollbar(janela)
        barra.pack(side="right", fill="y")
        caixa = tk.Text(janela, bg=tema.MESA["papel"], fg=tema.MESA["tinta"], wrap="word", font=("Segoe UI", 10),
                        padx=16, pady=14, yscrollcommand=barra.set, relief="flat")
        caixa.pack(side="left", fill="both", expand=True)
        barra.config(command=caixa.yview)
        caixa.insert("1.0", texto_como_jogar())
        caixa.config(state="disabled")

    def atualizar_ao_exibir(self):
        self._montar_paginas()
        # abre sempre na página do ciclo que está sendo jogado
        self.after(50, lambda: self._ir_para_pagina(persistencia.ciclo_atual() - 1))
