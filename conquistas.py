from evolucao_dados import TOTAL_ESTAGIOS, nome_do_estagio, todas_receitas_fusao, BLOCOS
from comportamento import LISTA_COMPORTAMENTOS

MARCOS_MERGE = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2000]
MARCOS_REPRODUCAO = [1, 5, 10, 25, 50, 100, 250, 500, 750, 1000]
MARCOS_CONTAGIO = [1, 5, 10, 25, 50]
MARCOS_POPULACAO = [10, 50, 100, 200, 300]
MARCOS_DIARIO = [5, 25, 100]
MARCOS_POPULACAO_ESTAGIO = 5
MARCOS_FUSAO_MANUAL = [5, 25, 100]

# Conquistas das ferramentas do cientista: (estatística, marcos, nome, descrição)
CONQUISTAS_FERRAMENTAS = [
    ("arrastar_total", [1, 25, 100], "Mão firme", "Arraste organismos {marco} vez(es) com o mouse."),
    ("coletar_total", [1, 10, 50], "Coletor de amostras", "Colete {marco} organismo(s) para as Áreas de Fusão/Mutação."),
    ("soltar_total", [1, 10], "De volta à placa", "Solte {marco} organismo(s) de volta na placa."),
    ("infectar_total", [1, 10, 50], "Paciente zero", "Infecte {marco} organismo(s) pelo menu."),
    ("destruir_total", [1, 10, 50], "Esterilização", "Destrua {marco} organismo(s) pelo menu."),
]
CHAVES_LABORATORIO = ["arrastar_total", "coletar_total", "infectar_total", "destruir_total", "zoom_maximo_total"]

# Geladeira: além das 12 de cada slot, 5 com desafio de verdade
CONQUISTAS_GELADEIRA_EXTRAS = [
    ("geladeira_arca", "Arca de Noé", "Congele uma colônia com 100 organismos ou mais."),
    ("geladeira_amostra_rara", "Amostra rara", "Congele uma colônia que tenha um organismo do estágio 20 ou maior."),
    ("geladeira_cofre_cheio", "Cofre cheio", "Tenha os 6 compartimentos da geladeira ocupados ao mesmo tempo."),
    ("geladeira_ressurreicao", "Ressurreição", "Descongele uma colônia quando a placa estiver vazia."),
    ("geladeira_viajante", "Viajante do tempo", "Descongele colônias 10 vezes."),
]
TROFEUS_PARA_CONQUISTAS = [("madeira", "Madeira"), ("bronze", "Bronze"), ("prata", "Prata"),
                           ("ouro", "Ouro"), ("diamante", "Diamante")]


