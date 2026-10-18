import tkinter as tk
import janelas
import random

import persistencia
import recursos
import sons
import tema
import bau_dados
from habilidades import herdar_habilidades, gerar_habilidades_iniciais
from evolucao_dados import TOTAL_ESTAGIOS, nome_do_estagio
from placa import PlacaBase

ORGANISMOS_DA_CONTA_NOVA = 6


class TelaSimulacao(PlacaBase):
    LOCAL = "placa"
    TITULO = "Colônia — Placa de Cultura"
    DICA = ("Arraste com o mouse  •  Botão direito: menu  •  Roda: zoom  •  Setas: andar pelo mapa  •  "
            "Espaço: pausar  •  F11: tela cheia  •  Clique no minimapa para ir até lá")
    TEXTO_VAZIO = "Placa vazia nesta região.\nClique em “+ Organismo” ou use o minimapa para procurar."

    def _montar_botoes(self, rodape):
        self._botao(rodape, f"+ Organismo ({bau_dados.CUSTO_ORGANISMO} ⬡)", self._adicionar_organismo_aleatorio,
                    self.COR_BOTAO_LIGADO, padx=10).pack(side="left")
        # Nasce: um botão com o desenho de cada estágio; a Cultura Avançada (Baú) destranca os mais altos
        self.area_nasce = tk.Frame(rodape, bg=self.COR_FUNDO)
        self.area_nasce.pack(side="left", padx=(8, 0))
        tk.Label(self.area_nasce, text="Nasce:", fg=tema.LAB["texto_suave"], bg=self.COR_FUNDO,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.botoes_nasce = {}
        self._imagem_vazia = tk.PhotoImage(width=1, height=1)   # com imagem, width/height ficam em pixels
        for estagio in range(1, bau_dados.estagio_maximo_possivel() + 1):
            botao = tk.Button(self.area_nasce, relief="flat", takefocus=0, bd=0, width=30, height=30,
                              image=self._imagem_vazia, compound="center",
                              highlightthickness=2, command=lambda e=estagio: self._escolher_nascimento(e))
            botao.pack(side="left", padx=2)
            botao.bind("<Enter>", lambda evento, e=estagio: self._dica_nascimento(e))
            self.botoes_nasce[estagio] = botao
        self._atualizar_botoes_nasce()
        self._botao(rodape, "Limpar Placa", self._confirmar_limpar, tema.LAB["perigo"],
                    padx=10).pack(side="left", padx=6)

    def _carregar_inicial(self):
        linhas = persistencia.listar_organismos()

        if len(linhas) > bau_dados.limite_populacao():
            quantidade_antes = len(linhas)
            removidos = persistencia.limitar_populacao(bau_dados.limite_populacao())
            persistencia.adicionar_entrada_diario(
                f"Superpopulação detectada ({quantidade_antes} organismos) — colônia podada "
                f"automaticamente para {bau_dados.limite_populacao()} (recursos limitados do prato)."
            )
            self.after(500, lambda: janelas.showwarning(
                "Colônia superpopulada",
                f"Sua colônia tinha {quantidade_antes} organismos e foi reduzida para {bau_dados.limite_populacao()}. "
                f"({removidos} organismos removidos — os mais antigos.)"
            ))

        conta_nova = (persistencia.contar_organismos() == 0 and persistencia.obter_estatistica("merge_total") == 0
                      and bau_dados.trofeus() == 0)
        if conta_nova:
            bau_dados.ganhar(bau_dados.MEMBRANA_INICIAL)
            persistencia.adicionar_entrada_diario(
                "Início dos experimentos. Organismos iguais que se encostam na placa se fundem e evoluem. "
                "Veja o Manual → Como jogar."
            )
            self._semear_organismos_iniciais()
        else:
            self._carregar_organismos()

    def _semear_organismos_iniciais(self):
        """Começo de conta (ou de ciclo novo): alguns organismos calmos do estágio 1, no meio do mapa."""
        for _ in range(ORGANISMOS_DA_CONTA_NOVA):
            self._criar_organismo_no_banco(estagio=1, habilidades=gerar_habilidades_iniciais("Calmo"))
        self._carregar_organismos()
        if self.organismos:
            self._marcar_especie_nova(self.organismos[0])  # o ❓ da primeira espécie descoberta

    def comecar_ciclo_novo(self):
        """Chamado pelo main.py depois de um troféu: a placa recomeça do zero."""
        self.camera.centralizar_em(self.camera.largura_mundo / 2, self.camera.altura_mundo / 2)
        self._especies_novas.clear()
        self._semear_organismos_iniciais()
        self._atualizar_membrana()
        self._atualizar_barra_frascos()

    def _adicionar_organismo_aleatorio(self):
        if persistencia.contar_organismos() >= bau_dados.limite_populacao():
            self._mostrar_evento("Colônia no limite — não cabe mais ninguém")
            return
        sem_saida = bau_dados.saldo() < bau_dados.CUSTO_ORGANISMO and not self.organismos
        if not sem_saida:
            if not persistencia.gastar_membrana(bau_dados.CUSTO_ORGANISMO):
                self._mostrar_evento("Sem Membrana! Clique num organismo da placa para ganhar +1 ⬡")
                return
        # Cultura Avançada (Baú) libera estágios mais altos; o botão 🧫 Nasce escolhe qual
        self._criar_e_mostrar(estagio=bau_dados.estagio_gerado())
        self._atualizar_membrana()
        if sem_saida:
            self._mostrar_evento("Este saiu de graça: sem Membrana e com a placa vazia 🤝")

    def _atualizar_botoes_nasce(self):
        maximo = bau_dados.estagio_maximo_de_nascimento()
        escolhido = bau_dados.estagio_gerado()
        for estagio, botao in self.botoes_nasce.items():
            if estagio <= maximo:
                # liberado: mostra o desenho; o escolhido ganha a borda acesa
                imagem = recursos.imagem_organismo_redimensionada(estagio, 26)
                aceso = estagio == escolhido
                botao.config(image=imagem or self._imagem_vazia, text="" if imagem else str(estagio), state="normal",
                             cursor="hand2", bg=tema.LAB["destaque"] if aceso else tema.LAB["painel"],
                             highlightbackground=tema.LAB["destaque_claro"] if aceso else tema.LAB["borda"])
                botao.image = imagem
            else:
                # ainda trancado: cadeado (a Cultura Avançada do Baú libera)
                botao.config(image=self._imagem_vazia, text="🔒", state="normal", cursor="arrow", bg=tema.LAB["painel"],
                             fg=tema.LAB["texto_suave"], highlightbackground=tema.LAB["grade"])
                botao.image = None

    def _escolher_nascimento(self, estagio):
        if estagio > bau_dados.estagio_maximo_de_nascimento():
            self._mostrar_evento("🔒 Trancado — compre a 🧬 Cultura Avançada no Baú para liberar este estágio")
            return
        bau_dados.escolher_estagio_de_nascimento(estagio)
        self._atualizar_botoes_nasce()
        sons.tocar(sons.SOM_CLIQUE)
        self._mostrar_evento(f"Organismos novos vão nascer no estágio {estagio}: {nome_do_estagio(estagio)}")

    def _dica_nascimento(self, estagio):
        if estagio <= bau_dados.estagio_maximo_de_nascimento():
            self._mostrar_evento(f"Nascer no estágio {estagio}: {nome_do_estagio(estagio)}")
        else:
            self._mostrar_evento(f"🔒 Estágio {estagio} — libere com a 🧬 Cultura Avançada (Baú)")

    def atualizar_ao_exibir(self):
        super().atualizar_ao_exibir()
        self._atualizar_botoes_nasce()   # pode ter comprado a Cultura Avançada no Baú

    def _ao_clicar_organismo(self, organismo):
        # sem Membrana nenhuma, clicar num organismo "brota" +1 ⬡ (assim o jogador nunca fica preso)
        if bau_dados.saldo() < bau_dados.CUSTO_ORGANISMO:
            ganho = bau_dados.ganhar(bau_dados.GANHO_CLIQUE_SEM_SALDO)
            self._mostrar_ganho(organismo.x, organismo.y - organismo.raio(), ganho)
            sons.tocar(sons.SOM_CLIQUE)
            return
        self._inspecionar(organismo)

    def _confirmar_limpar(self):
        if janelas.askyesno("Limpar Placa", "Remover todos os organismos da placa?\n"
                                            "(Os que estão na Área de Fusão e na de Mutação continuam lá.)"):
            persistencia.limpar_colonia("placa")
            for organismo in self.organismos:
                organismo.remover_do_canvas(self.canvas)
            self.organismos = []
            self._atualizar_rotulo_populacao()
            self._atualizar_extras()

    def _resolver_interacao(self, organismo_a, organismo_b):
        """Na placa só acontece fusão espontânea (merge): dois iguais viram um do estágio seguinte."""
        if organismo_a.estagio >= TOTAL_ESTAGIOS:
            return

        habilidades_a = {
            "velocidade_mod": organismo_a.velocidade_mod,
            "tamanho_mod": organismo_a.tamanho_mod,
            "comportamento": organismo_a.comportamento,
        }
        habilidades_b = {
            "velocidade_mod": organismo_b.velocidade_mod,
            "tamanho_mod": organismo_b.tamanho_mod,
            "comportamento": organismo_b.comportamento,
        }
        habilidades_novas = herdar_habilidades(habilidades_a, habilidades_b)

        novo_estagio = organismo_a.estagio + 1
        x = (organismo_a.x + organismo_b.x) / 2 + random.uniform(-10, 10)
        y = (organismo_a.y + organismo_b.y) / 2 + random.uniform(-10, 10)
        ids_que_sumiram = {organismo_a.id_banco, organismo_b.id_banco}
        self._remover_organismo(organismo_a)
        self._remover_organismo(organismo_b)
        novo = self._criar_e_mostrar(novo_estagio, x, y, habilidades_novas)
        persistencia.incrementar_estatistica("merge_total")
        self._avisar_simbiontes(ids_que_sumiram, novo)

        # unir dois organismos iguais rende Membrana: 3 + o nível da Eclosão Rica
        ganho = bau_dados.ganhar(bau_dados.recompensa_fusao())
        self._mostrar_ganho(x, y - novo.raio(), ganho)
        if not novo.ganho_descoberta:
            self._mostrar_evento(f"Fusão espontânea: {nome_do_estagio(novo_estagio)} (+{ganho} ⬡)")
        sons.tocar(sons.SOM_MERGE)

    def _opcoes_menu(self, organismo):
        opcoes = [
            ("🔍  Inspecionar", self._inspecionar),
            ("🧺  Coletar para a Área de Fusão", self._coletar),
        ]
        if bau_dados.mutacao_liberada():
            opcoes.append(("🧬  Coletar para a Área de Mutação", self._coletar_mutacao))
        opcoes += [
            ("☣️  Infectar", self._infectar),
            ("💥  Destruir", self._destruir),
        ]
        return opcoes

    def _coletar(self, organismo):
        self._transferir(organismo, "fusao", "coletar_total")
        self._mostrar_evento(f"{organismo.dados_estagio()['nome']} coletado para a Área de Fusão 🧺")

    def _coletar_mutacao(self, organismo):
        self._transferir(organismo, "mutacao", "coletar_total")
        self._mostrar_evento(f"{organismo.dados_estagio()['nome']} levado para a Área de Mutação 🧬")
