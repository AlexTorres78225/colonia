import random

# Tabela única dos comportamentos. Cada coluna:
#   velocidade_mult    -> multiplica a velocidade do organismo
#   tamanho_mult       -> multiplica o tamanho do estágio
#   chance_reproducao  -> chance de ter filhote ao encostar num igual (só na Área de Fusão)
#   movimento          -> jeito de andar (ver Organismo.mover)
#   natural            -> True = pode nascer assim; False = só aparece pela ação do cientista
COMPORTAMENTOS = {
    "Calmo": {
        "emoji": "😌",
        "velocidade_mult": 0.6,
        "tamanho_mult": 1.0,
        "chance_reproducao": 0.65,
        "movimento": "suave",
        "natural": True,
        "descricao": "Lento, faz curvas suaves e às vezes para um pouco. Se reproduz com facilidade.",
    },
    "Agitado": {
        "emoji": "⚡",
        "velocidade_mult": 1.6,
        "tamanho_mult": 0.9,
        "chance_reproducao": 0.35,
        "movimento": "reto",
        "natural": True,
        "descricao": "Rápido e um pouco menor. Anda em linha reta e quica nas bordas, então encontra parceiros antes.",
    },
    "Irritado": {
        "emoji": "😠",
        "velocidade_mult": 1.2,
        "tamanho_mult": 1.0,
        "chance_reproducao": 0.20,
        "movimento": "persegue",
        "natural": True,
        "descricao": "Vai atrás do vizinho mais próximo e empurra os outros. Se reproduz pouco.",
    },
    "Infectado": {
        "emoji": "☣️",
        "velocidade_mult": 0.8,
        "tamanho_mult": 1.0,
        "chance_reproducao": 0.0,
        "movimento": "zigue",
        "natural": False,
        "chance_contagio": 0.25,
        "descricao": "Só surge quando o cientista usa 'Infectar'. Anda em zigue-zague, não se reproduz "
                     "e pode passar a infecção para quem encostar nele.",
    },
    "Mutação": {
        "emoji": "🧬",
        "velocidade_mult": 1.0,
        "tamanho_mult": 1.25,
        "chance_reproducao": 0.0,
        "movimento": "erratico",
        "natural": False,
        "descricao": "Só surge pela fusão manual na Área de Mutação. 25% maior e muda de direção o tempo todo. "
                     "Duas Mutações iguais que se encostam lá se fundem e pulam +2 estágios.",
    },
    # ---- IAs: liberadas no troféu de Prata. Nascem às vezes e dão contraste (nem ajudam, nem destroem). ----
    "Guardião": {
        "emoji": "🛡️",
        "velocidade_mult": 0.5,
        "tamanho_mult": 1.15,
        "chance_reproducao": 0.30,
        "movimento": "patrulha",
        "natural": False,
        "ia": True,
        "descricao": "IA. Patrulha em círculos e empurra para longe quem chega perto (atrapalha as fusões ao "
                     "redor). Perto dele, a infecção não pega.",
    },
    "Predador": {
        "emoji": "🐺",
        "velocidade_mult": 1.4,
        "tamanho_mult": 1.0,
        "chance_reproducao": 0.0,
        "movimento": "caca",
        "natural": False,
        "ia": True,
        "descricao": "IA. Caça organismos pelo menos 3 estágios menores e devora um a cada 10 segundos. "
                     "Não se reproduz.",
    },
    "Simbionte": {
        "emoji": "🤝",
        "velocidade_mult": 1.0,
        "tamanho_mult": 0.8,
        "chance_reproducao": 0.25,
        "movimento": "segue",
        "natural": False,
        "ia": True,
        "descricao": "IA. Gruda num organismo de outro estágio e segue ele. Quando o hospedeiro se funde, "
                     "o Simbionte sobe +1 estágio junto.",
    },
}

LISTA_COMPORTAMENTOS = list(COMPORTAMENTOS.keys())
LISTA_NATURAIS = [nome for nome, dados in COMPORTAMENTOS.items() if dados["natural"]]
LISTA_IAS = [nome for nome, dados in COMPORTAMENTOS.items() if dados.get("ia")]
COMPORTAMENTO_PADRAO = "Calmo"
CHANCE_DE_NASCER_IA = 0.08   # depois do troféu de Prata, 8% dos nascimentos viram uma IA


def escolher_comportamento_aleatorio():
    return random.choice(LISTA_NATURAIS)


def eh_ia(comportamento):
    return bool(modificadores(comportamento).get("ia"))


def eh_natural(comportamento):
    return modificadores(comportamento)["natural"]


def herdar_comportamento(comportamento_pai1, comportamento_pai2):
    if comportamento_pai1 == comportamento_pai2 and not eh_ia(comportamento_pai1):
        return comportamento_pai1
    if "Infectado" in (comportamento_pai1, comportamento_pai2):
        return "Infectado"  # a infecção passa para o filho
    candidatos = [c for c in (comportamento_pai1, comportamento_pai2) if eh_natural(c)]
    if not candidatos:
        return escolher_comportamento_aleatorio()
    return random.choice(candidatos)


def modificadores(comportamento):
    return COMPORTAMENTOS.get(comportamento, COMPORTAMENTOS[COMPORTAMENTO_PADRAO])
