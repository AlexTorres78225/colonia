import colorsys
import random
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
    ("Célula Colonial", 24), ("Célula Adaptada", 25), ("Forma de Vida Suprema", 30),
]

NOMES_ESTAGIOS = [nome for nome, _arquivo in ESTAGIOS]
TOTAL_ESTAGIOS = len(ESTAGIOS)

# ---- V2: espécies novas, liberadas pelos troféus ----
# Todo ciclo continua com 25 estágios e a Suprema no 25. A partir do ciclo 2, os 24 primeiros lugares
# são 15 espécies novas (exclusivas daquele ciclo) embaralhadas com 9 das antigas.
# Cada linha: (nome, número do arquivo estagio_XX.png). O índice da lista = troféus que o jogador tem.
ESPECIES_NOVAS = {
    1: ("🌿", "Protistas", [
        ("Esporo Espinhoso", 31), ("Espiroqueta Lilás", 32), ("Sarcina Profunda", 33),
        ("Leptospira Verde", 34), ("Coco Felpudo", 35), ("Ameboide Rochoso", 36),
        ("Ameba Azul", 37), ("Radiolário Verde", 38), ("Bacilo Rubro", 39),
        ("Estafilococo Dourado", 40), ("Feixe de Bacilos", 41), ("Tétrade Escarlate", 42),
        ("Vírus Sombrio", 43), ("Bacilo Ciliado", 44), ("Flagelado Violeta", 45)]),
    2: ("🔬", "Micróbios Raros", [
        ("Cocos Limão", 46), ("Vírus Laranja", 47), ("Mórula Azul", 48),
        ("Cacho Oliva", 49), ("Cristal Viral", 50), ("Euglena Verde", 51),
        ("Icosaedro Rosado", 52), ("Plasmídeo Azul", 53), ("Coral Microbiano", 54),
        ("Diatomácea Verde", 55), ("Corrente Âmbar", 56), ("Diatomácea Turquesa", 57),
        ("Vibrião Dourado", 58), ("Aglomerado Púrpura", 59), ("Vírus Esmeralda", 60)]),
    3: ("🌀", "Formas Exóticas", [
        ("Esfera Carmim", 61), ("Espiroqueta Ciano", 62), ("Heliozoário", 63),
        ("Fago Cristalino", 64), ("Espiral Rubra", 65), ("Estreptococo Dourado", 66),
        ("Colônia Púrpura", 67), ("Estrela Filamentosa", 68), ("Bacilo Espinhoso", 69),
        ("Icosaedro Rubro", 70), ("Esfera Musgo", 71), ("Diplococo Magenta", 72),
        ("Actinófrio Laranja", 73), ("Bacilo Safira", 74), ("Volvox", 75)]),
    4: ("🧬", "Híbridos", [
        ("Micélio Âmbar", 76), ("Anel Violeta", 77), ("Novelo Rosa", 78),
        ("Massa Dourada", 79), ("Vírus Celeste", 80),
        ("Espirovírus", 81), ("Bacilófago", 82), ("Coccofusão", 83), ("Flagelovírus", 84),
        ("Icosaedrospira", 85), ("Fagococo", 86), ("Coronabacilo", 87), ("Helicovírus", 88),
        ("Reticulófago", 89), ("Pseudoalveolado", 90)]),
}
ANTIGAS_POR_CICLO = 9
TOTAL_ESPECIES = TOTAL_ESTAGIOS + sum(len(lista) for _e, _n, lista in ESPECIES_NOVAS.values())

# O ciclo que está sendo jogado (a persistencia avisa ao abrir o save e a cada troféu).
_ciclo_atual = 1


def definir_ciclo(ciclo):
    global _ciclo_atual
    _ciclo_atual = ciclo


def ciclo_em_jogo():
    return _ciclo_atual

BLOCOS = [
    {"nome": "Bactérias", "inicio": 1, "fim": 10, "emoji": "🦠"},
    {"nome": "Vírus", "inicio": 11, "fim": 19, "emoji": "✴️"},
    {"nome": "Células Complexas", "inicio": 20, "fim": 25, "emoji": "🧫"},
]

# Tamanho (raio em pixels, no zoom 100%) do primeiro e do último estágio.
# Todo estágio é maior que o anterior: evoluir sempre faz crescer.
TAMANHO_PRIMEIRO_ESTAGIO = 5
TAMANHO_ULTIMO_ESTAGIO = 63


def bloco_do_estagio(estagio):
    for bloco in BLOCOS:
        if bloco["inicio"] <= estagio <= bloco["fim"]:
            return bloco
    return BLOCOS[-1]