def gerar_lista_conquistas():
    conquistas = []

    for estagio in range(1, TOTAL_ESTAGIOS + 1):
        conquistas.append({
            "chave": f"descoberta_estagio_{estagio}",
            "nome": f"Primeira observação: {nome_do_estagio(estagio)}",
            "descricao": f"Observe pela primeira vez um organismo no estágio {estagio}.",
            "categoria": "Descoberta",
        })

    for marco in MARCOS_MERGE:
        conquistas.append({
            "chave": f"merge_total_{marco}",
            "nome": f"Fusões espontâneas: {marco}",
            "descricao": f"Realize {marco} fusões espontâneas (merge) na placa.",
            "categoria": "Merge",
        })

    for marco in MARCOS_REPRODUCAO:
        conquistas.append({
            "chave": f"reproducao_total_{marco}",
            "nome": f"Reproduções: {marco}",
            "descricao": f"Gere {marco} novos organismos por reprodução na Área de Fusão.",
            "categoria": "Reprodução",
        })

    for receita in todas_receitas_fusao():
        conquistas.append({
            "chave": f"fusao_manual_{receita['chave']}",
            "nome": f"Fusão dirigida: {receita['nome']}",
            "descricao": "Realize esta fusão manual na Área de Mutação.",
            "categoria": "Fusão Manual",
        })

    for marco in MARCOS_CONTAGIO:
        conquistas.append({
            "chave": f"contagio_total_{marco}",
            "nome": f"Surto: {marco} contágio(s)",
            "descricao": f"Deixe a infecção passar de um organismo para outro {marco} vez(es).",
            "categoria": "Infecção",
        })

    for slot in range(1, 7):
        conquistas.append({
            "chave": f"geladeira_salvar_{slot}",
            "nome": f"Amostra congelada — slot {slot}",
            "descricao": f"Salve um cenário no slot {slot} da geladeira.",
            "categoria": "Geladeira",
        })
        conquistas.append({
            "chave": f"geladeira_carregar_{slot}",
            "nome": f"Amostra descongelada — slot {slot}",
            "descricao": f"Carregue um cenário do slot {slot} da geladeira.",
            "categoria": "Geladeira",
        })

    for comportamento in LISTA_COMPORTAMENTOS:
        conquistas.append({
            "chave": f"comportamento_{comportamento.lower()}",
            "nome": f"Padrão identificado: {comportamento}",
            "descricao": f"Observe um organismo com comportamento {comportamento}.",
            "categoria": "Comportamento",
        })

    for marco in MARCOS_POPULACAO:
        conquistas.append({
            "chave": f"populacao_total_{marco}",
            "nome": f"População da colônia: {marco}",
            "descricao": f"Alcance {marco} organismos vivos simultaneamente.",
            "categoria": "População",
        })

    for estagio in range(1, TOTAL_ESTAGIOS + 1):
        conquistas.append({
            "chave": f"populacao_estagio_{estagio}",
            "nome": f"Colônia estabelecida: {nome_do_estagio(estagio)}",
            "descricao": f"Tenha {MARCOS_POPULACAO_ESTAGIO} organismos no estágio {estagio} ao mesmo tempo.",
            "categoria": "População por Estágio",
        })

    for bloco in BLOCOS:
        conquistas.append({
            "chave": f"colecionador_bloco_{bloco['nome'].lower().replace(' ', '_')}",
            "nome": f"Catálogo completo: {bloco['nome']}",
            "descricao": f"Descubra todos os estágios do grupo {bloco['nome']}.",
            "categoria": "Colecionador",
        })

    conquistas.append({
        "chave": "colecionador_total",
        "nome": "O Manual Completo",
        "descricao": f"Descubra todos os {TOTAL_ESTAGIOS} estágios de evolução.",
        "categoria": "Colecionador",
    })

    for marco in MARCOS_DIARIO:
        conquistas.append({
            "chave": f"diario_entradas_{marco}",
            "nome": f"Registros do cientista: {marco}",
            "descricao": f"Acumule {marco} entradas no diário de anotações.",
            "categoria": "Diário",
        })

    conquistas.append({
        "chave": "primeira_fusao_manual",
        "nome": "Mãos na Massa",
        "descricao": "Realize sua primeira fusão manual.",
        "categoria": "Marcos",
    })
    conquistas.append({
        "chave": "primeiro_contagio",
        "nome": "Algo Deu Errado",
        "descricao": "Testemunhe a primeira vez que a infecção passa para outro organismo.",
        "categoria": "Marcos",
    })
    conquistas.append({
        "chave": "brincar_de_deus",
        "nome": "Brincar de Deus",
        "descricao": "Provoque merge, reprodução e fusão manual.",
        "categoria": "Marcos",
    })

    for marco in MARCOS_FUSAO_MANUAL:
        conquistas.append({
            "chave": f"fusao_manual_total_{marco}",
            "nome": f"Alquimista: {marco} fusões",
            "descricao": f"Realize {marco} fusões manuais na Área de Fusão.",
            "categoria": "Fusão Manual",
        })

    for estatistica, marcos, nome, descricao in CONQUISTAS_FERRAMENTAS:
        for marco in marcos:
            conquistas.append({
                "chave": f"{estatistica}_{marco}",
                "nome": f"{nome}: {marco}",
                "descricao": descricao.format(marco=marco),
                "categoria": "Ferramentas do Cientista",
            })

    conquistas.append({
        "chave": "zoom_maximo",
        "nome": "Lente de aumento",
        "descricao": "Dê zoom de 300% em uma placa.",
        "categoria": "Ferramentas do Cientista",
    })
    conquistas.append({
        "chave": "explorador",
        "nome": "Explorador",
        "descricao": "Use as setas do teclado ou o minimapa para visitar outra parte do mapa.",
        "categoria": "Ferramentas do Cientista",
    })
    conquistas.append({
        "chave": "laboratorio_completo",
        "nome": "Laboratório completo",
        "descricao": "Use todas as ferramentas: arrastar, coletar, infectar, destruir e zoom máximo.",
        "categoria": "Marcos",
    })

    for chave, nome, descricao in CONQUISTAS_GELADEIRA_EXTRAS:
        conquistas.append({"chave": chave, "nome": nome, "descricao": descricao, "categoria": "Geladeira"})

    for numero, (chave, nome) in enumerate(TROFEUS_PARA_CONQUISTAS, start=1):
        conquistas.append({
            "chave": f"trofeu_{chave}",
            "nome": f"Troféu de {nome}",
            "descricao": f"Leve a colônia até a Forma de Vida Suprema pela {numero}ª vez.",
            "categoria": "Troféus",
        })

    return conquistas


def total_de_conquistas():
    return len(gerar_lista_conquistas())


