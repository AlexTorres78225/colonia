import tkinter as tk
import janelas
import random
import math

import persistencia
import recursos
import sons
import tema
import bau_dados
from organismo import Organismo
from camera import Camera, PASSO_ZOOM, ZOOM_MAXIMO
from comportamento import modificadores, escolher_comportamento_aleatorio, eh_natural, eh_ia
from habilidades import gerar_habilidades_iniciais
from evolucao_dados import nome_do_estagio, cor_do_estagio, TOTAL_ESTAGIOS
from conquistas import avaliar_e_desbloquear

# Tela = o pedaço que aparece no monitor. Mundo = o mapa inteiro (3 telas de largura x 2 de altura).
LARGURA_TELA = 940            # tamanho inicial; em tela cheia a área do jogo cresce (ver _ao_redimensionar_canvas)
ALTURA_TELA = 540
LARGURA_MUNDO = LARGURA_TELA * 3
ALTURA_MUNDO = ALTURA_TELA * 2

# o limite de população agora vem do Baú (🧫 Placa Maior): bau_dados.limite_populacao()
TAMANHO_CELULA_GRADE = 100
DISTANCIA_MINIMA_ARRASTO = 4
MARGEM = 20
VELOCIDADE_CAMERA = 18        # pixels da tela por quadro, ao segurar uma seta
DISTANCIA_PERSEGUICAO = 250   # até onde o Irritado enxerga um vizinho
RECARGA_CONTAGIO = 50         # quadros entre uma tentativa de contágio e outra
ESPACO_GRADE_FUNDO = 200      # linhas do fundo, para dar noção de movimento
VELOCIDADES = (1, 2, 4)       # opções do botão ⏩

LARGURA_MINIMAPA = 180
ALTURA_MINIMAPA = round(LARGURA_MINIMAPA * ALTURA_MUNDO / LARGURA_MUNDO)
TECLAS_SETAS = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}


