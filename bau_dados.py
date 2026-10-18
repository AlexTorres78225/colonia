"""Catálogo do Baú: upgrades, frascos, troféus e a economia da Membrana ⬡.

(O símbolo da Membrana é ⬡ — o emoji 🫧 aparecia como um quadradinho no Windows 10.)

Upgrades -> permanentes, sempre bons, até 3 níveis, cada nível mais caro.
Frascos  -> de uso único; o jogador escolhe ser herói ou vilão.
Troféus  -> cada vez que a colônia chega ao último estágio, ganha um troféu e começa um ciclo novo.
            Cada troféu libera UMA coisa nova (requer_trofeu nos itens).
"""
import random

import persistencia
from comportamento import LISTA_IAS, CHANCE_DE_NASCER_IA

NIVEL_MAXIMO = 3

# Economia
MEMBRANA_INICIAL = 50         # conta nova e cada ciclo novo começam com isso
PARTE_DA_MEMBRANA_QUE_FICA = 0.2   # ao ganhar um troféu, 20% da Membrana que sobrou vai para o ciclo novo
CUSTO_ORGANISMO = 1           # o "+ Organismo" custa 1 ⬡ (grátis se estiver sem ⬡ e com a placa vazia)
GANHO_FUSAO_BASE = 3          # unir dois organismos iguais (+1 por nível da Eclosão Rica)
GANHO_ESPECIE_NOVA = 20       # + Bônus de Descoberta
GANHO_CONQUISTA = 15
GANHO_REPRODUCAO = 1
GANHO_CLIQUE_SEM_SALDO = 1    # sem Membrana nenhuma, clicar num organismo "brota" +1 ⬡
AUMENTO_EVOLUTIVO = 20        # cada Evolutivo comprado no ciclo fica 20 ⬡ mais caro

RAIO_FRASCO_BASE = 110        # área de efeito dos frascos (em pixels do mapa, sem upgrade)

# ---------- troféus ----------
TROFEUS = [
    {"chave": "madeira", "emoji": "🌲", "nome": "Madeira", "cor": "#a0703c",
     "libera": "🧬 Área de Mutação (receitas e Mutações que pulam +2 estágios)"},
    {"chave": "bronze", "emoji": "🥉", "nome": "Bronze", "cor": "#cd7f32",
     "libera": "😈 3 frascos vilões novos no Baú (Praga, Instável e Caos)"},
    {"chave": "prata", "emoji": "🥈", "nome": "Prata", "cor": "#c0c8d0",
     "libera": "🤖 3 IAs: Guardião, Predador e Simbionte começam a nascer"},
    {"chave": "ouro", "emoji": "🥇", "nome": "Ouro", "cor": "#f2c94c",
     "libera": "⬆️ 3 upgrades novos no Baú (Imunidade, Reembolso e Herança Forte)"},
    {"chave": "diamante", "emoji": "💎", "nome": "Diamante", "cor": "#7fe7ff",
     "libera": "👑 Título de Mestre da Colônia — o jogo está completo!"},
]
TOTAL_TROFEUS = len(TROFEUS)
NOME_DO_TROFEU_REQUERIDO = {i + 1: t["nome"] for i, t in enumerate(TROFEUS)}

