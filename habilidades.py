import random
from comportamento import escolher_comportamento_aleatorio, herdar_comportamento

VELOCIDADE_MIN, VELOCIDADE_MAX = 0.5, 2.5
# O tamanho agora vem só do estágio e do comportamento (sem sorteio).
# tamanho_mod continua no banco, mas fica sempre 1.0.
TAMANHO_MOD_PADRAO = 1.0


def gerar_habilidades_iniciais(comportamento=None):
    return {
        "velocidade_mod": round(random.uniform(0.8, 1.3), 2),
        "tamanho_mod": TAMANHO_MOD_PADRAO,
        "comportamento": comportamento or escolher_comportamento_aleatorio(),
    }


def _limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def herdar_habilidades(habilidades_pai1, habilidades_pai2):
    velocidade = (habilidades_pai1["velocidade_mod"] + habilidades_pai2["velocidade_mod"]) / 2
    velocidade += random.uniform(-0.1, 0.1)
    comportamento = herdar_comportamento(
        habilidades_pai1["comportamento"], habilidades_pai2["comportamento"]
    )
    return {
        "velocidade_mod": round(_limitar(velocidade, VELOCIDADE_MIN, VELOCIDADE_MAX), 2),
        "tamanho_mod": TAMANHO_MOD_PADRAO,
        "comportamento": comportamento,
    }


def habilidades_de_fusao(habilidades_pai1, habilidades_pai2):
    base = herdar_habilidades(habilidades_pai1, habilidades_pai2)
    base["comportamento"] = "Mutação"
    base["velocidade_mod"] = round(_limitar(base["velocidade_mod"] * 1.15, VELOCIDADE_MIN, VELOCIDADE_MAX), 2)
    return base
