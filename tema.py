"""Cores do jogo, tiradas dos fundos desenhados para cada tela.

Três "climas":
  LAB    -> laboratório holográfico (Simulação, Geladeira, Conquistas, Login, barra lateral)
  FUSAO  -> câmara de fusão: grafite com luzes âmbar (Área de Fusão)
  MESA   -> mesa do cientista: madeira, couro e papel (Manual e Diário)

Para mudar a cara do jogo inteiro, é só mexer aqui.

A cada troféu, LAB e FUSAO trocam de cor (ver CORES_DOS_CICLOS e aplicar_ciclo):
o jogador sente que subiu de fase.
"""
import colorsys

LAB = {
    "fundo": "#0a2646",          # azul-marinho
    "painel": "#0f2e4f",         # azul-aço (barras, caixas)
    "painel_claro": "#164270",   # botões comuns
    "grade": "#123a63",          # linhas do mapa
    "borda": "#2a9acc",          # ciano holográfico
    "destaque": "#1d76ac",       # botão principal
    "destaque_claro": "#51c1f0",
    "texto": "#d8f1fb",          # branco-gelo
    "texto_suave": "#8fc3dd",
    "aviso": "#f2c94c",          # amarelo dos avisos
    "perigo": "#8a2f3f",         # botões de apagar/sair
    "ativo": "#1d76ac",          # botão da tela atual na barra lateral
}

FUSAO = {
    "fundo": "#141d28",          # grafite
    "painel": "#293444",         # aço
    "painel_claro": "#36465d",
    "grade": "#1f2a38",
    "borda": "#f2a33a",          # âmbar das luzes da câmara
    "destaque": "#f2a33a",
    "destaque_claro": "#ffc46b",
    "texto": "#e3e9ec",          # prata
    "texto_suave": "#a9b6bd",
    "texto_no_destaque": "#1a1208",   # texto escuro em cima do âmbar
    "aviso": "#ffc46b",
    "perigo": "#8a2f3f",
}

MESA = {
    "fundo": "#1e1710",          # madeira escura
    "painel": "#3f2514",         # couro
    "painel_claro": "#5a3a22",
    "papel": "#e9d8bd",          # folha do caderno
    "tinta": "#2b1d12",          # texto escrito no papel
    "destaque": "#c89b78",
    "texto": "#f1e2cc",          # creme
    "texto_suave": "#c9a988",
    "bloqueado": "#2a2018",
}

# clima "laboratório de mutação": roxo escuro com verde-mutante (Área de Mutação, troféu de Madeira)
MUTACAO = {
    "fundo": "#1a1030",
    "painel": "#2a1a48",
    "painel_claro": "#3d2866",
    "grade": "#251842",
    "borda": "#8be04a",          # verde-mutante
    "destaque": "#6b3fc0",
    "texto": "#efe6ff",
    "texto_suave": "#b9a6e0",
    "aviso": "#8be04a",
}

# cores dos 5 troféus
TROFEUS = {
    "fundo": "#140f08",
    "painel": "#2a2012",
    "texto": "#f6ecd6",
    "texto_suave": "#c8b590",
    "bloqueado": "#3a3428",
}


# ---------- cores de cada ciclo ----------
# (matiz em graus, multiplicador da saturação). None = cores originais (azul do laboratório).
# Cada ciclo ganha a cor do troféu que acabou de ser conquistado.
CORES_DOS_CICLOS = {
    1: None,               # 🔵 laboratório azul
    2: (135, 0.8),         # 🌲 depois da Madeira: verde-musgo
    3: (22, 0.95),         # 🥉 depois do Bronze: cobre
    4: (205, 0.2),         # 🥈 depois da Prata: aço prateado
    5: (45, 1.0),          # 🥇 depois do Ouro: dourado
    6: (275, 1.0),         # 💎 Mestre da Colônia: cristal roxo
}
# telas cujo desenho de fundo também troca de cor
FUNDOS_QUE_MUDAM = {"simulacao", "geladeira", "conquistas", "fusao"}
# cores que têm significado próprio e não mudam (amarelo de aviso, vermelho de apagar...)
_CHAVES_FIXAS = {"aviso", "perigo", "texto_no_destaque"}

_ORIGINAIS = {"LAB": dict(LAB), "FUSAO": dict(FUSAO)}
_ajuste_atual = None


def _recolorir(cor_hex, matiz, saturacao):
    r, g, b = (int(cor_hex[i:i + 2], 16) / 255 for i in (1, 3, 5))
    _h, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(matiz / 360, min(1.0, s * saturacao), v)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def aplicar_ciclo(ciclo):
    """Troca as cores do LAB e da FUSAO para as do ciclo (muda o dicionário no lugar)."""
    global _ajuste_atual
    _ajuste_atual = CORES_DOS_CICLOS.get(ciclo)
    for nome, paleta in (("LAB", LAB), ("FUSAO", FUSAO)):
        for chave, cor in _ORIGINAIS[nome].items():
            if _ajuste_atual is None or chave in _CHAVES_FIXAS:
                paleta[chave] = cor
            else:
                paleta[chave] = _recolorir(cor, *_ajuste_atual)


def ajuste_do_fundo(nome_tela):
    """(matiz, saturação) para recolorir o desenho de fundo dessa tela, ou None."""
    return _ajuste_atual if nome_tela in FUNDOS_QUE_MUDAM else None
