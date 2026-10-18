import random
import math
import time
from evolucao_dados import dados_completos_estagio, tamanho_do_estagio
from comportamento import modificadores
from camera import CAMERA_PADRAO
import recursos

DURACAO_SELO_NOVO = 10  # segundos que o ❓ de espécie nova fica visível

# Aparência dos selos: (cor da bolinha, cor do símbolo)
ESTILO_SELOS = {
    "?": ("#f2c94c", "#1a1a1a"),
    "!": ("#e04848", "#ffffff"),
}


class Organismo:
    def __init__(self, id_banco, estagio, x, y, velocidade_mod, tamanho_mod,
                 comportamento, tipo="normal", local="placa", variante=""):
        self.id_banco = id_banco
        self.estagio = estagio
        self.x = x
        self.y = y
        self.velocidade_mod = velocidade_mod
        self.tamanho_mod = tamanho_mod
        self.comportamento = comportamento
        self.tipo = tipo
        self.local = local
        self.variante = variante or ""
        self.recarga = 0
        self.recarga_contagio = 0
        self.recarga_caca = 0          # Predador: espera entre uma "refeição" e outra
        self.hospedeiro_id = None      # Simbionte: id do organismo que ele segue
        self._fora_da_tela = False
        self.novo_ate = 0
        self.angulo = random.uniform(0, 2 * math.pi)
        self._descanso = 0
        self._passos_zigue = 0
        self.itens_canvas = []
        self.itens_selo = []
        self._selo_desenhado = None
        self._imagem_referencia = None

    # ---------- dados ----------

    def dados_estagio(self):
        return dados_completos_estagio(self.estagio)

    def raio(self):
        return tamanho_do_estagio(self.estagio) * self.tamanho_mod * modificadores(self.comportamento)["tamanho_mult"]

    def velocidade_efetiva(self):
        return modificadores(self.comportamento)["velocidade_mult"] * self.velocidade_mod

    def sofreu_interferencia(self):
        return self.tipo == "fusao" or not modificadores(self.comportamento)["natural"]

    def marcar_como_especie_nova(self):
        self.novo_ate = time.time() + DURACAO_SELO_NOVO

    def selo(self):
        if self.novo_ate > time.time():
            return "?"
        if self.sofreu_interferencia():
            return "!"
        return None

    # ---------- movimento ----------

    def mover(self, largura, altura, alvo=None, margem=20, atracao=None, forca_atracao=0.0):
        """Anda um passo. O jeito de andar vem do comportamento (coluna 'movimento').

        atracao: um organismo igual por perto (Feromônio do Baú); o ângulo vira um pouco na direção dele.
        """
        movimento = modificadores(self.comportamento)["movimento"]

        if movimento == "suave":
            if self._descanso > 0 and atracao is None:
                self._descanso -= 1
                return
            if random.random() < 0.004:
                self._descanso = random.randint(25, 60)
            self.angulo += random.uniform(-0.15, 0.15)
        elif movimento == "reto":
            self.angulo += random.uniform(-0.05, 0.05)
        elif movimento in ("persegue", "caca", "segue") and alvo is not None:
            # Irritado persegue o vizinho, o Predador caça a presa e o Simbionte segue o hospedeiro
            angulo_alvo = math.atan2(alvo.y - self.y, alvo.x - self.x)
            diferenca = (angulo_alvo - self.angulo + math.pi) % (2 * math.pi) - math.pi
            curva = 0.35 if movimento == "segue" else 0.15
            self.angulo += diferenca * curva + random.uniform(-0.1, 0.1)
            if movimento == "segue" and self.distancia_para(alvo) < self.raio() + alvo.raio() + 6:
                return   # já está grudado no hospedeiro: fica parado junto dele
        elif movimento == "patrulha":
            self.angulo += 0.04   # o Guardião anda em círculos
        elif movimento == "zigue":
            self._passos_zigue += 1
            if self._passos_zigue >= 10:
                self._passos_zigue = 0
                self.angulo += random.choice([-1.1, 1.1])
        elif movimento == "erratico":
            self.angulo += random.uniform(-1.2, 1.2)
        else:
            self.angulo += random.uniform(-0.3, 0.3)

        if atracao is not None and forca_atracao > 0:
            angulo_par = math.atan2(atracao.y - self.y, atracao.x - self.x)
            diferenca = (angulo_par - self.angulo + math.pi) % (2 * math.pi) - math.pi
            self.angulo += diferenca * forca_atracao

        velocidade = self.velocidade_efetiva()
        self.x += math.cos(self.angulo) * velocidade
        self.y += math.sin(self.angulo) * velocidade
        raio = self.raio()
        if self.x < margem + raio or self.x > largura - margem - raio:
            self.angulo = math.pi - self.angulo
        if self.y < margem + raio or self.y > altura - margem - raio:
            self.angulo = -self.angulo
        self.x = max(margem + raio, min(largura - margem - raio, self.x))
        self.y = max(margem + raio, min(altura - margem - raio, self.y))

    def distancia_para(self, outro):
        return math.hypot(self.x - outro.x, self.y - outro.y)

    def esta_encostando(self, outro):
        return self.distancia_para(outro) <= (self.raio() + outro.raio())

    def contem_ponto(self, x, y):
        return math.hypot(self.x - x, self.y - y) <= max(self.raio(), 6)

    # ---------- desenho ----------

    def _posicao_na_tela(self, camera):
        x_tela, y_tela = camera.para_tela(self.x, self.y)
        return x_tela, y_tela, self.raio() * camera.zoom

    def _imagem(self, tamanho_pixels):
        imagem = None
        if self.tipo == "fusao":
            imagem = recursos.imagem_fusao_redimensionada(self.variante, tamanho_pixels)
        if imagem is None:
            imagem = recursos.imagem_organismo_redimensionada(self.estagio, tamanho_pixels)
        return imagem

    def criar_no_canvas(self, canvas, camera=CAMERA_PADRAO):
        x, y, raio = self._posicao_na_tela(camera)
        imagem = self._imagem(int(raio * 2))
        if imagem is not None:
            self._imagem_referencia = imagem
            self.itens_canvas = [canvas.create_image(x, y, image=imagem)]
        else:
            # Só acontece se o PNG sumir da pasta assets: um círculo simples na cor do estágio.
            cor = self.dados_estagio()["cor"]
            self.itens_canvas = [canvas.create_oval(x - raio, y - raio, x + raio, y + raio,
                                                    fill=cor, outline="")]
        self._selo_desenhado = None
        self.itens_selo = []
        self._atualizar_selo(canvas, x, y, raio, camera.zoom)
        return self.itens_canvas

    def _posicao_selo(self, x, y, raio, zoom):
        raio_selo = 6 + 2 * zoom
        return x + raio * 0.75, y - raio * 0.75, raio_selo

    def _atualizar_selo(self, canvas, x, y, raio, zoom):
        selo = self.selo()
        sx, sy, raio_selo = self._posicao_selo(x, y, raio, zoom)
        if selo != self._selo_desenhado:
            for item in self.itens_selo:
                canvas.delete(item)
            self.itens_selo = []
            self._selo_desenhado = selo
            if selo is None:
                return
            cor_fundo, cor_texto = ESTILO_SELOS[selo]
            bolinha = canvas.create_oval(sx - raio_selo, sy - raio_selo, sx + raio_selo, sy + raio_selo,
                                         fill=cor_fundo, outline="#1a1a1a", width=1)
            texto = canvas.create_text(sx, sy, text=selo, fill=cor_texto,
                                       font=("Segoe UI", int(raio_selo * 1.2), "bold"))
            self.itens_selo = [bolinha, texto]
        elif self.itens_selo:
            canvas.coords(self.itens_selo[0], sx - raio_selo, sy - raio_selo, sx + raio_selo, sy + raio_selo)
            canvas.coords(self.itens_selo[1], sx, sy)

    def atualizar_no_canvas(self, canvas, camera=CAMERA_PADRAO):
        if not self.itens_canvas:
            return
        x, y, raio = self._posicao_na_tela(camera)
        # desempenho: se já estava fora da tela e continua fora, não precisa mexer no desenho
        folga = raio + 40
        fora = (x < -folga or y < -folga or x > camera.largura_tela + folga or y > camera.altura_tela + folga)
        if fora and self._fora_da_tela:
            return
        self._fora_da_tela = fora
        if self._imagem_referencia is not None:
            canvas.coords(self.itens_canvas[0], x, y)
        else:
            canvas.coords(self.itens_canvas[0], x - raio, y - raio, x + raio, y + raio)
        self._atualizar_selo(canvas, x, y, raio, camera.zoom)

    def redesenhar(self, canvas, camera=CAMERA_PADRAO):
        """Apaga e desenha de novo (usado quando o organismo muda de comportamento)."""
        self.remover_do_canvas(canvas)
        self.criar_no_canvas(canvas, camera)

    def remover_do_canvas(self, canvas):
        for item in self.itens_canvas + self.itens_selo:
            canvas.delete(item)
        self.itens_canvas = []
        self.itens_selo = []
        self._selo_desenhado = None

    # ---------- banco ----------

    @staticmethod
    def a_partir_de_linha(linha):
        return Organismo(
            id_banco=linha.get("id"),
            estagio=linha["estagio"],
            x=linha["x"],
            y=linha["y"],
            velocidade_mod=linha["velocidade_mod"],
            tamanho_mod=linha["tamanho_mod"],
            comportamento=linha["comportamento"],
            tipo=linha.get("tipo", "normal"),
            local=linha.get("local") or "placa",
            variante=linha.get("variante") or "",
        )