# "valores" tem 4 posições: nível 0 (sem comprar), 1, 2 e 3.
UPGRADES = [
    {"chave": "eclosao_rica", "emoji": "💰", "nome": "Eclosão Rica",
     "descricao": "Membrana ganha a cada fusão.",
     "valores": [3, 4, 5, 6], "precos": [30, 60, 100], "formato": "{} ⬡ por fusão"},
    {"chave": "cultura_avancada", "emoji": "🧬", "nome": "Cultura Avançada",
     "descricao": "Libera organismos novos mais evoluídos (escolha qual nasce na Simulação, em “Nasce”).",
     "valores": [1, 2, 3, 4], "precos": [40, 80, 130], "formato": "nasce até o estágio {}"},
    {"chave": "alcance", "emoji": "🎯", "nome": "Alcance dos Frascos",
     "descricao": "Aumenta a área de efeito dos frascos.",
     "valores": [1.0, 1.3, 1.6, 2.0], "precos": [50, 100, 160], "formato": "área ×{}"},
    {"chave": "catalisador", "emoji": "⚗️", "nome": "Catalisador",
     "descricao": "Mais chance de reprodução na Área de Fusão.",
     "valores": [0, 10, 20, 30], "precos": [60, 120, 200], "formato": "+{}% de chance"},
    {"chave": "lente", "emoji": "🔭", "nome": "Lente Potente",
     "descricao": "Aumenta o zoom máximo.",
     "valores": [300, 350, 400, 500], "precos": [75, 150, 250], "formato": "zoom até {}%"},
    {"chave": "recarga", "emoji": "⏳", "nome": "Recarga Rápida",
     "descricao": "Menos espera entre um filhote e outro.",
     "valores": [0, 20, 40, 60], "precos": [90, 180, 300], "formato": "−{}% de espera"},
    {"chave": "placa_maior", "emoji": "🧫", "nome": "Placa Maior",
     "descricao": "Aumenta o limite de população da colônia.",
     "valores": [300, 400, 500, 600], "precos": [110, 220, 360], "formato": "até {} organismos"},
    {"chave": "feromonio", "emoji": "🧲", "nome": "Feromônio",
     "descricao": "Iguais se atraem na placa e se fundem mais rápido.",
     "valores": [0, 1, 2, 3], "precos": [130, 260, 420],
     "formato_lista": ["sem atração", "atração fraca", "atração média", "atração forte"]},
    {"chave": "descoberta", "emoji": "🔍", "nome": "Bônus de Descoberta",
     "descricao": "Membrana extra ao descobrir uma espécie nova.",
     "valores": [0, 10, 20, 30], "precos": [160, 320, 500], "formato": "+{} ⬡ por espécie"},
    {"chave": "sorte", "emoji": "🍀", "nome": "Sorte de Laboratório",
     "descricao": "Melhora a chance boa do Frasco Reverso.",
     "valores": [50, 60, 70, 80], "precos": [200, 400, 650], "formato": "{}% de chance boa"},
    # ---- liberados no troféu de Ouro ----
    {"chave": "imunidade", "emoji": "🛡", "nome": "Imunidade", "requer_trofeu": 4,
     "descricao": "Menos chance de a infecção passar adiante.",
     "valores": [0, 25, 50, 75], "precos": [250, 500, 800], "formato": "−{}% de contágio"},
    {"chave": "reembolso", "emoji": "💸", "nome": "Reembolso", "requer_trofeu": 4,
     "descricao": "Chance de ganhar um frasco a mais de graça ao comprar.",
     "valores": [0, 15, 30, 45], "precos": [300, 600, 900], "formato": "{}% de frasco grátis"},
    {"chave": "heranca", "emoji": "🧪", "nome": "Herança Forte", "requer_trofeu": 4,
     "descricao": "Filhotes da Área de Fusão às vezes nascem 1 estágio acima.",
     "valores": [0, 10, 20, 30], "precos": [400, 800, 1200], "formato": "{}% nasce +1 estágio"},
]

# Feromônio por nível: (distância que o organismo "sente" o par, força da atração)
FEROMONIO = [(0, 0.0), (160, 0.05), (260, 0.09), (380, 0.15)]