@lru_cache(maxsize=None)
def especies_do_ciclo(ciclo):
    """Os 25 lugares do ciclo: cada um é (nome, arquivo, emoji do grupo, nome do grupo, troféu que liberou).

    Ciclo 1 = as espécies de sempre. Do ciclo 2 em diante: 15 novas + 9 antigas, embaralhadas
    sempre do mesmo jeito (o sorteio usa o número do ciclo como semente).
    """
    antigas = []
    for estagio, (nome, arquivo) in enumerate(ESTAGIOS, 1):
        bloco = bloco_do_estagio(estagio)
        antigas.append((nome, arquivo, bloco["emoji"], bloco["nome"], 0))
    trofeu = ciclo - 1
    if trofeu not in ESPECIES_NOVAS:
        return antigas
    emoji, grupo, lista = ESPECIES_NOVAS[trofeu]
    novas = [(nome, arquivo, emoji, grupo, trofeu) for nome, arquivo in lista]
    sorteio = random.Random(f"colonia-ciclo-{ciclo}")
    lugares = TOTAL_ESTAGIOS - 1   # a Suprema fica fora do sorteio: sempre a última
    escolhidas = [antigas[i] for i in sorted(sorteio.sample(range(lugares), ANTIGAS_POR_CICLO))]
    vagas_das_novas = set(sorteio.sample(range(lugares), len(novas)))
    sorteio.shuffle(novas)
    resultado = []
    for lugar in range(lugares):
        resultado.append(novas.pop() if lugar in vagas_das_novas else escolhidas.pop(0))
    return resultado + [antigas[-1]]


def especie(estagio, ciclo=None):
    return especies_do_ciclo(ciclo or _ciclo_atual)[estagio - 1]


def arquivo_do_estagio(estagio, ciclo=None):
    return especie(estagio, ciclo)[1]


def todas_as_especies():
    """As 85 espécies diferentes (arquivo -> nome), de todos os ciclos."""
    especies = {arquivo: nome for nome, arquivo in ESTAGIOS}
    for _emoji, _grupo, lista in ESPECIES_NOVAS.values():
        especies.update({arquivo: nome for nome, arquivo in lista})
    return especies


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
    else:
        matiz = 95 - posicao * 45
    saturacao = 0.55 + posicao * 0.35
    valor = 0.65 + posicao * 0.3
    return _cor_hex(matiz, min(saturacao, 0.95), min(valor, 0.95))


@lru_cache(maxsize=None)
def tamanho_do_estagio(estagio):
    passo = (TAMANHO_ULTIMO_ESTAGIO - TAMANHO_PRIMEIRO_ESTAGIO) / (TOTAL_ESTAGIOS - 1)
    return round(TAMANHO_PRIMEIRO_ESTAGIO + (estagio - 1) * passo, 1)


def nome_do_estagio(estagio, ciclo=None):
    return especie(estagio, ciclo)[0]


def dados_completos_estagio(estagio, ciclo=None):
    return _dados_completos(estagio, ciclo or _ciclo_atual)


@lru_cache(maxsize=None)
def _dados_completos(estagio, ciclo):
    nome, arquivo, emoji, grupo, trofeu = especie(estagio, ciclo)
    return {
        "estagio": estagio,
        "nome": nome,
        "arquivo": arquivo,
        "bloco": grupo,
        "emoji": emoji,
        "trofeu": trofeu,
        "cor": cor_do_estagio(estagio),
        "tamanho": tamanho_do_estagio(estagio),
    }


def _quantidade_fusoes(estagio):
    return ((estagio - 1) % 3) + 1


_SUFIXOS_FUSAO = ["Variante Calma", "Variante Agitada", "Variante Irritada"]
_REQUISITOS_FUSAO = ["Calmo", "Agitado", "Irritado"]


def receitas_fusao_do_estagio(estagio, ciclo=None):
    quantidade = _quantidade_fusoes(estagio)
    receitas = []
    for indice in range(quantidade):
        receitas.append({
            "chave": f"fusao_{estagio}_{indice + 1}",
            "nome": f"{nome_do_estagio(estagio, ciclo)} — {_SUFIXOS_FUSAO[indice]}",
            "estagio_origem": estagio,
            "comportamento_exigido": _REQUISITOS_FUSAO[indice],
        })
    return receitas


def todas_receitas_fusao(ciclo=None):
    receitas = []
    for estagio in range(1, TOTAL_ESTAGIOS + 1):
        receitas.extend(receitas_fusao_do_estagio(estagio, ciclo))
    return receitas
