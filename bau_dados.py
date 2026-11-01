"""Catálogo do Baú: upgrades, frascos, troféus e a economia da Membrana ⬡.

(O símbolo da Membrana é ⬡ — o emoji 🫧 aparecia como um quadradinho no Windows 10.)

Upgrades -> permanentes, sempre bons, até 5 níveis, cada nível mais caro.
            O nível 4 só abre com o troféu de Prata e o nível 5 com o de Ouro.
Frascos  -> de uso único; o jogador escolhe ser herói ou vilão.
Troféus  -> cada vez que a colônia chega ao último estágio, ganha um troféu e começa um ciclo novo.
            Cada troféu libera UMA coisa nova (requer_trofeu nos itens).
"""
import random

import persistencia
from comportamento import LISTA_IAS, CHANCE_DE_NASCER_IA

NIVEL_MAXIMO = 5
TROFEU_DO_NIVEL = {4: 3, 5: 4}   # nível 4 pede o troféu de Prata (3º); nível 5, o de Ouro (4º)

# Economia
MEMBRANA_INICIAL = 50         # conta nova e cada ciclo novo começam com isso
PARTE_DA_MEMBRANA_QUE_FICA = 0.2   # ao ganhar um troféu, 20% da Membrana que sobrou vai para o ciclo novo
CUSTO_ORGANISMO = 1           # o mínimo: o "+ Organismo" custa o número do estágio que nasce (ver custo_organismo)
FRASCOS_QUE_PASSAM = 3        # no troféu, cada frasco leva no máximo 3 para o ciclo novo
CUSTO_DESTRUIR_INFECTADO = 3  # destruir um Infectado custa Membrana (antes era de graça)
EVOLUTIVO_MAXIMO = 8          # o Frasco Evolutivo evolui no máximo 8 organismos
GANHO_FUSAO_BASE = 3          # unir dois organismos iguais (+1 por nível da Eclosão Rica)
GANHO_ESPECIE_NOVA = 20       # + Bônus de Descoberta
GANHO_CONQUISTA = 15
GANHO_REPRODUCAO = 1
GANHO_CLIQUE_SEM_SALDO = 1    # sem Membrana nenhuma, clicar num organismo "brota" +1 ⬡
AUMENTO_EVOLUTIVO = 20        # cada Evolutivo comprado fica 20 ⬡ mais caro (e não volta ao normal no ciclo novo)
GANHO_NUCLEO_DESTRUIDO = 50   # recompensa por destruir um Núcleo Corrompido com a 3ª Seringa

RAIO_FRASCO_BASE = 110        # área de efeito dos frascos (em pixels do mapa, sem upgrade)