FRASCOS = [
    {"chave": "corrompido", "emoji": "☣️", "nome": "Frasco Corrompido", "lado": "vilão", "preco": 15,
     "descricao": "Cria +1 organismo Infectado onde você clicar."},
    {"chave": "nutritivo", "emoji": "💧", "nome": "Frasco Nutritivo", "lado": "herói", "preco": 25,
     "descricao": "Cria 3 organismos ali, no estágio da Cultura Avançada."},
    {"chave": "antidoto", "emoji": "💉", "nome": "Frasco Antídoto", "lado": "herói", "preco": 30,
     "descricao": "Cura todos os Infectados da área."},
    {"chave": "antibiotico", "emoji": "💀", "nome": "Frasco Antibiótico", "lado": "vilão", "preco": 40,
     "descricao": "Mata todos os organismos da área, bons e ruins."},
    {"chave": "reverso", "emoji": "🔁", "nome": "Frasco Reverso", "lado": "aposta", "preco": 45,
     "descricao": "Elimina os ruins da área… ou os bons! A Sorte melhora a chance."},
    {"chave": "evolutivo", "emoji": "✨", "nome": "Frasco Evolutivo", "lado": "herói", "preco": 120,
     "descricao": "+1 estágio para todos da área. Fica +20 ⬡ mais caro a cada compra no ciclo."},
    # ---- liberados no troféu de Bronze ----
    {"chave": "praga", "emoji": "🦠", "nome": "Frasco Praga", "lado": "vilão", "preco": 50, "requer_trofeu": 2,
     "descricao": "Infecta todos os organismos da área."},
    {"chave": "instavel", "emoji": "🧨", "nome": "Frasco Instável", "lado": "vilão", "preco": 35, "requer_trofeu": 2,
     "descricao": "Todos da área regridem 1 estágio."},
    {"chave": "caos", "emoji": "🌪", "nome": "Frasco Caos", "lado": "vilão", "preco": 30, "requer_trofeu": 2,
     "descricao": "Espalha os organismos da área pelo mapa e embaralha os comportamentos."},
]

COR_DO_LADO = {"herói": "#4fc38a", "vilão": "#e05a5a", "aposta": "#f2c94c"}

# Conquistas que dão 1 nível de upgrade de presente
PRESENTES_DE_CONQUISTA = {
    "arrastar_total_25": "feromonio",
    "colecionador_total": "cultura_avancada",
    "brincar_de_deus": "sorte",
}

_UPGRADE_POR_CHAVE = {u["chave"]: u for u in UPGRADES}
_FRASCO_POR_CHAVE = {f["chave"]: f for f in FRASCOS}


# ---------- troféus e ciclos ----------

def trofeus():
    return persistencia.obter_estatistica("trofeus")


def ciclo_atual():
    return min(trofeus() + 1, TOTAL_TROFEUS)


def liberado(dados):
    """Upgrade/frasco liberado? (os que têm 'requer_trofeu' esperam o troféu certo)"""
    return trofeus() >= dados.get("requer_trofeu", 0)


def texto_bloqueio(dados):
    return f"🔒 Requer o troféu de {NOME_DO_TROFEU_REQUERIDO[dados['requer_trofeu']]}"


def mutacao_liberada():
    return trofeus() >= 1


def ias_liberadas():
    return trofeus() >= 3


def penalidade_reproducao():
    """A cada troféu o jogo fica um pouco mais difícil: -5% de chance de reprodução (até -20%)."""
    return min(0.20, 0.05 * trofeus())


def comportamento_de_nascimento(comportamento):
    """Depois do troféu de Prata, às vezes quem nasce é uma IA."""
    if ias_liberadas() and random.random() < CHANCE_DE_NASCER_IA:
        return random.choice(LISTA_IAS)
    return comportamento


# ---------- upgrades ----------

def upgrade(chave):
    return _UPGRADE_POR_CHAVE[chave]


def nivel(chave):
    return persistencia.obter_nivel_upgrade(chave)


def valor(chave):
    """O efeito do upgrade no nível atual (ex.: Eclosão Rica no nível 2 -> 5 Membranas)."""
    return upgrade(chave)["valores"][nivel(chave)]


def texto_do_nivel(chave, nivel_desejado):
    dados = upgrade(chave)
    if "formato_lista" in dados:
        return dados["formato_lista"][nivel_desejado]
    return dados["formato"].format(dados["valores"][nivel_desejado])


def preco_do_proximo_nivel(chave):
    atual = nivel(chave)
    if atual >= NIVEL_MAXIMO:
        return None
    return upgrade(chave)["precos"][atual]


def comprar_upgrade(chave):
    dados = upgrade(chave)
    if not liberado(dados):
        return False, texto_bloqueio(dados)
    preco = preco_do_proximo_nivel(chave)
    if preco is None:
        return False, "Esse upgrade já está no nível máximo."
    if not persistencia.gastar_membrana(preco):
        return False, f"Membrana insuficiente: precisa de {preco} ⬡."
    persistencia.definir_nivel_upgrade(chave, nivel(chave) + 1)
    persistencia.adicionar_entrada_diario(f"Upgrade comprado no Baú: {dados['nome']} nível {nivel(chave)}.")
    return True, f"{dados['emoji']} {dados['nome']} subiu para o nível {nivel(chave)}!"


