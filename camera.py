ZOOM_MINIMO = 1.0
ZOOM_MAXIMO = 3.0
PASSO_ZOOM = 0.25


class Camera:
    """Mostra um pedaço do mundo (onde os organismos vivem) na tela, com zoom.

    O mundo pode ser maior que a tela: a câmera guarda qual canto do mundo
    (self.x, self.y) aparece no canto de cima/esquerda da tela.
    """

    def __init__(self, largura_tela, altura_tela, largura_mundo=None, altura_mundo=None):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.largura_mundo = largura_mundo or largura_tela
        self.altura_mundo = altura_mundo or altura_tela
        self.zoom = 1.0
        self.zoom_maximo = ZOOM_MAXIMO   # a Lente Potente do Baú aumenta este valor
        self.x = 0.0
        self.y = 0.0

    def para_tela(self, x, y):
        return (x - self.x) * self.zoom, (y - self.y) * self.zoom

    def para_mundo(self, x_tela, y_tela):
        return self.x + x_tela / self.zoom, self.y + y_tela / self.zoom

    def largura_visivel(self):
        return self.largura_tela / self.zoom

    def altura_visivel(self):
        return self.altura_tela / self.zoom

    def limitar(self):
        self.x = max(0.0, min(self.largura_mundo - self.largura_visivel(), self.x))
        self.y = max(0.0, min(self.altura_mundo - self.altura_visivel(), self.y))

    def mover(self, dx_tela, dy_tela):
        """Anda com a câmera; a distância é em pixels da tela (fica igual em qualquer zoom)."""
        self.x += dx_tela / self.zoom
        self.y += dy_tela / self.zoom
        self.limitar()

    def centralizar_em(self, x, y):
        self.x = x - self.largura_visivel() / 2
        self.y = y - self.altura_visivel() / 2
        self.limitar()

    def aplicar_zoom(self, novo_zoom, x_tela, y_tela):
        """Muda o zoom mantendo parado o ponto que está embaixo do mouse."""
        novo_zoom = max(ZOOM_MINIMO, min(self.zoom_maximo, novo_zoom))
        mundo_x, mundo_y = self.para_mundo(x_tela, y_tela)
        self.zoom = novo_zoom
        self.x = mundo_x - x_tela / self.zoom
        self.y = mundo_y - y_tela / self.zoom
        self.limitar()


CAMERA_PADRAO = Camera(1, 1)
