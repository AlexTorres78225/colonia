import colorsys
from functools import lru_cache

# Só entram na evolução os estágios que têm desenho (PNG).
# Cada linha: (nome do estágio, número do arquivo estagio_XX.png em assets/organismos)
ESTAGIOS = [
    ("Cianobactéria Primitiva", 1), ("Micrococo Simples", 2), ("Bacilo Jovem", 3),
    ("Espirilo Ativo", 4), ("Estreptococo Duplo", 5), ("Estafilococo Robusto", 6),
    ("Bacilo Resiliente", 7), ("Cianobactéria Madura", 8), ("Colônia Bacteriana", 9),
    ("Bactéria Ápice", 10),
    ("Partícula Viral", 11), ("Capsídeo Simples", 12), ("Vírus Icosaédrico", 14),
    ("Bacteriófago Jovem", 15), ("Vírus Envelopado", 16), ("Vírus Mutante", 17),
    ("Vírus Agressivo", 18), ("Vírus Dominante", 19), ("Vírus Ápice", 20),
    ("Célula Primordial", 21), ("Célula Nucleada", 22), ("Célula Especializada", 23),
    ("Célula Colonial", 24), ("Célula Adaptada", 25),
    # ---- V2: 60 espécies novas entre a Célula Adaptada e a Suprema, liberadas pelos troféus ----
    # 🌲 Madeira
    ("Esporo Espinhoso", 31), ("Espiroqueta Lilás", 32), ("Sarcina Profunda", 33),
    ("Leptospira Verde", 34), ("Coco Felpudo", 35), ("Ameboide Rochoso", 36),
    ("Ameba Azul", 37), ("Radiolário Verde", 38), ("Bacilo Rubro", 39),
    ("Estafilococo Dourado", 40), ("Feixe de Bacilos", 41), ("Tétrade Escarlate", 42),
    ("Vírus Sombrio", 43), ("Bacilo Ciliado", 44), ("Flagelado Violeta", 45),
    # 🥉 Bronze
    ("Cocos Limão", 46), ("Vírus Laranja", 47), ("Mórula Azul", 48),
    ("Cacho Oliva", 49), ("Cristal Viral", 50), ("Euglena Verde", 51),
    ("Icosaedro Rosado", 52), ("Plasmídeo Azul", 53), ("Coral Microbiano", 54),
    ("Diatomácea Verde", 55), ("Corrente Âmbar", 56), ("Diatomácea Turquesa", 57),
    ("Vibrião Dourado", 58), ("Aglomerado Púrpura", 59), ("Vírus Esmeralda", 60),
    # 🥈 Prata
    ("Esfera Carmim", 61), ("Espiroqueta Ciano", 62), ("Heliozoário", 63),
    ("Fago Cristalino", 64), ("Espiral Rubra", 65), ("Estreptococo Dourado", 66),
    ("Colônia Púrpura", 67), ("Estrela Filamentosa", 68), ("Bacilo Espinhoso", 69),
    ("Icosaedro Rubro", 70), ("Esfera Musgo", 71), ("Diplococo Magenta", 72),
    ("Actinófrio Laranja", 73), ("Bacilo Safira", 74), ("Volvox", 75),
    # 🥇 Ouro
    ("Micélio Âmbar", 76), ("Anel Violeta", 77), ("Novelo Rosa", 78),
    ("Massa Dourada", 79), ("Vírus Celeste", 80),
    ("Espirovírus", 81), ("Bacilófago", 82), ("Coccofusão", 83), ("Flagelovírus", 84),
    ("Icosaedrospira", 85), ("Fagococo", 86), ("Coronabacilo", 87), ("Helicovírus", 88),
    ("Reticulófago", 89), ("Pseudoalveolado", 90),
    # a Forma de Vida Suprema é SEMPRE a última
    ("Forma de Vida Suprema", 30),
]

NOMES_ESTAGIOS = [nome for nome, _arquivo in ESTAGIOS]
TOTAL_ESTAGIOS = len(ESTAGIOS)
ESTAGIOS_DO_CICLO_1 = 25    # antes da V2 o jogo tinha 25 estágios (a Suprema era o 25)

# "trofeu" = quantos troféus o jogador precisa ter para essas espécies aparecerem.
# No ciclo 1 a Célula Adaptada (24) se funde direto na Suprema; cada troféu abre mais 15 no meio do caminho.
BLOCOS = [
    {"nome": "Bactérias", "inicio": 1, "fim": 10, "emoji": "🦠", "trofeu": 0},
    {"nome": "Vírus", "inicio": 11, "fim": 19, "emoji": "✴️", "trofeu": 0},
    {"nome": "Células Complexas", "inicio": 20, "fim": 24, "emoji": "🧫", "trofeu": 0},
    {"nome": "Protistas", "inicio": 25, "fim": 39, "emoji": "🌿", "trofeu": 1},
    {"nome": "Micróbios Raros", "inicio": 40, "fim": 54, "emoji": "🔬", "trofeu": 2},
    {"nome": "Formas Exóticas", "inicio": 55, "fim": 69, "emoji": "🌀", "trofeu": 3},
    {"nome": "Híbridos", "inicio": 70, "fim": 84, "emoji": "🧬", "trofeu": 4},
    {"nome": "Forma Suprema", "inicio": 85, "fim": 85, "emoji": "👑", "trofeu": 0},
]

