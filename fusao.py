import random

import persistencia
import sons
import tema
import bau_dados
from comportamento import modificadores
from evolucao_dados import nome_do_estagio, TOTAL_ESTAGIOS
from habilidades import herdar_habilidades
from placa import PlacaBase

RECARGA_APOS_REPRODUZIR = 150
RECARGA_APOS_TENTATIVA = 25


def _habilidades_de(organismo):
    return {
        "velocidade_mod": organismo.velocidade_mod,
        "tamanho_mod": organismo.tamanho_mod,
        "comportamento": organismo.comportamento,
    }


class TelaFusao(PlacaBase):
    """⚗️ Área de Fusão: aqui os iguais que se encostam se REPRODUZEM (não se fundem).

    A fusão manual (receitas -> Mutação) mudou para a 🧬 Área de Mutação, aberta pelo troféu de Madeira.
    """

    LOCAL = "fusao"
    TITULO = "⚗️ Área de Fusão"
    DICA = ("Iguais que se encostam aqui se reproduzem  •  Leve os filhotes de volta à placa para fundir  •  "
            "Setas, Espaço, F11 e minimapa também funcionam")
    TEXTO_VAZIO = ("Área de Fusão vazia nesta região.\nNa Simulação, clique com o botão direito num organismo "
                   "e escolha “Coletar para a Área de Fusão”.")
    NOME_FUNDO = "fusao"
    # clima "câmara de fusão": grafite com luzes âmbar (tema.FUSAO)
    COR_FUNDO = tema.FUSAO["fundo"]
    COR_CANVAS = tema.FUSAO["fundo"]
    COR_GRADE = tema.FUSAO["grade"]
    COR_BORDA = tema.FUSAO["borda"]
    COR_TEXTO = tema.FUSAO["texto"]
    COR_TEXTO_SUAVE = tema.FUSAO["texto_suave"]
    COR_PAINEL = tema.FUSAO["painel"]
    COR_BOTAO = tema.FUSAO["painel_claro"]
    COR_BOTAO_LIGADO = tema.FUSAO["destaque"]
    COR_TEXTO_BOTAO = tema.FUSAO["texto_no_destaque"]
    COR_AVISO = tema.FUSAO["aviso"]

    def _montar_botoes(self, rodape):
        self._botao(rodape, "↩️ Soltar todos na placa", self._soltar_todos, self.COR_BOTAO_LIGADO,
                    padx=10).pack(side="left")

    # ---------- reprodução (só acontece aqui) ----------

    def _par_pode_interagir(self, organismo_a, organismo_b):
        return organismo_a.recarga == 0 and organismo_b.recarga == 0

    def _resolver_interacao(self, organismo_a, organismo_b):
        chance_a = modificadores(organismo_a.comportamento)["chance_reproducao"]
        chance_b = modificadores(organismo_b.comportamento)["chance_reproducao"]
        if chance_a == 0 or chance_b == 0:
            return  # Infectado, Mutação e Predador não se reproduzem
        # Catalisador (Baú) soma chance; cada troféu tira um pouco (o jogo fica mais difícil a cada ciclo)
        chance_reproducao = (chance_a + chance_b) / 2 + bau_dados.bonus_reproducao() - bau_dados.penalidade_reproducao()
        chance_reproducao = max(0.05, min(0.95, chance_reproducao))
        espera = round(RECARGA_APOS_REPRODUZIR * bau_dados.fator_recarga())

        if random.random() >= chance_reproducao:
            organismo_a.recarga = organismo_b.recarga = RECARGA_APOS_TENTATIVA
            return

        organismo_a.recarga = organismo_b.recarga = espera
        if persistencia.contar_organismos() >= bau_dados.limite_populacao():
            self._mostrar_evento("Colônia no limite — reprodução pausada (🧫 Placa Maior no Baú aumenta o limite)")
            return

        habilidades_novas = herdar_habilidades(_habilidades_de(organismo_a), _habilidades_de(organismo_b))
        estagio = organismo_a.estagio
        if estagio < TOTAL_ESTAGIOS and random.random() < bau_dados.chance_heranca_forte():
            estagio += 1   # Herança Forte (Baú, troféu de Ouro): às vezes o filhote nasce 1 estágio acima
        novo = self._criar_e_mostrar(
            estagio,
            x=(organismo_a.x + organismo_b.x) / 2 + random.uniform(-15, 15),
            y=(organismo_a.y + organismo_b.y) / 2 + random.uniform(-15, 15),
            habilidades=habilidades_novas,
        )
        novo.recarga = espera
        persistencia.incrementar_estatistica("reproducao_total")
        ganho = bau_dados.ganhar(bau_dados.GANHO_REPRODUCAO)
        self._mostrar_ganho(novo.x, novo.y - novo.raio(), ganho)
        self._mostrar_evento(f"Reprodução: novo {nome_do_estagio(estagio)}")
        sons.tocar(sons.SOM_REPRODUCAO)

    # ---------- menu e devolução para a placa ----------

    def _opcoes_menu(self, organismo):
        return [
            ("🔍  Inspecionar", self._inspecionar),
            ("↩️  Soltar na placa", self._soltar),
            ("☣️  Infectar", self._infectar),
            ("💥  Destruir", self._destruir),
        ]

    def _soltar(self, organismo):
        self._transferir(organismo, "placa", "soltar_total")
        self._mostrar_evento(f"{organismo.dados_estagio()['nome']} devolvido à placa ↩️")

    def _soltar_todos(self):
        if not self.organismos:
            return
        quantidade = len(self.organismos)
        for organismo in list(self.organismos):
            self._transferir(organismo, "placa", "soltar_total")
        self._mostrar_evento(f"{quantidade} organismos devolvidos à placa ↩️")