def dar_presente(chave_conquista):
    """Algumas conquistas dão 1 nível de upgrade grátis. Devolve o texto do presente (ou None)."""
    chave = PRESENTES_DE_CONQUISTA.get(chave_conquista)
    if chave is None or nivel(chave) >= NIVEL_MAXIMO:
        return None
    persistencia.definir_nivel_upgrade(chave, nivel(chave) + 1)
    dados = upgrade(chave)
    return f"presente: {dados['emoji']} {dados['nome']} nível {nivel(chave)}"


# ---------- frascos ----------

def frasco(chave):
    return _FRASCO_POR_CHAVE[chave]


def quantidade(chave):
    return persistencia.obter_quantidade_item(chave)


def preco_frasco(chave):
    preco = frasco(chave)["preco"]
    if chave == "evolutivo":
        preco += AUMENTO_EVOLUTIVO * persistencia.obter_estatistica("evolutivos_comprados_ciclo")
    return preco


def comprar_frasco(chave):
    dados = frasco(chave)
    if not liberado(dados):
        return False, texto_bloqueio(dados)
    preco = preco_frasco(chave)
    if not persistencia.gastar_membrana(preco):
        return False, f"Membrana insuficiente: precisa de {preco} ⬡."
    persistencia.ajustar_item(chave, 1)
    if chave == "evolutivo":
        persistencia.incrementar_estatistica("evolutivos_comprados_ciclo")
    if random.random() < valor("reembolso") / 100:
        persistencia.ajustar_item(chave, 1)
        return True, f"{dados['emoji']} {dados['nome']} guardado — e o 💸 Reembolso deu mais um de graça!"
    return True, f"{dados['emoji']} {dados['nome']} guardado na barra de frascos."


def gastar_frasco(chave):
    if quantidade(chave) <= 0:
        return False
    persistencia.ajustar_item(chave, -1)
    return True


# ---------- efeitos que o resto do jogo usa ----------

def saldo():
    return persistencia.obter_membrana()


def membrana_que_fica():
    """Quanto da Membrana atual o jogador leva para o próximo ciclo."""
    return int(saldo() * PARTE_DA_MEMBRANA_QUE_FICA)


def ganhar(quantidade_membrana):
    persistencia.ganhar_membrana(quantidade_membrana)
    return quantidade_membrana


def recompensa_fusao():
    return valor("eclosao_rica")


def recompensa_especie_nova():
    return GANHO_ESPECIE_NOVA + valor("descoberta")


def estagio_maximo_de_nascimento():
    return valor("cultura_avancada")


def estagio_gerado():
    """O estágio que o jogador escolheu no botão 🧫 Nasce (0 = o máximo que a Cultura Avançada libera)."""
    maximo = estagio_maximo_de_nascimento()
    escolhido = persistencia.obter_estatistica("estagio_escolhido")
    return min(escolhido, maximo) if escolhido else maximo


def estagio_maximo_possivel():
    """O estágio mais alto que a Cultura Avançada libera no nível máximo (quantos botões 'Nasce' existem)."""
    return upgrade("cultura_avancada")["valores"][-1]


def escolher_estagio_de_nascimento(estagio):
    """Botões 'Nasce' da Simulação: guarda o estágio escolhido pelo jogador."""
    persistencia.zerar_estatistica("estagio_escolhido")
    persistencia.incrementar_estatistica("estagio_escolhido", estagio)


def raio_frasco():
    return RAIO_FRASCO_BASE * valor("alcance")


def bonus_reproducao():
    return valor("catalisador") / 100


def fator_recarga():
    return 1 - valor("recarga") / 100


def limite_populacao():
    return valor("placa_maior")


def zoom_maximo():
    return valor("lente") / 100


def feromonio():
    return FEROMONIO[nivel("feromonio")]


def chance_boa_reverso():
    return valor("sorte") / 100


def fator_contagio():
    return 1 - valor("imunidade") / 100


def chance_heranca_forte():
    return valor("heranca") / 100