def avaliar_e_desbloquear(contexto):
    import persistencia
    import bau_dados

    novas = []

    def tentar(chave):
        resultado = persistencia.desbloquear_conquista(chave)
        if resultado:
            # toda conquista rende Membrana; algumas ainda dão 1 nível de upgrade de presente
            resultado["ganho"] = bau_dados.ganhar(bau_dados.GANHO_CONQUISTA)
            resultado["presente"] = bau_dados.dar_presente(chave)
            novas.append(resultado)

    merge_total = persistencia.obter_estatistica("merge_total")
    for marco in MARCOS_MERGE:
        if merge_total >= marco:
            tentar(f"merge_total_{marco}")

    reproducao_total = persistencia.obter_estatistica("reproducao_total")
    for marco in MARCOS_REPRODUCAO:
        if reproducao_total >= marco:
            tentar(f"reproducao_total_{marco}")

    contagio_total = persistencia.obter_estatistica("contagio_total")
    for marco in MARCOS_CONTAGIO:
        if contagio_total >= marco:
            tentar(f"contagio_total_{marco}")
    if contagio_total >= 1:
        tentar("primeiro_contagio")

    diario_total = persistencia.contar_diario()
    for marco in MARCOS_DIARIO:
        if diario_total >= marco:
            tentar(f"diario_entradas_{marco}")

    descobertos = persistencia.listar_estagios_descobertos()
    for estagio, descoberto in descobertos.items():
        if descoberto:
            tentar(f"descoberta_estagio_{estagio}")

    for bloco in BLOCOS:
        completo = all(descobertos.get(e, False) for e in range(bloco["inicio"], bloco["fim"] + 1))
        if completo:
            tentar(f"colecionador_bloco_{bloco['nome'].lower().replace(' ', '_')}")

    if all(descobertos.get(e, False) for e in range(1, TOTAL_ESTAGIOS + 1)):
        tentar("colecionador_total")

    populacao_atual = contexto.get("populacao_atual", 0)
    for marco in MARCOS_POPULACAO:
        if populacao_atual >= marco:
            tentar(f"populacao_total_{marco}")

    for estagio, quantidade in contexto.get("populacao_por_estagio", {}).items():
        if quantidade >= MARCOS_POPULACAO_ESTAGIO:
            tentar(f"populacao_estagio_{estagio}")

    for comportamento in contexto.get("comportamentos_vistos", []):
        tentar(f"comportamento_{comportamento.lower()}")

    for slot in contexto.get("slots_salvos", []):
        tentar(f"geladeira_salvar_{slot}")

    for slot in contexto.get("slots_carregados", []):
        tentar(f"geladeira_carregar_{slot}")

    # geladeira: desafios extras
    if contexto.get("salvou_com_organismos", 0) >= 100:
        tentar("geladeira_arca")
    if contexto.get("salvou_com_maior_estagio", 0) >= 20:
        tentar("geladeira_amostra_rara")
    if contexto.get("carregou_com_placa_vazia"):
        tentar("geladeira_ressurreicao")
    if persistencia.obter_estatistica("geladeira_carregar_total") >= 10:
        tentar("geladeira_viajante")
    if all(slot["ocupado"] for slot in persistencia.listar_slots_geladeira()):
        tentar("geladeira_cofre_cheio")

    # troféus
    for numero, (chave, _nome) in enumerate(TROFEUS_PARA_CONQUISTAS, start=1):
        if persistencia.obter_estatistica("trofeus") >= numero:
            tentar(f"trofeu_{chave}")

    fusoes_realizadas = contexto.get("fusoes_realizadas", [])
    for chave_fusao in fusoes_realizadas:
        tentar(f"fusao_manual_{chave_fusao}")
    if fusoes_realizadas:
        tentar("primeira_fusao_manual")

    fusao_manual_total = persistencia.obter_estatistica("fusao_manual_total")
    if merge_total >= 1 and reproducao_total >= 1 and fusao_manual_total >= 1:
        tentar("brincar_de_deus")

    for marco in MARCOS_FUSAO_MANUAL:
        if fusao_manual_total >= marco:
            tentar(f"fusao_manual_total_{marco}")

    for estatistica, marcos, _nome, _descricao in CONQUISTAS_FERRAMENTAS:
        valor = persistencia.obter_estatistica(estatistica)
        for marco in marcos:
            if valor >= marco:
                tentar(f"{estatistica}_{marco}")

    if persistencia.obter_estatistica("zoom_maximo_total") >= 1:
        tentar("zoom_maximo")

    if persistencia.obter_estatistica("explorar_total") >= 1:
        tentar("explorador")

    if all(persistencia.obter_estatistica(chave) >= 1 for chave in CHAVES_LABORATORIO):
        tentar("laboratorio_completo")

    return novas