# ---------- troféus ----------
TROFEUS = [
    {"chave": "madeira", "emoji": "🌲", "nome": "Madeira", "cor": "#a0703c",
     "libera": "🧬 Área de Mutação e ☣️ Núcleos Corrompidos (1 por troféu, até 4), com Película, "
               "Glóbulos Brancos e Seringa no Baú"},
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

# "valores" tem 6 posições: nível 0 (sem comprar), 1, 2, 3, 4 e 5.
UPGRADES = [
    {"chave": "eclosao_rica", "emoji": "💰", "nome": "Eclosão Rica",
     "descricao": "Membrana ganha a cada fusão.",
     "valores": [3, 4, 5, 6, 7, 8], "precos": [40, 90, 160, 260, 420], "formato": "{} ⬡ por fusão"},
    {"chave": "cultura_avancada", "emoji": "🧬", "nome": "Cultura Avançada",
     "descricao": "Libera organismos novos mais evoluídos (escolha qual nasce na Simulação, em “Nasce”).",
     "valores": [1, 2, 3, 4, 5, 6], "precos": [50, 110, 190, 300, 480], "formato": "nasce até o estágio {}"},
    {"chave": "alcance", "emoji": "🎯", "nome": "Alcance dos Frascos",
     "descricao": "Aumenta a área de efeito dos frascos.",
     "valores": [1.0, 1.2, 1.4, 1.6, 1.8, 2.0], "precos": [60, 130, 220, 350, 540], "formato": "área ×{}"},
    {"chave": "catalisador", "emoji": "⚗️", "nome": "Catalisador",
     "descricao": "Mais chance de reprodução na Área de Fusão.",
     "valores": [0, 6, 12, 18, 24, 30], "precos": [70, 150, 250, 390, 600], "formato": "+{}% de chance"},
    {"chave": "lente", "emoji": "🔭", "nome": "Lente Potente",
     "descricao": "Aumenta o zoom máximo.",
     "valores": [300, 340, 380, 420, 460, 500], "precos": [80, 170, 280, 430, 650], "formato": "zoom até {}%"},
    {"chave": "recarga", "emoji": "⏳", "nome": "Recarga Rápida",
     "descricao": "Menos espera entre um filhote e outro.",
     "valores": [0, 12, 24, 36, 48, 60], "precos": [100, 210, 350, 540, 800], "formato": "−{}% de espera"},
    {"chave": "placa_maior", "emoji": "🧫", "nome": "Placa Maior",
     "descricao": "Aumenta o limite de população da colônia.",
     "valores": [300, 360, 420, 480, 540, 600], "precos": [120, 250, 400, 600, 860], "formato": "até {} organismos"},
    {"chave": "feromonio", "emoji": "🧲", "nome": "Feromônio",
     "descricao": "Iguais se atraem na placa e se fundem mais rápido.",
     "valores": [0, 1, 2, 3, 4, 5], "precos": [140, 290, 470, 710, 1050],
     "formato_lista": ["sem atração", "atração mínima", "atração fraca", "atração média", "atração forte",
                       "atração máxima"]},
    {"chave": "descoberta", "emoji": "🔍", "nome": "Bônus de Descoberta",
     "descricao": "Membrana extra ao descobrir uma espécie nova.",
     "valores": [0, 6, 12, 18, 24, 30], "precos": [170, 350, 560, 830, 1200], "formato": "+{} ⬡ por espécie"},
    {"chave": "sorte", "emoji": "🍀", "nome": "Sorte de Laboratório",
     "descricao": "Melhora a chance boa do Frasco Reverso.",
     "valores": [50, 55, 60, 65, 70, 75], "precos": [220, 450, 720, 1050, 1450], "formato": "{}% de chance boa"},
    # ---- liberados no troféu de Madeira, junto com os Núcleos Corrompidos ----
    {"chave": "pelicula_tempo", "emoji": "🔮", "nome": "Película Duradoura", "requer_trofeu": 1,
     "descricao": "A Película segura o Núcleo por mais tempo antes de se romper.",
     "valores": [20, 25, 30, 35, 40, 50], "precos": [80, 170, 280, 430, 650], "formato": "dura {} s"},
    {"chave": "pelicula_resistencia", "emoji": "🧱", "nome": "Película Reforçada", "requer_trofeu": 1,
     "descricao": "A Película aguenta mais ondas de vírus antes de se romper.",
     "valores": [2, 3, 4, 5, 6, 8], "precos": [90, 190, 310, 470, 700], "formato": "aguenta {} ondas"},
    {"chave": "globulos_tempo", "emoji": "⏱", "nome": "Glóbulos Persistentes", "requer_trofeu": 1,
     "descricao": "Os Glóbulos Brancos ficam mais tempo de guarda perto do Núcleo.",
     "valores": [20, 25, 30, 35, 40, 50], "precos": [80, 170, 280, 430, 650], "formato": "ficam {} s"},
    {"chave": "globulos_resistencia", "emoji": "⚪", "nome": "Glóbulos Fortes", "requer_trofeu": 1,
     "descricao": "Cada bolinha branca derruba mais vírus antes de sumir.",
     "valores": [1, 2, 3, 4, 5, 6], "precos": [90, 190, 310, 470, 700], "formato": "{} vírus por bolinha"},
    # ---- liberados no troféu de Ouro ----
    {"chave": "imunidade", "emoji": "🛡", "nome": "Imunidade", "requer_trofeu": 4,
     "descricao": "Menos chance de a infecção passar adiante (contra o vírus do Núcleo, vale metade).",
     "valores": [0, 15, 30, 45, 60, 75], "precos": [280, 570, 920, 1350, 1900], "formato": "−{}% de contágio"},
    {"chave": "reembolso", "emoji": "💸", "nome": "Reembolso", "requer_trofeu": 4,
     "descricao": "Chance de ganhar um frasco a mais de graça ao comprar.",
     "valores": [0, 9, 18, 27, 36, 45], "precos": [320, 650, 1050, 1500, 2100], "formato": "{}% de frasco grátis"},
    {"chave": "heranca", "emoji": "🧪", "nome": "Herança Forte", "requer_trofeu": 4,
     "descricao": "Filhotes da Área de Fusão às vezes nascem 1 estágio acima.",
     "valores": [0, 6, 12, 18, 24, 30], "precos": [420, 850, 1350, 1950, 2700], "formato": "{}% nasce +1 estágio"},
]

# Feromônio por nível: (distância que o organismo "sente" o par, força da atração)
FEROMONIO = [(0, 0.0), (140, 0.04), (200, 0.06), (260, 0.09), (320, 0.12), (380, 0.15)]

FRASCOS = [
    {"chave": "corrompido", "emoji": "☣️", "nome": "Frasco Corrompido", "lado": "vilão", "preco": 15,
     "descricao": "Cria +1 organismo Infectado onde você clicar."},
    {"chave": "nutritivo", "emoji": "💧", "nome": "Frasco Nutritivo", "lado": "herói", "preco": 25,
     "descricao": "Cria 3 organismos ali, no estágio da Cultura Avançada."},
    {"chave": "antidoto", "emoji": "💊", "nome": "Frasco Antídoto", "lado": "herói", "preco": 30,
     "descricao": "Cura todos os Infectados da área."},
    {"chave": "antibiotico", "emoji": "💀", "nome": "Frasco Antibiótico", "lado": "vilão", "preco": 40,
     "descricao": "Mata todos os organismos da área, bons e ruins."},
    {"chave": "reverso", "emoji": "🔁", "nome": "Frasco Reverso", "lado": "aposta", "preco": 45,
     "descricao": "Elimina os ruins da área… ou os bons! A Sorte melhora a chance."},
    {"chave": "evolutivo", "emoji": "✨", "nome": "Frasco Evolutivo", "lado": "herói", "preco": 120,
     "descricao": "+1 estágio para até 8 organismos da área. Fica +20 ⬡ mais caro a cada compra."},
    # ---- contra os Núcleos Corrompidos (troféu de Madeira): use clicando em cima de um Núcleo ----
    {"chave": "pelicula", "emoji": "🔮", "nome": "Película", "lado": "herói", "preco": 40, "requer_trofeu": 1,
     "no_nucleo": True,
     "descricao": "Envolve um Núcleo numa bolha: os vírus não saem até ela se romper."},
    {"chave": "globulos", "emoji": "⚪", "nome": "Glóbulos Brancos", "lado": "herói", "preco": 60,
     "requer_trofeu": 1, "no_nucleo": True,
     "descricao": "Ficam perto de um Núcleo soltando bolinhas brancas que caçam os vírus."},
    {"chave": "seringa", "emoji": "💉", "nome": "Seringa", "lado": "herói", "preco": 160, "requer_trofeu": 1,
     "no_nucleo": True,
     "descricao": "O único jeito de destruir um Núcleo: ele some na 3ª Seringa."},
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
    """A cada troféu o jogo fica mais difícil: -8% de chance de reprodução (até -32%)."""
    return min(0.32, 0.08 * trofeus())


def maximo_de_nucleos():
    """Núcleos Corrompidos ao mesmo tempo na placa: 1 por troféu, até 4 (o ciclo 1 não tem nenhum)."""
    return min(4, trofeus())


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


def nivel_trancado(nivel_desejado):
    """Os níveis 4 e 5 esperam um troféu. Devolve o texto do cadeado (ou None se já pode comprar)."""
    trofeu = TROFEU_DO_NIVEL.get(nivel_desejado)
    if trofeu is None or trofeus() >= trofeu:
        return None
    return f"🔒 Nível {nivel_desejado} requer o troféu de {NOME_DO_TROFEU_REQUERIDO[trofeu]}"


def comprar_upgrade(chave):
    dados = upgrade(chave)
    if not liberado(dados):
        return False, texto_bloqueio(dados)
    preco = preco_do_proximo_nivel(chave)
    if preco is None:
        return False, "Esse upgrade já está no nível máximo."
    trancado = nivel_trancado(nivel(chave) + 1)
    if trancado:
        return False, trancado
    if not persistencia.gastar_membrana(preco):
        return False, f"Membrana insuficiente: precisa de {preco} ⬡."
    persistencia.definir_nivel_upgrade(chave, nivel(chave) + 1)
    persistencia.adicionar_entrada_diario(f"Upgrade comprado no Baú: {dados['nome']} nível {nivel(chave)}.")
    return True, f"{dados['emoji']} {dados['nome']} subiu para o nível {nivel(chave)}!"


def dar_presente(chave_conquista):
    """Algumas conquistas dão 1 nível de upgrade grátis. Devolve o texto do presente (ou None)."""
    chave = PRESENTES_DE_CONQUISTA.get(chave_conquista)
    if chave is None or nivel(chave) >= NIVEL_MAXIMO or nivel_trancado(nivel(chave) + 1):
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
        # o nome da estatística ficou do tempo em que ela zerava a cada ciclo; hoje ela não zera mais
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


def custo_organismo():
    """O "+ Organismo" custa o número do estágio que nasce: estágio 1 = 1 ⬡, estágio 4 = 4 ⬡."""
    return max(CUSTO_ORGANISMO, estagio_gerado())


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


def fator_contagio_nucleo():
    """O vírus do Núcleo é uma cepa nova: a Imunidade só vale metade contra ele."""
    return 1 - valor("imunidade") / 200


def duracao_pelicula():
    return valor("pelicula_tempo")


def resistencia_pelicula():
    return valor("pelicula_resistencia")


def duracao_globulos():
    return valor("globulos_tempo")


def resistencia_globulos():
    return valor("globulos_resistencia")


def chance_heranca_forte():
    return valor("heranca") / 100