# Tamanho (raio em pixels, no zoom 100%).
# Todo estágio é maior que o anterior: evoluir sempre faz crescer.
# Os 24 primeiros continuam com o tamanho de antes; as 60 espécies novas crescem devagar até a Suprema.
TAMANHO_PRIMEIRO_ESTAGIO = 5
PASSO_ANTIGO = (63 - 5) / 24          # o passo de tamanho dos 25 estágios da V1
TAMANHO_PRIMEIRA_NOVA = 61.5
TAMANHO_ULTIMA_NOVA = 79.5
TAMANHO_ULTIMO_ESTAGIO = 82


def bloco_do_estagio(estagio):
    for bloco in BLOCOS:
        if bloco["inicio"] <= estagio <= bloco["fim"]:
            return bloco
    return BLOCOS[-1]


def trofeu_do_estagio(estagio):
    """Quantos troféus são precisos para esta espécie existir no jogo (0 = desde o começo)."""
    return bloco_do_estagio(estagio)["trofeu"]


def estagios_com_trofeus(trofeus):
    """A lista dos estágios que existem com esse tanto de troféus, em ordem (a Suprema sempre por último)."""
    return [e for e in range(1, TOTAL_ESTAGIOS + 1) if trofeu_do_estagio(e) <= trofeus]


def arquivo_do_estagio(estagio):
    return ESTAGIOS[estagio - 1][1]


def _cor_hex(matiz, saturacao, valor):
    r, g, b = colorsys.hsv_to_rgb(matiz / 360.0, saturacao, valor)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


@lru_cache(maxsize=None)
def cor_do_estagio(estagio):
    """Cor usada nos pontinhos do minimapa."""
    bloco = bloco_do_estagio(estagio)
    posicao = (estagio - bloco["inicio"]) / max(1, (bloco["fim"] - bloco["inicio"]))
    if bloco["nome"] == "Bactérias":
        matiz = 10 + posicao * 30
    elif bloco["nome"] == "Vírus":
        matiz = 260 - posicao * 40
    elif bloco["trofeu"]:   # espécies novas: cada grupo numa faixa de cor
        matiz = (140 + bloco["trofeu"] * 50 + posicao * 40) % 360
    else:
        matiz = 95 - posicao * 45
    saturacao = 0.55 + posicao * 0.35
    valor = 0.65 + posicao * 0.3
    return _cor_hex(matiz, min(saturacao, 0.95), min(valor, 0.95))


@lru_cache(maxsize=None)
def tamanho_do_estagio(estagio):
    if estagio >= TOTAL_ESTAGIOS:
        return TAMANHO_ULTIMO_ESTAGIO
    if estagio < ESTAGIOS_DO_CICLO_1:
        return round(TAMANHO_PRIMEIRO_ESTAGIO + (estagio - 1) * PASSO_ANTIGO, 1)
    posicao = (estagio - ESTAGIOS_DO_CICLO_1) / (TOTAL_ESTAGIOS - 1 - ESTAGIOS_DO_CICLO_1)
    return round(TAMANHO_PRIMEIRA_NOVA + posicao * (TAMANHO_ULTIMA_NOVA - TAMANHO_PRIMEIRA_NOVA), 1)


def nome_do_estagio(estagio):
    return NOMES_ESTAGIOS[estagio - 1]


@lru_cache(maxsize=None)
def dados_completos_estagio(estagio):
    bloco = bloco_do_estagio(estagio)
    return {
        "estagio": estagio,
        "nome": nome_do_estagio(estagio),
        "bloco": bloco["nome"],
        "emoji": bloco["emoji"],
        "cor": cor_do_estagio(estagio),
        "tamanho": tamanho_do_estagio(estagio),
    }


def _quantidade_fusoes(estagio):
    return ((estagio - 1) % 3) + 1


_SUFIXOS_FUSAO = ["Variante Calma", "Variante Agitada", "Variante Irritada"]
_REQUISITOS_FUSAO = ["Calmo", "Agitado", "Irritado"]


def receitas_fusao_do_estagio(estagio):
    quantidade = _quantidade_fusoes(estagio)
    receitas = []
    for indice in range(quantidade):
        receitas.append({
            "chave": f"fusao_{estagio}_{indice + 1}",
            "nome": f"{nome_do_estagio(estagio)} — {_SUFIXOS_FUSAO[indice]}",
            "estagio_origem": estagio,
            "comportamento_exigido": _REQUISITOS_FUSAO[indice],
        })
    return receitas


def todas_receitas_fusao():
    receitas = []
    for estagio in range(1, TOTAL_ESTAGIOS + 1):
        receitas.extend(receitas_fusao_do_estagio(estagio))
    return receitas
