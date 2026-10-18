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
    ("Célula Colonial", 24), ("Célula Adaptada", 25), ("Forma de Vida Suprema", 30),
]

NOMES_ESTAGIOS = [nome for nome, _arquivo in ESTAGIOS]
TOTAL_ESTAGIOS = len(ESTAGIOS)

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
    else:
        matiz = 95 - posicao * 45
    saturacao = 0.55 + posicao * 0.35
    valor = 0.65 + posicao * 0.3
    return _cor_hex(matiz, min(saturacao, 0.95), min(valor, 0.95))


@lru_cache(maxsize=None)
def tamanho_do_estagio(estagio):
    passo = (TAMANHO_ULTIMO_ESTAGIO - TAMANHO_PRIMEIRO_ESTAGIO) / (TOTAL_ESTAGIOS - 1)
    return round(TAMANHO_PRIMEIRO_ESTAGIO + (estagio - 1) * passo, 1)


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
