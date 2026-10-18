import os

import tema
from evolucao_dados import arquivo_do_estagio

try:
    from PIL import Image, ImageTk
    _PILLOW_DISPONIVEL = True
except ImportError:
    _PILLOW_DISPONIVEL = False

PASTA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
PASTA_ORGANISMOS = os.path.join(PASTA_ASSETS, "organismos")
PASTA_FUNDOS = os.path.join(PASTA_ASSETS, "fundos")
PASTA_ICONES = os.path.join(PASTA_ASSETS, "icones")

_CACHE_REDIMENSIONADAS = {}
_CACHE_ORIGINAIS = {}
_CACHE_FUNDOS = {}


def limpar_cache():
    """As imagens do Tkinter pertencem a uma janela; ao abrir uma janela nova, recomeça o cache."""
    _CACHE_REDIMENSIONADAS.clear()
    _CACHE_FUNDOS.clear()


def _existe(caminho):
    return os.path.isfile(caminho)


def _recortar_transparencia(imagem):
    """Tira a sobra transparente em volta do desenho.

    Cada PNG tem uma margem diferente; sem recortar, um desenho com muita margem
    pareceria menor do que é e o tamanho não acompanharia a evolução.
    """
    # pixels quase invisíveis (brilho fraquinho) não contam como parte do desenho
    caixa = imagem.getchannel("A").point(lambda alfa: 255 if alfa > 40 else 0).getbbox()
    return imagem.crop(caixa) if caixa else imagem


def _encaixar_no_quadrado(imagem, tamanho_pixels):
    """Redimensiona sem achatar: o lado maior vira tamanho_pixels e o desenho fica centralizado."""
    largura, altura = imagem.size
    escala = tamanho_pixels / max(largura, altura)
    nova = imagem.resize((max(1, round(largura * escala)), max(1, round(altura * escala))), Image.LANCZOS)
    quadrado = Image.new("RGBA", (tamanho_pixels, tamanho_pixels), (0, 0, 0, 0))
    quadrado.paste(nova, ((tamanho_pixels - nova.width) // 2, (tamanho_pixels - nova.height) // 2))
    return quadrado


def _imagem_redimensionada(caminho, tamanho_pixels):
    if not _existe(caminho):
        return None

    tamanho_pixels = max(4, int(tamanho_pixels))
    chave = (caminho, tamanho_pixels)
    if chave in _CACHE_REDIMENSIONADAS:
        return _CACHE_REDIMENSIONADAS[chave]

    if _PILLOW_DISPONIVEL:
        try:
            if caminho not in _CACHE_ORIGINAIS:
                _CACHE_ORIGINAIS[caminho] = _recortar_transparencia(Image.open(caminho).convert("RGBA"))
            imagem_tk = ImageTk.PhotoImage(_encaixar_no_quadrado(_CACHE_ORIGINAIS[caminho], tamanho_pixels))
        except Exception:
            imagem_tk = None
    else:
        try:
            import tkinter as tk
            imagem_tk = tk.PhotoImage(file=caminho)
        except Exception:
            imagem_tk = None

    _CACHE_REDIMENSIONADAS[chave] = imagem_tk
    return imagem_tk


def imagem_organismo_redimensionada(estagio, tamanho_pixels):
    caminho = os.path.join(PASTA_ORGANISMOS, f"estagio_{arquivo_do_estagio(estagio):02d}.png")
    return _imagem_redimensionada(caminho, tamanho_pixels)


# Qual desenho de fusão usar para cada receita (o comportamento exigido pela receita).
_ARQUIVO_FUSAO_POR_VARIANTE = {
    "Calmo": "equilibrado",
    "Agitado": "agitado",
    "Irritado": "instavel",
}


def imagem_fusao_redimensionada(variante, tamanho_pixels):
    nome_arquivo = _ARQUIVO_FUSAO_POR_VARIANTE.get(variante)
    if nome_arquivo is None:
        return None
    caminho = os.path.join(PASTA_ORGANISMOS, f"fusao_{nome_arquivo}.png")
    return _imagem_redimensionada(caminho, tamanho_pixels)


def _recolorir_imagem(imagem, matiz, saturacao):
    """Pinta o desenho inteiro na cor do ciclo, mantendo o claro/escuro (igual ao tema.aplicar_ciclo)."""
    alfa = imagem.getchannel("A")
    _h, s, v = imagem.convert("RGB").convert("HSV").split()
    h = Image.new("L", imagem.size, round(matiz / 360 * 255))
    s = s.point(lambda valor: min(255, round(valor * saturacao)))
    nova = Image.merge("HSV", (h, s, v)).convert("RGBA")
    nova.putalpha(alfa)
    return nova


def imagem_fundo(nome_tela, largura=None, altura=None):
    caminho = os.path.join(PASTA_FUNDOS, f"{nome_tela}.png")
    if not _existe(caminho):
        return None

    ajuste = tema.ajuste_do_fundo(nome_tela)
    chave = (caminho, largura, altura, ajuste)
    if chave in _CACHE_FUNDOS:
        return _CACHE_FUNDOS[chave]

    if _PILLOW_DISPONIVEL:
        try:
            imagem = Image.open(caminho).convert("RGBA")
            if ajuste:
                imagem = _recolorir_imagem(imagem, *ajuste)
            if largura and altura:
                imagem = imagem.resize((largura, altura), Image.LANCZOS)
            imagem_tk = ImageTk.PhotoImage(imagem)
        except Exception:
            imagem_tk = None
    else:
        try:
            import tkinter as tk
            imagem_tk = tk.PhotoImage(file=caminho)
        except Exception:
            imagem_tk = None

    _CACHE_FUNDOS[chave] = imagem_tk
    return imagem_tk


def aplicar_fundo_canvas(canvas, nome_tela, largura, altura):
    imagem = imagem_fundo(nome_tela, largura, altura)
    if imagem is None:
        return None
    item = canvas.create_image(0, 0, image=imagem, anchor="nw")
    canvas.tag_lower(item)
    return imagem


def aplicar_fundo_frame(frame, nome_tela):
    imagem = imagem_fundo(nome_tela)
    if imagem is None:
        return None
    import tkinter as tk
    rotulo = tk.Label(frame, image=imagem, borderwidth=0)
    rotulo.image = imagem
    rotulo.place(x=0, y=0, relwidth=1, relheight=1)
    rotulo.lower()

    # quando a tela muda de tamanho (tela cheia), o fundo é refeito no tamanho novo
    def ao_redimensionar(evento):
        if getattr(rotulo, "_id_ajuste", None):
            rotulo.after_cancel(rotulo._id_ajuste)
        rotulo._id_ajuste = rotulo.after(80, lambda: ajustar(evento.width, evento.height))

    def ajustar(largura, altura):
        rotulo._id_ajuste = None
        nova = imagem_fundo(nome_tela, largura, altura)
        if nova is not None and rotulo.winfo_exists():
            rotulo.config(image=nova)
            rotulo.image = nova

    rotulo.bind("<Configure>", ao_redimensionar)
    return rotulo


def pillow_disponivel():
    return _PILLOW_DISPONIVEL