class PlacaBase(tk.Frame):
    """Base das telas que mostram organismos vivos (Simulação e Área de Fusão).

    Cuida do que as duas têm em comum: loop de movimento, pausa, câmera (zoom, setas
    e minimapa), arrastar com o mouse, menu do botão direito e contágio.
    Cada tela filha decide o que acontece quando dois organismos iguais se encostam
    (_resolver_interacao).
    """

    LOCAL = "placa"
    TITULO = ""
    DICA = ""
    TEXTO_VAZIO = ""
    NOME_FUNDO = "simulacao"
    # cores vindas do tema.py (a Área de Fusão troca para tema.FUSAO)
    COR_FUNDO = tema.LAB["fundo"]
    COR_CANVAS = tema.LAB["fundo"]
    COR_GRADE = tema.LAB["grade"]
    COR_BORDA = tema.LAB["borda"]
    COR_TEXTO = tema.LAB["texto"]
    COR_TEXTO_SUAVE = tema.LAB["texto_suave"]
    COR_PAINEL = tema.LAB["painel"]
    COR_BOTAO = tema.LAB["painel_claro"]
    COR_BOTAO_LIGADO = tema.LAB["destaque"]
    COR_TEXTO_BOTAO = "white"
    COR_AVISO = tema.LAB["aviso"]

    def __init__(self, master, controlador):
        super().__init__(master, bg=self.COR_FUNDO)
        self.controlador = controlador
        self.organismos = []
        self.rodando = False
        self.pausado = False
        self.velocidade = 1
        self.contador_ciclos = 0
        self.contador_quadros = 0
        self.comportamentos_vistos = set()
        self.camera = Camera(LARGURA_TELA, ALTURA_TELA, LARGURA_MUNDO, ALTURA_MUNDO)
        self.camera.zoom_maximo = bau_dados.zoom_maximo()
        self.camera.centralizar_em(LARGURA_MUNDO / 2, ALTURA_MUNDO / 2)
        self._frasco_mirando = None   # frasco escolhido na barra, esperando o clique no mapa

        self.arrastando = None
        self._inicio_clique = None
        self._moveu_mouse = False
        self._arrasto_camera = None
        self._arrastando_minimapa = False
        self._teclas_apertadas = set()
        self._ja_explorou = False
        self._id_proximo_ciclo = None
        self._id_redesenho = None
        self._especies_novas = {}
        self._item_borda = None
        self._item_vazio = None
        self._itens_grade_fundo = []

        self._montar_layout()
        self._carregar_inicial()
        self._atualizar_membrana()
        self._atualizar_barra_frascos()
        self.iniciar_loop()

    # ---------- montagem da tela ----------

    def _botao(self, pai, texto, comando, cor, **opcoes):
        # takefocus=0: assim a barra de espaço pausa o jogo em vez de "apertar" o botão
        return tk.Button(pai, text=texto, command=comando, bg=cor, fg=self._cor_texto_do_botao(cor),
                         activebackground=self.COR_BORDA, relief="flat", takefocus=0, **opcoes)

    def _cor_texto_do_botao(self, cor_fundo):
        # botão claro (como o âmbar da Fusão) pede texto escuro; botão escuro, texto branco
        return self.COR_TEXTO_BOTAO if cor_fundo == self.COR_BOTAO_LIGADO else "white"

    def _montar_layout(self):
        topo = tk.Frame(self, bg=self.COR_FUNDO)
        topo.pack(fill="x", padx=10, pady=(8, 0))

        tk.Label(topo, text=self.TITULO, fg=self.COR_TEXTO, bg=self.COR_FUNDO,
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        self.rotulo_populacao = tk.Label(topo, text="População: 0", fg=self.COR_TEXTO_SUAVE,
                                          bg=self.COR_FUNDO, font=("Segoe UI", 11))
        self.rotulo_populacao.pack(side="right")

        self.rotulo_membrana = tk.Label(topo, text="⬡ 0", fg=self.COR_AVISO, bg=self.COR_FUNDO,
                                        font=("Segoe UI", 11, "bold"))
        self.rotulo_membrana.pack(side="right", padx=(0, 16))

        self._botao(topo, "+", lambda: self._mudar_zoom(self.camera.zoom + PASSO_ZOOM), self.COR_BOTAO,
                    width=3).pack(side="right", padx=(2, 16))
        self.rotulo_zoom = tk.Label(topo, text="100%", width=5, fg=self.COR_TEXTO_SUAVE, bg=self.COR_FUNDO,
                                     font=("Segoe UI", 10))
        self.rotulo_zoom.pack(side="right")
        self._botao(topo, "−", lambda: self._mudar_zoom(self.camera.zoom - PASSO_ZOOM), self.COR_BOTAO,
                    width=3).pack(side="right", padx=2)
        tk.Label(topo, text="🔍 Zoom", fg=self.COR_TEXTO_SUAVE, bg=self.COR_FUNDO,
                 font=("Segoe UI", 10)).pack(side="right", padx=(0, 4))

        self.botao_pausa = self._botao(topo, "⏸ Pausar", self.alternar_pausa, self.COR_BOTAO, width=11)
        self.botao_pausa.pack(side="right", padx=(0, 16))

        self.botao_velocidade = self._botao(topo, "⏩ 1×", self.alternar_velocidade, self.COR_BOTAO, width=6)
        self.botao_velocidade.pack(side="right", padx=(0, 6))

        tk.Label(self, text=self.DICA, fg=self.COR_TEXTO_SUAVE, bg=self.COR_FUNDO,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12)

        # o rodapé é preso embaixo ANTES da área do jogo, para ela poder crescer sem empurrá-lo para fora
        rodape = tk.Frame(self, bg=self.COR_FUNDO)
        rodape.pack(side="bottom", fill="x", padx=10, pady=6)
        self._montar_botoes(rodape)

        # barra de frascos: os frascos comprados no Baú aparecem aqui para usar no mapa
        self.barra_frascos = tk.Frame(rodape, bg=self.COR_FUNDO)
        self.barra_frascos.pack(side="left", padx=(18, 0))

        self.rotulo_evento = tk.Label(rodape, text="", fg=self.COR_AVISO, bg=self.COR_FUNDO,
                                       font=("Segoe UI", 10, "italic"))
        self.rotulo_evento.pack(side="right")

        # fill + expand: a área do jogo ocupa todo o espaço que sobrar (cresce em tela cheia)
        self.canvas = tk.Canvas(self, width=LARGURA_TELA, height=ALTURA_TELA, bg=self.COR_CANVAS,
                                 highlightthickness=1, highlightbackground=self.COR_BORDA)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=4)
        self.canvas.bind("<Configure>", self._ao_redimensionar_canvas)
        self.canvas.bind("<ButtonPress-1>", self._ao_pressionar)
        self.canvas.bind("<B1-Motion>", self._ao_arrastar)
        self.canvas.bind("<ButtonRelease-1>", self._ao_soltar)
        self.canvas.bind("<Button-3>", self._ao_clicar_direito)
        self.canvas.bind("<MouseWheel>", self._ao_rolar)
        self.canvas.bind("<Motion>", self._desenhar_mira)

        janela = self.winfo_toplevel()
        janela.bind("<KeyPress>", self._ao_apertar_tecla, add="+")
        janela.bind("<KeyRelease>", self._ao_soltar_tecla, add="+")
        # o main.py já usa <Escape> (sair da tela cheia); uma ligação específica "esconde" a genérica
        # <KeyPress>, então a placa também se liga ao <Escape> (add="+" faz as duas rodarem)
        janela.bind("<Escape>", self._ao_apertar_tecla, add="+")

    def _ao_redimensionar_canvas(self, evento):
        """A janela mudou de tamanho: a câmera passa a mostrar um pedaço maior (ou menor) do mapa."""
        largura, altura = evento.width - 2, evento.height - 2   # tira a borda de 1 px de cada lado
        if (largura, altura) == (self.camera.largura_tela, self.camera.altura_tela):
            return
        self.camera.largura_tela, self.camera.altura_tela = largura, altura
        self.camera.limitar()
        # espera a janela parar de mudar de tamanho para redesenhar uma vez só
        if self._id_redesenho is not None:
            self.after_cancel(self._id_redesenho)
        self._id_redesenho = self.after(80, self._redesenhar_tudo_do_zero)

    def _montar_botoes(self, rodape):
        pass

    # ---------- organismos ----------

    def _posicao_aleatoria(self):
        """Um lugar sorteado dentro do pedaço do mapa que está aparecendo na tela."""
        margem = 40
        x0, y0 = self.camera.x, self.camera.y
        x = random.uniform(x0 + margem, x0 + self.camera.largura_visivel() - margem)
        y = random.uniform(y0 + margem, y0 + self.camera.altura_visivel() - margem)
        return x, y

    def _carregar_inicial(self):
        self._carregar_organismos()

    def _carregar_organismos(self):
        linhas = persistencia.listar_organismos(self.LOCAL)
        self.organismos = [Organismo.a_partir_de_linha(linha) for linha in linhas]
        for organismo in self.organismos:
            # o ❓ não fica no banco: a tela lembra pelo id até o tempo dele acabar
            organismo.novo_ate = self._especies_novas.get(organismo.id_banco, 0)
        self._redesenhar_tudo_do_zero()

    def _marcar_especie_nova(self, organismo):
        organismo.marcar_como_especie_nova()
        self._especies_novas[organismo.id_banco] = organismo.novo_ate

    def _criar_organismo_no_banco(self, estagio, x=None, y=None, habilidades=None, tipo="normal", variante=""):
        if x is None or y is None:
            x, y = self._posicao_aleatoria()
        if habilidades is None:
            habilidades = gerar_habilidades_iniciais()
        if tipo == "normal" and eh_natural(habilidades["comportamento"]):
            # depois do troféu de Prata, às vezes quem nasce é uma IA
            habilidades = dict(habilidades, comportamento=bau_dados.comportamento_de_nascimento(
                habilidades["comportamento"]))
        novo_id = persistencia.criar_organismo(
            estagio, x, y, habilidades["velocidade_mod"], habilidades["tamanho_mod"],
            habilidades["comportamento"], tipo=tipo, local=self.LOCAL, variante=variante,
        )
        novo = Organismo(
            id_banco=novo_id, estagio=estagio, x=x, y=y,
            velocidade_mod=habilidades["velocidade_mod"], tamanho_mod=habilidades["tamanho_mod"],
            comportamento=habilidades["comportamento"], tipo=tipo, local=self.LOCAL, variante=variante,
        )
        novo.ganho_descoberta = self._registrar_descoberta(novo)
        return novo

    def _registrar_descoberta(self, organismo):
        """Primeira vez que este estágio aparece no ciclo? Marca no Manual, dá Membrana e,
        se for o último estágio, agenda o troféu. Devolve quanto de Membrana rendeu (0 se não era novo)."""
        if not persistencia.marcar_estagio_descoberto(organismo.estagio):
            return 0
        self._marcar_especie_nova(organismo)
        ganho = bau_dados.ganhar(bau_dados.recompensa_especie_nova())
        persistencia.adicionar_entrada_diario(f"Nova espécie descoberta: {nome_do_estagio(organismo.estagio)} "
                                              f"(estágio {organismo.estagio}).")
        if organismo.estagio >= TOTAL_ESTAGIOS:
            self._agendar_trofeu()
        return ganho

    def _agendar_trofeu(self):
        controlador = self.controlador
        if hasattr(controlador, "conquistar_trofeu") and not getattr(controlador, "_trofeu_agendado", False):
            controlador._trofeu_agendado = True
            self._mostrar_evento("🏆 ÚLTIMO ESTÁGIO ALCANÇADO! Preparando o troféu…")
            self.after(2500, controlador.conquistar_trofeu)

    def _criar_e_mostrar(self, estagio, x=None, y=None, habilidades=None, tipo="normal", variante=""):
        novo = self._criar_organismo_no_banco(estagio, x, y, habilidades, tipo, variante)
        novo.criar_no_canvas(self.canvas, self.camera)
        self.organismos.append(novo)
        if novo.ganho_descoberta:
            self._mostrar_evento(f"❓ Nova espécie: {nome_do_estagio(estagio)}! (+{novo.ganho_descoberta} ⬡)")
            self._mostrar_ganho(novo.x, novo.y - novo.raio(), novo.ganho_descoberta)
        self._atualizar_rotulo_populacao()
        return novo

    def _remover_organismo(self, organismo, apagar_do_banco=True):
        if apagar_do_banco:
            persistencia.remover_organismo(organismo.id_banco)
        organismo.remover_do_canvas(self.canvas)
        if organismo in self.organismos:
            self.organismos.remove(organismo)
        if self.arrastando is organismo:
            self.arrastando = None
        self._ao_remover(organismo)
        self._atualizar_rotulo_populacao()

    def _ao_remover(self, organismo):
        pass

    def _atualizar_rotulo_populacao(self):
        self.rotulo_populacao.config(text=f"População: {len(self.organismos)}")

    # ---------- desenho ----------

    def _redesenhar_tudo_do_zero(self):
        for organismo in self.organismos:
            organismo.itens_canvas = []
            organismo.itens_selo = []
        self.canvas.delete("all")
        self._item_vazio = None
        self._imagem_fundo = recursos.aplicar_fundo_canvas(self.canvas, self.NOME_FUNDO,
                                                            self.camera.largura_tela, self.camera.altura_tela)
        self._itens_grade_fundo = []
        for x in range(ESPACO_GRADE_FUNDO, LARGURA_MUNDO, ESPACO_GRADE_FUNDO):
            self._itens_grade_fundo.append(("v", x, self.canvas.create_line(0, 0, 0, 0, fill=self.COR_GRADE)))
        for y in range(ESPACO_GRADE_FUNDO, ALTURA_MUNDO, ESPACO_GRADE_FUNDO):
            self._itens_grade_fundo.append(("h", y, self.canvas.create_line(0, 0, 0, 0, fill=self.COR_GRADE)))
        self._item_borda = self.canvas.create_rectangle(0, 0, 0, 0, outline=self.COR_BORDA, width=3)
        self._posicionar_fundo()
        for organismo in self.organismos:
            organismo.criar_no_canvas(self.canvas, self.camera)
        self._atualizar_extras()
        self._desenhar_minimapa()
        self._atualizar_rotulo_populacao()

    def _posicionar_fundo(self):
        """Linhas do fundo e borda do mapa acompanham a câmera."""
        x0, y0 = self.camera.para_tela(0, 0)
        x1, y1 = self.camera.para_tela(LARGURA_MUNDO, ALTURA_MUNDO)
        for direcao, valor, item in self._itens_grade_fundo:
            if direcao == "v":
                xt, _ = self.camera.para_tela(valor, 0)
                self.canvas.coords(item, xt, y0, xt, y1)
            else:
                _, yt = self.camera.para_tela(0, valor)
                self.canvas.coords(item, x0, yt, x1, yt)
        if self._item_borda is not None:
            self.canvas.coords(self._item_borda, x0 + 2, y0 + 2, x1 - 2, y1 - 2)

    def _atualizar_todos_na_tela(self):
        self._posicionar_fundo()
        for organismo in self.organismos:
            organismo.atualizar_no_canvas(self.canvas, self.camera)
        self._atualizar_extras()

    def _atualizar_extras(self):
        """Desenhos por cima dos organismos. As telas filhas podem acrescentar mais coisas."""
        if not self.organismos and self._item_vazio is None:
            self._item_vazio = self.canvas.create_text(
                self.camera.largura_tela / 2, self.camera.altura_tela / 2, text=self.TEXTO_VAZIO,
                fill=self.COR_TEXTO_SUAVE, font=("Segoe UI", 12, "italic"), justify="center",
            )
        elif self.organismos and self._item_vazio is not None:
            self.canvas.delete(self._item_vazio)
            self._item_vazio = None

        self.canvas.delete("aviso_pausa")
        if self.pausado:
            self.canvas.create_text(self.camera.largura_tela / 2, 22, text="⏸  PAUSADO  —  Espaço para continuar",
                                    fill=self.COR_AVISO, font=("Segoe UI", 12, "bold"), tags="aviso_pausa")

    # ---------- minimapa ----------

    def _area_minimapa(self):
        x0 = self.camera.largura_tela - LARGURA_MINIMAPA - 10
        y0 = self.camera.altura_tela - ALTURA_MINIMAPA - 10
        return x0, y0, x0 + LARGURA_MINIMAPA, y0 + ALTURA_MINIMAPA

    def _desenhar_minimapa(self):
        self.canvas.delete("minimapa")
        x0, y0, x1, y1 = self._area_minimapa()
        escala = LARGURA_MINIMAPA / LARGURA_MUNDO
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=self.COR_PAINEL, outline=self.COR_BORDA, width=2,
                                     tags="minimapa")
        for organismo in self.organismos:
            px = x0 + organismo.x * escala
            py = y0 + organismo.y * escala
            r = max(1.5, organismo.raio() * escala * 1.5)
            cor = "#e04848" if organismo.sofreu_interferencia() else cor_do_estagio(organismo.estagio)
            self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=cor, outline="", tags="minimapa")
        vx0 = x0 + self.camera.x * escala
        vy0 = y0 + self.camera.y * escala
        vx1 = vx0 + self.camera.largura_visivel() * escala
        vy1 = vy0 + self.camera.altura_visivel() * escala
        self.canvas.create_rectangle(vx0, vy0, vx1, vy1, outline="#f2f2f2", width=1, tags="minimapa")
        self.canvas.tag_raise("minimapa")

    def _esta_no_minimapa(self, x_tela, y_tela):
        x0, y0, x1, y1 = self._area_minimapa()
        return x0 <= x_tela <= x1 and y0 <= y_tela <= y1

    def _ir_pelo_minimapa(self, x_tela, y_tela):
        x0, y0, _x1, _y1 = self._area_minimapa()
        escala = LARGURA_MINIMAPA / LARGURA_MUNDO
        self.camera.centralizar_em((x_tela - x0) / escala, (y_tela - y0) / escala)
        self._registrar_exploracao()
        self._atualizar_todos_na_tela()
        self._desenhar_minimapa()

    # ---------- loop da simulação ----------

    def _esta_visivel(self):
        return getattr(self.controlador, "tela_visivel", self) is self

    def iniciar_loop(self):
        self.rodando = True
        self._ciclo()

    def parar_loop(self):
        self.rodando = False
        if self._id_proximo_ciclo is not None:
            self.after_cancel(self._id_proximo_ciclo)
            self._id_proximo_ciclo = None

    def alternar_pausa(self):
        self.pausado = not self.pausado
        cor = self.COR_BOTAO_LIGADO if self.pausado else self.COR_BOTAO
        self.botao_pausa.config(text="▶ Continuar" if self.pausado else "⏸ Pausar",
                                bg=cor, fg=self._cor_texto_do_botao(cor))
        if self.pausado:
            self._salvar_posicoes()
        self._atualizar_extras()

    def alternar_velocidade(self):
        """1× → 2× → 4× → 1×. Na velocidade 4×, cada quadro faz 4 passos da simulação."""
        indice = VELOCIDADES.index(self.velocidade)
        self.velocidade = VELOCIDADES[(indice + 1) % len(VELOCIDADES)]
        cor = self.COR_BOTAO_LIGADO if self.velocidade > 1 else self.COR_BOTAO
        self.botao_velocidade.config(text=f"⏩ {self.velocidade}×", bg=cor, fg=self._cor_texto_do_botao(cor))

    def _passo_da_simulacao(self, desenhar):
        self._mover_todos(self._construir_grade_espacial(), desenhar)
        grade = self._construir_grade_espacial()
        self._aplicar_separacao(grade, desenhar)
        self._processar_colisoes(grade)
        grade = self._construir_grade_espacial()
        self._espalhar_infeccao(grade)
        self._efeitos_das_ias(grade)
        self.contador_ciclos += 1
        if self.contador_ciclos % 15 == 0:
            self._salvar_posicoes()
        if self.contador_ciclos % 30 == 0:
            self._checar_conquistas()

    def _ciclo(self):
        if not self.rodando:
            return
        if self._esta_visivel():
            camera_mexeu = self._mover_camera_pelas_teclas()
            if not self.pausado:
                for passo in range(self.velocidade):
                    # só o último passo desenha: assim 4× não pesa 4 vezes mais na tela
                    self._passo_da_simulacao(desenhar=(passo == self.velocidade - 1))
                self._posicionar_fundo()
                self._atualizar_extras()
            elif camera_mexeu:
                self._atualizar_todos_na_tela()
            self.contador_quadros += 1
            if camera_mexeu or self.contador_quadros % 5 == 0:
                self._desenhar_minimapa()
        self._id_proximo_ciclo = self.after(40, self._ciclo)

    def _construir_grade_espacial(self):
        grade = {}
        for indice, organismo in enumerate(self.organismos):
            celula = (int(organismo.x // TAMANHO_CELULA_GRADE), int(organismo.y // TAMANHO_CELULA_GRADE))
            grade.setdefault(celula, []).append(indice)
        return grade

    def _vizinhos_da_celula(self, grade, cx, cy, alcance=1):
        indices_vizinhos = []
        for dx in range(-alcance, alcance + 1):
            for dy in range(-alcance, alcance + 1):
                indices_vizinhos.extend(grade.get((cx + dx, cy + dy), []))
        return indices_vizinhos

    def _vizinho_mais_proximo(self, organismo, grade, distancia_maxima=DISTANCIA_PERSEGUICAO, mesmo_estagio=False):
        cx, cy = int(organismo.x // TAMANHO_CELULA_GRADE), int(organismo.y // TAMANHO_CELULA_GRADE)
        alcance = math.ceil(distancia_maxima / TAMANHO_CELULA_GRADE)
        mais_perto, menor_distancia = None, distancia_maxima
        for j in self._vizinhos_da_celula(grade, cx, cy, alcance):
            outro = self.organismos[j]
            if outro is organismo:
                continue
            if mesmo_estagio and (outro.estagio != organismo.estagio or outro.tipo == "fusao"):
                continue
            distancia = organismo.distancia_para(outro)
            if distancia < menor_distancia:
                mais_perto, menor_distancia = outro, distancia
        return mais_perto

    def _mover_todos(self, grade, desenhar=True):
        # Feromônio (upgrade do Baú): só na placa, onde acontecem as fusões
        alcance_feromonio, forca_feromonio = bau_dados.feromonio() if self.LOCAL == "placa" else (0, 0.0)
        for organismo in self.organismos:
            if organismo.recarga > 0:
                organismo.recarga -= 1
            if organismo.recarga_contagio > 0:
                organismo.recarga_contagio -= 1
            if organismo.recarga_caca > 0:
                organismo.recarga_caca -= 1
            if organismo is not self.arrastando:
                alvo = None
                movimento = modificadores(organismo.comportamento)["movimento"]
                if movimento == "persegue":
                    alvo = self._vizinho_mais_proximo(organismo, grade)
                elif movimento == "caca":
                    alvo = self._presa_mais_proxima(organismo, grade)
                elif movimento == "segue":
                    alvo = self._hospedeiro_de(organismo, grade)
                par = None
                if forca_feromonio > 0 and organismo.tipo != "fusao":
                    par = self._vizinho_mais_proximo(organismo, grade, alcance_feromonio, mesmo_estagio=True)
                organismo.mover(LARGURA_MUNDO, ALTURA_MUNDO, alvo, atracao=par, forca_atracao=forca_feromonio)
            if desenhar:
                organismo.atualizar_no_canvas(self.canvas, self.camera)
            self.comportamentos_vistos.add(organismo.comportamento)

    def _salvar_posicoes(self):
        lote = [(o.id_banco, o.x, o.y) for o in self.organismos if o.id_banco is not None]
        persistencia.atualizar_posicoes_em_lote(lote)

    def _aplicar_separacao(self, grade, desenhar=True):
        for (cx, cy), indices_da_celula in grade.items():
            indices_vizinhos = self._vizinhos_da_celula(grade, cx, cy)
            for i in indices_da_celula:
                organismo_a = self.organismos[i]
                if organismo_a is self.arrastando:
                    continue
                raio_a = organismo_a.raio()
                for j in indices_vizinhos:
                    if j == i:
                        continue
                    organismo_b = self.organismos[j]
                    diferenca_x = organismo_a.x - organismo_b.x
                    diferenca_y = organismo_a.y - organismo_b.y
                    distancia = math.hypot(diferenca_x, diferenca_y)
                    minimo = (raio_a + organismo_b.raio()) * 0.9
                    if distancia <= 0 or distancia >= minimo:
                        continue
                    # O Irritado empurra mais forte quem está perto dele.
                    forca = 0.8 if organismo_b.comportamento == "Irritado" else 0.5
                    sobreposicao = (minimo - distancia) * forca
                    direcao_x, direcao_y = diferenca_x / distancia, diferenca_y / distancia
                    organismo_a.x += direcao_x * sobreposicao
                    organismo_a.y += direcao_y * sobreposicao
                    organismo_a.x = max(MARGEM + raio_a, min(LARGURA_MUNDO - MARGEM - raio_a, organismo_a.x))
                    organismo_a.y = max(MARGEM + raio_a, min(ALTURA_MUNDO - MARGEM - raio_a, organismo_a.y))
                if desenhar:
                    organismo_a.atualizar_no_canvas(self.canvas, self.camera)

    def _par_pode_interagir(self, organismo_a, organismo_b):
        return True

    def _pode_colidir(self, organismo):
        """Quem participa de fusões/reproduções nesta tela (a Área de Mutação troca isso)."""
        return organismo.tipo != "fusao"

    def _processar_colisoes(self, grade):
        usados = set()
        eventos = []

        for (cx, cy), indices_da_celula in grade.items():
            indices_vizinhos = self._vizinhos_da_celula(grade, cx, cy)

            for i in indices_da_celula:
                organismo_a = self.organismos[i]
                if organismo_a.id_banco in usados or not self._pode_colidir(organismo_a):
                    continue
                for j in indices_vizinhos:
                    if j <= i:
                        continue
                    organismo_b = self.organismos[j]
                    if organismo_b.id_banco in usados or not self._pode_colidir(organismo_b):
                        continue
                    if organismo_a.estagio != organismo_b.estagio:
                        continue
                    if not organismo_a.esta_encostando(organismo_b):
                        continue
                    if not self._par_pode_interagir(organismo_a, organismo_b):
                        continue
                    usados.add(organismo_a.id_banco)
                    usados.add(organismo_b.id_banco)
                    eventos.append((organismo_a, organismo_b))
                    break

        for organismo_a, organismo_b in eventos:
            self._resolver_interacao(organismo_a, organismo_b)

    def _resolver_interacao(self, organismo_a, organismo_b):
        pass

    # ---------- infecção ----------

    def _espalhar_infeccao(self, grade):
        """Um Infectado que encosta em outro organismo pode passar a infecção."""
        novos_infectados = []
        for (cx, cy), indices_da_celula in grade.items():
            indices_vizinhos = self._vizinhos_da_celula(grade, cx, cy)
            for i in indices_da_celula:
                doente = self.organismos[i]
                if doente.comportamento != "Infectado" or doente.recarga_contagio > 0:
                    continue
                for j in indices_vizinhos:
                    outro = self.organismos[j]
                    if outro is doente or outro.tipo == "fusao" or outro.comportamento == "Infectado":
                        continue
                    if outro in novos_infectados or not doente.esta_encostando(outro):
                        continue
                    doente.recarga_contagio = RECARGA_CONTAGIO
                    chance = modificadores("Infectado")["chance_contagio"] * bau_dados.fator_contagio()
                    if random.random() < chance and not self._protegido_por_guardiao(outro):
                        novos_infectados.append(outro)
                    break
        for organismo in novos_infectados:
            self._tornar_infectado(organismo)
            persistencia.incrementar_estatistica("contagio_total")
            self._mostrar_evento(f"☣️ Contágio: um {organismo.dados_estagio()['nome']} foi infectado")
        if novos_infectados:
            sons.tocar(sons.SOM_CORRUPCAO)

    def _tornar_infectado(self, organismo):
        organismo.comportamento = "Infectado"
        persistencia.atualizar_comportamento(organismo.id_banco, "Infectado")
        organismo.redesenhar(self.canvas, self.camera)

    # ---------- IAs (liberadas no troféu de Prata) ----------

    def _guardioes(self):
        return [o for o in self.organismos if o.comportamento == "Guardião"]

    def _protegido_por_guardiao(self, organismo):
        """Perto de um Guardião a infecção não pega."""
        return any(g.distancia_para(organismo) < g.raio() * 3 for g in self._guardioes())

    def _presa_mais_proxima(self, predador, grade):
        """O Predador só caça quem é pelo menos 3 estágios menor (e nunca Mutações nem outras IAs)."""
        cx, cy = int(predador.x // TAMANHO_CELULA_GRADE), int(predador.y // TAMANHO_CELULA_GRADE)
        melhor, menor = None, 320
        for j in self._vizinhos_da_celula(grade, cx, cy, 3):
            presa = self.organismos[j]
            if presa.tipo == "fusao" or eh_ia(presa.comportamento) or presa.estagio > predador.estagio - 3:
                continue
            distancia = predador.distancia_para(presa)
            if distancia < menor:
                melhor, menor = presa, distancia
        return melhor

    def _hospedeiro_de(self, simbionte, grade):
        """O Simbionte gruda num organismo de outro estágio; se perder o hospedeiro, procura outro."""
        for organismo in self.organismos:
            if organismo.id_banco == simbionte.hospedeiro_id:
                return organismo
        cx, cy = int(simbionte.x // TAMANHO_CELULA_GRADE), int(simbionte.y // TAMANHO_CELULA_GRADE)
        melhor, menor = None, 420
        for j in self._vizinhos_da_celula(grade, cx, cy, 4):
            outro = self.organismos[j]
            if outro is simbionte or outro.estagio == simbionte.estagio or eh_ia(outro.comportamento):
                continue
            distancia = simbionte.distancia_para(outro)
            if distancia < menor:
                melhor, menor = outro, distancia
        simbionte.hospedeiro_id = melhor.id_banco if melhor else None
        return melhor

    def _efeitos_das_ias(self, grade):
        if not any(eh_ia(o.comportamento) for o in self.organismos):
            return
        devorados = []
        for organismo in self.organismos:
            if organismo.comportamento == "Guardião":
                # empurra para longe quem chega perto (atrapalha as fusões ao redor)
                alcance = organismo.raio() * 2.5
                for outro in self.organismos:
                    if outro is organismo or outro is self.arrastando or outro.comportamento == "Guardião":
                        continue
                    dx, dy = outro.x - organismo.x, outro.y - organismo.y
                    distancia = math.hypot(dx, dy)
                    if 0 < distancia < alcance:
                        outro.x += dx / distancia * 1.5
                        outro.y += dy / distancia * 1.5
            elif organismo.comportamento == "Predador" and organismo.recarga_caca == 0:
                presa = self._presa_mais_proxima(organismo, grade)
                if presa is not None and presa not in devorados and organismo.esta_encostando(presa):
                    devorados.append(presa)
                    organismo.recarga_caca = 250   # ~10 segundos no 1×
        for presa in devorados:
            if presa in self.organismos:
                self._remover_organismo(presa)
                persistencia.incrementar_estatistica("devorados_total")
                self._mostrar_evento(f"🐺 Um Predador devorou um {presa.dados_estagio()['nome']}")

    def _avisar_simbiontes(self, ids_que_sumiram, novo):
        """O hospedeiro se fundiu: o Simbionte que seguia ele sobe +1 estágio e passa a seguir o novo."""
        for simbionte in self.organismos:
            if simbionte.comportamento != "Simbionte" or simbionte.hospedeiro_id not in ids_que_sumiram:
                continue
            simbionte.hospedeiro_id = novo.id_banco
            if simbionte.estagio < TOTAL_ESTAGIOS:
                simbionte.estagio += 1
                persistencia.atualizar_estagio(simbionte.id_banco, simbionte.estagio)
                self._registrar_descoberta(simbionte)
                simbionte.redesenhar(self.canvas, self.camera)
                self._mostrar_evento(f"🤝 O Simbionte subiu junto com o hospedeiro: estágio {simbionte.estagio}")

    # ---------- avisos e conquistas ----------

    def _mostrar_evento(self, texto):
        self.rotulo_evento.config(text=texto)
        # cancela o "apagar" do aviso anterior, senão ele apagaria este aviso novo antes da hora
        if getattr(self, "_id_apagar_evento", None):
            self.after_cancel(self._id_apagar_evento)
        self._id_apagar_evento = self.after(3000, lambda: self.rotulo_evento.config(text=""))

    def _checar_conquistas(self):
        populacao_por_estagio = {}
        for organismo in self.organismos:
            populacao_por_estagio[organismo.estagio] = populacao_por_estagio.get(organismo.estagio, 0) + 1

        contexto = {
            "populacao_atual": persistencia.contar_organismos(),
            "populacao_por_estagio": populacao_por_estagio,
            "comportamentos_vistos": list(self.comportamentos_vistos),
        }
        novas = avaliar_e_desbloquear(contexto)
        for conquista in novas:
            texto = f"🏆 Conquista: {conquista['nome']} (+{conquista.get('ganho', 0)} ⬡)"
            if conquista.get("presente"):
                texto += f" • {conquista['presente']}"
            self._mostrar_evento(texto)
            sons.tocar(sons.SOM_CONQUISTA)
        if novas:
            self._atualizar_membrana()

    # ---------- teclado: setas e pausa ----------

    def _ao_apertar_tecla(self, evento):
        if not self._esta_visivel():
            return
        if evento.keysym in TECLAS_SETAS:
            self._teclas_apertadas.add(evento.keysym)
        elif evento.keysym == "space":
            self.alternar_pausa()
        elif evento.keysym == "Escape" and self._frasco_mirando:
            self._cancelar_mira()

    def _ao_soltar_tecla(self, evento):
        self._teclas_apertadas.discard(evento.keysym)

    def _mover_camera_pelas_teclas(self):
        dx = dy = 0
        for tecla in self._teclas_apertadas:
            passo_x, passo_y = TECLAS_SETAS[tecla]
            dx += passo_x
            dy += passo_y
        if dx == 0 and dy == 0:
            return False
        antes = (self.camera.x, self.camera.y)
        self.camera.mover(dx * VELOCIDADE_CAMERA, dy * VELOCIDADE_CAMERA)
        if (self.camera.x, self.camera.y) == antes:
            return False
        self._registrar_exploracao()
        return True

    def _registrar_exploracao(self):
        if not self._ja_explorou:
            self._ja_explorou = True
            persistencia.incrementar_estatistica("explorar_total")

    # ---------- mouse: arrastar, clicar e mover a câmera ----------

    def _ao_pressionar(self, evento):
        self._inicio_clique = (evento.x, evento.y)
        self._moveu_mouse = False
        if self._esta_no_minimapa(evento.x, evento.y):
            self._arrastando_minimapa = True
            self._ir_pelo_minimapa(evento.x, evento.y)
            return
        if self._frasco_mirando:
            self._inicio_clique = None
            self._usar_frasco(*self.camera.para_mundo(evento.x, evento.y))
            return
        self.arrastando = self._organismo_em(evento.x, evento.y)
        if self.arrastando is None:
            self._arrasto_camera = (evento.x, evento.y, self.camera.x, self.camera.y)

    def _ao_arrastar(self, evento):
        if self._inicio_clique is None:
            return
        if self._arrastando_minimapa:
            self._ir_pelo_minimapa(evento.x, evento.y)
            return
        if not self._moveu_mouse:
            distancia = math.hypot(evento.x - self._inicio_clique[0], evento.y - self._inicio_clique[1])
            if distancia < DISTANCIA_MINIMA_ARRASTO:
                return
            self._moveu_mouse = True

        if self.arrastando is not None:
            organismo = self.arrastando
            x, y = self.camera.para_mundo(evento.x, evento.y)
            raio = organismo.raio()
            organismo.x = max(MARGEM + raio, min(LARGURA_MUNDO - MARGEM - raio, x))
            organismo.y = max(MARGEM + raio, min(ALTURA_MUNDO - MARGEM - raio, y))
            organismo.atualizar_no_canvas(self.canvas, self.camera)
            self._atualizar_extras()
        elif self._arrasto_camera is not None:
            x0, y0, camera_x, camera_y = self._arrasto_camera
            self.camera.x = camera_x - (evento.x - x0) / self.camera.zoom
            self.camera.y = camera_y - (evento.y - y0) / self.camera.zoom
            self.camera.limitar()
            self._registrar_exploracao()
            self._atualizar_todos_na_tela()
            self._desenhar_minimapa()

    def _ao_soltar(self, evento):
        if self._inicio_clique is None:
            return
        organismo = self.arrastando
        if organismo is not None:
            if self._moveu_mouse:
                persistencia.atualizar_posicao(organismo.id_banco, organismo.x, organismo.y)
                persistencia.incrementar_estatistica("arrastar_total")
            else:
                self._ao_clicar_organismo(organismo)
        self.arrastando = None
        self._arrasto_camera = None
        self._arrastando_minimapa = False
        self._inicio_clique = None

    def _organismo_em(self, x_tela, y_tela):
        x, y = self.camera.para_mundo(x_tela, y_tela)
        for organismo in reversed(self.organismos):
            if organismo.contem_ponto(x, y):
                return organismo
        return None

    def _ao_clicar_organismo(self, organismo):
        self._inspecionar(organismo)

    # ---------- zoom ----------

    def _ao_rolar(self, evento):
        passo = PASSO_ZOOM if evento.delta > 0 else -PASSO_ZOOM
        self._mudar_zoom(self.camera.zoom + passo, evento.x, evento.y)

    def _mudar_zoom(self, novo_zoom, x_tela=None, y_tela=None):
        if x_tela is None:
            x_tela, y_tela = self.camera.largura_tela / 2, self.camera.altura_tela / 2
        zoom_antigo = self.camera.zoom
        self.camera.aplicar_zoom(novo_zoom, x_tela, y_tela)
        if self.camera.zoom == zoom_antigo:
            return
        self.rotulo_zoom.config(text=f"{int(round(self.camera.zoom * 100))}%")
        self._redesenhar_tudo_do_zero()
        if self.camera.zoom >= ZOOM_MAXIMO:
            persistencia.incrementar_estatistica("zoom_maximo_total")

    # ---------- menu do botão direito ----------

    def _opcoes_menu(self, organismo):
        return []

    def _ao_clicar_direito(self, evento):
        if self._frasco_mirando:
            self._cancelar_mira()
            return
        organismo = self._organismo_em(evento.x, evento.y)
        if organismo is None:
            return
        dados = modificadores(organismo.comportamento)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=f"{organismo.dados_estagio()['nome']}  •  {dados['emoji']} {organismo.comportamento}",
                         state="disabled")
        menu.add_separator()
        for texto, acao in self._opcoes_menu(organismo):
            menu.add_command(label=texto, command=lambda a=acao, o=organismo: self._executar_acao(a, o))
        try:
            menu.tk_popup(evento.x_root, evento.y_root)
        finally:
            menu.grab_release()

    def _executar_acao(self, acao, organismo):
        if organismo not in self.organismos:
            self._mostrar_evento("Esse organismo não está mais aqui.")
            return
        acao(organismo)

    def _inspecionar(self, organismo):
        dados = organismo.dados_estagio()
        comportamento = modificadores(organismo.comportamento)
        linhas = [
            f"Estágio {organismo.estagio}: {dados['nome']} ({dados['bloco']})",
            f"Comportamento: {comportamento['emoji']} {organismo.comportamento}",
            f"   {comportamento['descricao']}",
            f"Velocidade: {round(organismo.velocidade_efetiva(), 2)}",
            f"Tamanho: {round(organismo.raio() * 2)} px",
        ]
        if organismo.tipo == "fusao":
            linhas.append(f"Origem: fusão manual (receita {organismo.variante})")
        janelas.showinfo("Inspeção de Organismo", "\n".join(linhas))

    def _infectar(self, organismo):
        if organismo.comportamento == "Infectado":
            self._mostrar_evento("Esse organismo já está infectado.")
            return
        if organismo.tipo == "fusao":
            self._mostrar_evento("Mutações de fusão são resistentes à infecção.")
            return
        self._tornar_infectado(organismo)
        persistencia.incrementar_estatistica("infectar_total")
        persistencia.adicionar_entrada_diario(
            f"Infecção induzida pelo cientista em um {organismo.dados_estagio()['nome']}."
        )
        self._mostrar_evento("Organismo infectado ☣️")
        sons.tocar(sons.SOM_CORRUPCAO)

    def _destruir(self, organismo):
        self._remover_organismo(organismo)
        persistencia.incrementar_estatistica("destruir_total")
        self._mostrar_evento("Organismo destruído")

    def _transferir(self, organismo, destino, chave_estatistica):
        persistencia.mover_organismo_para(organismo.id_banco, destino, organismo.x, organismo.y)
        self._remover_organismo(organismo, apagar_do_banco=False)
        persistencia.incrementar_estatistica(chave_estatistica)

    # ---------- Baú: Membrana e frascos ----------

    def _atualizar_membrana(self):
        self.rotulo_membrana.config(text=f"⬡ {bau_dados.saldo()}")

    def _mostrar_ganho(self, x_mundo, y_mundo, quantidade):
        """Um '+3 ⬡' que sobe e some em cima de onde a Membrana foi ganha."""
        self._atualizar_membrana()
        x, y = self.camera.para_tela(x_mundo, y_mundo)
        item = self.canvas.create_text(x, y, text=f"+{quantidade} ⬡", fill=self.COR_AVISO,
                                       font=("Segoe UI", 11, "bold"), tags="ganho")

        def subir(passo=0):
            if passo >= 22 or not self.canvas.find_withtag(item):
                self.canvas.delete(item)
                return
            self.canvas.move(item, 0, -1.5)
            self.after(35, lambda: subir(passo + 1))

        subir()

    def _atualizar_barra_frascos(self):
        for widget in self.barra_frascos.winfo_children():
            widget.destroy()
        tem_algum = False
        for dados in bau_dados.FRASCOS:
            quantidade = bau_dados.quantidade(dados["chave"])
            if quantidade <= 0:
                continue
            tem_algum = True
            mirando = self._frasco_mirando == dados["chave"]
            botao = self._botao(self.barra_frascos, f"{dados['emoji']} {quantidade}",
                                lambda chave=dados["chave"]: self._escolher_frasco(chave),
                                self.COR_BOTAO_LIGADO if mirando else self.COR_BOTAO, padx=6)
            botao.pack(side="left", padx=2)
        if not tem_algum:
            tk.Label(self.barra_frascos, text="🧪 sem frascos — compre no 📦 Baú", fg=self.COR_TEXTO_SUAVE,
                     bg=self.COR_FUNDO, font=("Segoe UI", 9, "italic")).pack(side="left")

    def _escolher_frasco(self, chave):
        if self._frasco_mirando == chave:
            self._cancelar_mira()
            return
        self._frasco_mirando = chave
        self.canvas.config(cursor="crosshair")
        dados = bau_dados.frasco(chave)
        self._mostrar_evento(f"{dados['emoji']} {dados['nome']}: clique no mapa para usar • Esc ou botão direito cancela")
        self._atualizar_barra_frascos()

    def _cancelar_mira(self):
        self._frasco_mirando = None
        self.canvas.config(cursor="")
        self.canvas.delete("mira")
        self._atualizar_barra_frascos()

    def _desenhar_mira(self, evento):
        """Enquanto um frasco está escolhido, um círculo segue o mouse mostrando a área de efeito."""
        self.canvas.delete("mira")
        if not self._frasco_mirando:
            return
        raio = bau_dados.raio_frasco() * self.camera.zoom
        cor = bau_dados.COR_DO_LADO[bau_dados.frasco(self._frasco_mirando)["lado"]]
        self.canvas.create_oval(evento.x - raio, evento.y - raio, evento.x + raio, evento.y + raio,
                                outline=cor, width=2, dash=(6, 4), tags="mira")

    def _organismos_na_area(self, x, y, raio):
        return [o for o in self.organismos if math.hypot(o.x - x, o.y - y) <= raio + o.raio() * 0.5]

    def _efeito_visual(self, x_mundo, y_mundo, cor):
        """Uma onda que se espalha a partir do ponto onde o frasco caiu."""
        x, y = self.camera.para_tela(x_mundo, y_mundo)
        raio_final = bau_dados.raio_frasco() * self.camera.zoom
        item = self.canvas.create_oval(x, y, x, y, outline=cor, width=3, tags="efeito")

        def crescer(passo=1):
            if passo > 12 or not self.canvas.find_withtag(item):
                self.canvas.delete(item)
                return
            r = raio_final * passo / 12
            self.canvas.coords(item, x - r, y - r, x + r, y + r)
            self.after(25, lambda: crescer(passo + 1))

        crescer()

    def _usar_frasco(self, x, y):
        chave = self._frasco_mirando
        dados = bau_dados.frasco(chave)
        if not bau_dados.gastar_frasco(chave):
            self._cancelar_mira()
            return
        raio = bau_dados.raio_frasco()
        resultado = getattr(self, f"_frasco_{chave}")(x, y, raio)
        self._efeito_visual(x, y, bau_dados.COR_DO_LADO[dados["lado"]])
        persistencia.incrementar_estatistica("frascos_usados_total")
        persistencia.adicionar_entrada_diario(f"{dados['nome']} usado: {resultado}")
        self._mostrar_evento(f"{dados['emoji']} {resultado}")
        sons.tocar(sons.SOM_FUSAO)
        if bau_dados.quantidade(chave) <= 0:
            self._cancelar_mira()
        else:
            self._atualizar_barra_frascos()
        self._atualizar_membrana()
        self._atualizar_extras()

    def _cabe_mais(self, quantidade=1):
        return persistencia.contar_organismos() + quantidade <= bau_dados.limite_populacao()

    # Cada frasco devolve um texto curto dizendo o que aconteceu.

    def _frasco_corrompido(self, x, y, raio):
        if not self._cabe_mais():
            return "a colônia está no limite, nada surgiu."
        self._criar_e_mostrar(bau_dados.estagio_gerado(), x, y, gerar_habilidades_iniciais("Infectado"))
        return "um organismo Infectado surgiu na placa."

    def _frasco_nutritivo(self, x, y, raio):
        criados = 0
        for _ in range(3):
            if not self._cabe_mais():
                break
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(0, raio * 0.6)
            self._criar_e_mostrar(bau_dados.estagio_gerado(), x + math.cos(angulo) * distancia,
                                  y + math.sin(angulo) * distancia)
            criados += 1
        return f"{criados} organismo(s) novo(s) do estágio {bau_dados.estagio_gerado()}."

    def _frasco_antidoto(self, x, y, raio):
        curados = 0
        for organismo in self._organismos_na_area(x, y, raio):
            if organismo.comportamento == "Infectado":
                organismo.comportamento = escolher_comportamento_aleatorio()
                persistencia.atualizar_comportamento(organismo.id_banco, organismo.comportamento)
                organismo.redesenhar(self.canvas, self.camera)
                curados += 1
        return f"{curados} organismo(s) curado(s)."

    def _frasco_antibiotico(self, x, y, raio):
        mortos = self._organismos_na_area(x, y, raio)
        for organismo in mortos:
            self._remover_organismo(organismo)
        return f"{len(mortos)} organismo(s) eliminado(s)."

    def _frasco_reverso(self, x, y, raio):
        area = self._organismos_na_area(x, y, raio)
        if random.random() < bau_dados.chance_boa_reverso():
            alvos, lado = [o for o in area if o.comportamento == "Infectado"], "os RUINS"
        else:
            alvos, lado = [o for o in area if o.comportamento != "Infectado"], "os BONS"
        for organismo in alvos:
            self._remover_organismo(organismo)
        return f"o Reverso eliminou {lado}: {len(alvos)} organismo(s)."

    def _frasco_evolutivo(self, x, y, raio):
        evoluidos = 0
        for organismo in self._organismos_na_area(x, y, raio):
            if organismo.estagio >= TOTAL_ESTAGIOS:
                continue
            organismo.estagio += 1
            persistencia.atualizar_estagio(organismo.id_banco, organismo.estagio)
            ganho = self._registrar_descoberta(organismo)
            if ganho:
                self._mostrar_ganho(organismo.x, organismo.y - organismo.raio(), ganho)
            organismo.redesenhar(self.canvas, self.camera)
            evoluidos += 1
        return f"{evoluidos} organismo(s) evoluíram +1 estágio."

    # ---- frascos vilões do troféu de Bronze ----

    def _frasco_praga(self, x, y, raio):
        infectados = 0
        for organismo in self._organismos_na_area(x, y, raio):
            if organismo.tipo != "fusao" and organismo.comportamento != "Infectado":
                self._tornar_infectado(organismo)
                infectados += 1
        return f"a Praga infectou {infectados} organismo(s)."

    def _frasco_instavel(self, x, y, raio):
        regrediram = 0
        for organismo in self._organismos_na_area(x, y, raio):
            if organismo.estagio > 1:
                organismo.estagio -= 1
                persistencia.atualizar_estagio(organismo.id_banco, organismo.estagio)
                ganho = self._registrar_descoberta(organismo)
                if ganho:
                    self._mostrar_ganho(organismo.x, organismo.y - organismo.raio(), ganho)
                organismo.redesenhar(self.canvas, self.camera)
                regrediram += 1
        return f"{regrediram} organismo(s) regrediram 1 estágio."

    def _frasco_caos(self, x, y, raio):
        espalhados = 0
        for organismo in self._organismos_na_area(x, y, raio):
            margem = organismo.raio() + MARGEM
            organismo.x = random.uniform(margem, LARGURA_MUNDO - margem)
            organismo.y = random.uniform(margem, ALTURA_MUNDO - margem)
            if organismo.tipo != "fusao" and eh_natural(organismo.comportamento):
                organismo.comportamento = escolher_comportamento_aleatorio()
                persistencia.atualizar_comportamento(organismo.id_banco, organismo.comportamento)
                organismo.redesenhar(self.canvas, self.camera)
            espalhados += 1
        self._salvar_posicoes()
        return f"o Caos espalhou {espalhados} organismo(s) pelo mapa."

    # ---------- troca de tela ----------

    def atualizar_ao_exibir(self):
        self._teclas_apertadas.clear()
        self._salvar_posicoes()
        self.camera.zoom_maximo = bau_dados.zoom_maximo()
        self._cancelar_mira()
        self._atualizar_membrana()
        self._carregar_organismos()
