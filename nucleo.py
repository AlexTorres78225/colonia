"""☣️ Núcleos Corrompidos (V2): o "chefão" da placa.

Ideia do Alex: um vírus gigante, maior que a Forma de Vida Suprema, que fica parado num lugar
sorteado e, de tempos em tempos, solta vírus pequenos que infectam os organismos.
Aparece 1 por troféu (até 4). O jogador tem três armas, compradas no Baú:

  🔮 Película         -> bolha em volta do Núcleo: segura as ondas de vírus até se romper
  ⚪ Glóbulos Brancos -> ficam perto do Núcleo soltando bolinhas brancas que caçam os vírus
  💉 Seringa          -> o único jeito de destruir o Núcleo: ele some na 3ª

Tudo aqui conta em quadros da simulação (1 quadro = 40 ms no 1×), então a pausa e o ⏩ valem.
Os desenhos do Alex entram sozinhos quando existirem em assets/nucleo/ (nucleo.png, pelicula.png,
globulo.png, seringa.png, virus.png e anticorpo.png); enquanto não existem, o jogo desenha formas simples.
"""
import math
import random

import bau_dados
import persistencia
import recursos
import sons
from evolucao_dados import tamanho_do_estagio, TOTAL_ESTAGIOS

QUADROS_POR_SEGUNDO = 25

RAIO_NUCLEO = round(tamanho_do_estagio(TOTAL_ESTAGIOS) * 1.5)   # maior que a Forma de Vida Suprema
SERINGAS_PARA_DESTRUIR = 3
ESPERA_PRIMEIRO_NUCLEO = 60 * QUADROS_POR_SEGUNDO    # o primeiro aparece 1 minuto depois de abrir a placa
ESPERA_ENTRE_NUCLEOS = 90 * QUADROS_POR_SEGUNDO      # depois de destruídos, voltam (todos juntos) em 1 min e meio
INTERVALO_ONDA = 10 * QUADROS_POR_SEGUNDO            # cada Núcleo solta uma onda de vírus a cada 10 s
MAXIMO_DE_VIRUS = 80

# vírus pequenos
RAIO_VIRUS = 4
VELOCIDADE_VIRUS = 1.6
VIDA_VIRUS = 15 * QUADROS_POR_SEGUNDO
VISAO_VIRUS = 320
CHANCE_INFECTAR = 0.6        # antes da Imunidade e do Guardião (que valem só metade contra esta cepa)

# Glóbulos Brancos
RAIO_BASE_GLOBULOS = 14
RAIO_SOLDADO = 5
VELOCIDADE_SOLDADO = 2.3
INTERVALO_SOLDADO = 40       # quadros entre uma bolinha branca e outra
MAXIMO_SOLDADOS = 6          # por Núcleo
VISAO_SOLDADO = 380

DURACAO_ANIMACAO_SERINGA = 18

CORES = {
    "corpo": "#4a0f3a", "borda": "#e0457b", "miolo": "#8a1f5c", "espinho": "#b0306a",
    "virus": "#e0457b", "virus_borda": "#ffb3cf", "pelicula": "#8fe3ff", "globulo": "#f4f8ff",
    "globulo_borda": "#9fc7e8", "texto": "#ffd6e6", "seringa": "#dfe9f2", "agulha": "#c0c8d0",
}


class Nucleo:
    def __init__(self, id_banco, x, y, seringas=0):
        self.id_banco = id_banco
        self.x = x
        self.y = y
        self.seringas = seringas
        self.proxima_onda = random.randint(INTERVALO_ONDA // 2, INTERVALO_ONDA)
        self.pelicula = 0               # quadros que a Película ainda dura (0 = sem Película)
        self.pelicula_resistencia = 0   # ondas que ela ainda segura
        self.globulos = 0               # quadros que os Glóbulos ainda ficam de guarda
        self.proximo_soldado = 0
        self.animacao_seringa = 0

    def raio(self):
        return RAIO_NUCLEO

    def base_dos_globulos(self):
        """Os Glóbulos ficam ao lado do Núcleo, um pouco abaixo e à direita."""
        distancia = RAIO_NUCLEO + 28
        return self.x + distancia * 0.7, self.y + distancia * 0.7


class Virus:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = random.uniform(0, 2 * math.pi)
        self.vida = VIDA_VIRUS
        self.alvo = None


class Soldado:
    """Bolinha branca dos Glóbulos: caça vírus; 'forca' = quantos vírus ela derruba antes de sumir."""

    def __init__(self, nucleo, x, y):
        self.nucleo = nucleo
        self.x = x
        self.y = y
        self.forca = bau_dados.resistencia_globulos()
        self.angulo = random.uniform(0, 2 * math.pi)


def _andar_ate(objeto, alvo_x, alvo_y, velocidade, curva=0.25):
    angulo_alvo = math.atan2(alvo_y - objeto.y, alvo_x - objeto.x)
    diferenca = (angulo_alvo - objeto.angulo + math.pi) % (2 * math.pi) - math.pi
    objeto.angulo += diferenca * curva
    objeto.x += math.cos(objeto.angulo) * velocidade
    objeto.y += math.sin(objeto.angulo) * velocidade


class GerenciadorNucleos:
    """Cuida dos Núcleos de uma tela (só a Simulação tem): nascer, soltar vírus, itens e desenho."""

    def __init__(self, tela):
        self.tela = tela
        self.nucleos = []
        self.virus = []
        self.soldados = []
        self.espera_novo = ESPERA_PRIMEIRO_NUCLEO

    # ---------- banco ----------

    def carregar(self):
        """Lê os Núcleos do save. Quem já estava na memória continua (com Película e Glóbulos ativos)."""
        linhas = persistencia.listar_nucleos()
        na_memoria = {n.id_banco: n for n in self.nucleos}
        self.nucleos = []
        for linha in linhas:
            nucleo = na_memoria.get(linha["id"]) or Nucleo(linha["id"], linha["x"], linha["y"], linha["seringas"])
            self.nucleos.append(nucleo)
        ids = {n.id_banco for n in self.nucleos}
        self.soldados = [s for s in self.soldados if s.nucleo.id_banco in ids]

    def recomecar(self):
        """Ciclo novo: a placa começa sem Núcleos e o primeiro demora um pouco para aparecer."""
        self.nucleos, self.virus, self.soldados = [], [], []
        self.espera_novo = ESPERA_PRIMEIRO_NUCLEO
        self.carregar()

    # ---------- consultas ----------

    def nucleo_em(self, x, y):
        for nucleo in self.nucleos:
            if math.hypot(nucleo.x - x, nucleo.y - y) <= nucleo.raio() + 10:
                return nucleo
        return None

    def problema_para(self, chave, nucleo):
        if chave == "pelicula" and nucleo.pelicula > 0:
            return "esse Núcleo já está dentro de uma Película."
        if chave == "globulos" and nucleo.globulos > 0:
            return "esse Núcleo já tem Glóbulos Brancos de guarda."
        return None

    # ---------- itens ----------

    def usar_pelicula(self, nucleo):
        nucleo.pelicula = bau_dados.duracao_pelicula() * QUADROS_POR_SEGUNDO
        nucleo.pelicula_resistencia = bau_dados.resistencia_pelicula()
        persistencia.incrementar_estatistica("peliculas_usadas_total")
        return (f"a Película envolveu o Núcleo: segura {nucleo.pelicula_resistencia} ondas por até "
                f"{bau_dados.duracao_pelicula()} s.")

    def usar_globulos(self, nucleo):
        nucleo.globulos = bau_dados.duracao_globulos() * QUADROS_POR_SEGUNDO
        nucleo.proximo_soldado = 0
        persistencia.incrementar_estatistica("globulos_usados_total")
        return f"os Glóbulos Brancos chegaram e ficam de guarda por {bau_dados.duracao_globulos()} s."

    def usar_seringa(self, nucleo):
        nucleo.seringas += 1
        nucleo.animacao_seringa = DURACAO_ANIMACAO_SERINGA
        if nucleo.seringas < SERINGAS_PARA_DESTRUIR:
            persistencia.atualizar_seringas_nucleo(nucleo.id_banco, nucleo.seringas)
            return f"Seringa aplicada! O Núcleo já levou {nucleo.seringas} de {SERINGAS_PARA_DESTRUIR}."
        self._destruir(nucleo)
        return f"o Núcleo Corrompido foi DESTRUÍDO! (+{bau_dados.GANHO_NUCLEO_DESTRUIDO} ⬡)"

    def _destruir(self, nucleo):
        persistencia.remover_nucleo(nucleo.id_banco)
        self.nucleos.remove(nucleo)
        self.soldados = [s for s in self.soldados if s.nucleo is not nucleo]
        persistencia.incrementar_estatistica("nucleos_destruidos_total")
        persistencia.adicionar_entrada_diario("☣️ Um Núcleo Corrompido foi destruído com a 3ª Seringa.")
        ganho = bau_dados.ganhar(bau_dados.GANHO_NUCLEO_DESTRUIDO)
        self.tela._mostrar_ganho(nucleo.x, nucleo.y - nucleo.raio(), ganho)
        sons.tocar(sons.SOM_CONQUISTA)
        if len(self.nucleos) < bau_dados.maximo_de_nucleos():
            self.espera_novo = ESPERA_ENTRE_NUCLEOS

    # ---------- simulação ----------

    def passo(self):
        self._talvez_nascer()
        for nucleo in self.nucleos:
            self._passo_do_nucleo(nucleo)
        self._empurrar_organismos()
        self._mover_virus()
        self._mover_soldados()

    def _talvez_nascer(self):
        if len(self.nucleos) >= bau_dados.maximo_de_nucleos():
            return
        self.espera_novo -= 1
        if self.espera_novo > 0:
            return
        self.espera_novo = ESPERA_ENTRE_NUCLEOS
        # nascem todos juntos: 1 por troféu (Bronze 1, Prata 2, Ouro 3, Diamante 4)
        quantos = bau_dados.maximo_de_nucleos() - len(self.nucleos)
        for _ in range(quantos):
            x, y = self._lugar_livre()
            self.nucleos.append(Nucleo(persistencia.criar_nucleo(x, y), x, y))
            persistencia.incrementar_estatistica("nucleos_surgidos_total")
        if quantos == 1:
            persistencia.adicionar_entrada_diario("☣️ Um Núcleo Corrompido surgiu na placa.")
            self.tela._mostrar_evento("☣️ Um NÚCLEO CORROMPIDO surgiu na placa! Veja no minimapa.")
        else:
            persistencia.adicionar_entrada_diario(f"☣️ {quantos} Núcleos Corrompidos surgiram na placa.")
            self.tela._mostrar_evento(f"☣️ {quantos} NÚCLEOS CORROMPIDOS surgiram na placa! Veja no minimapa.")
        sons.tocar(sons.SOM_CORRUPCAO)

    def _lugar_livre(self):
        """Um ponto sorteado longe das bordas e dos outros Núcleos."""
        largura, altura = self.tela.camera.largura_mundo, self.tela.camera.altura_mundo
        margem = RAIO_NUCLEO + 40
        x = y = 0
        for _tentativa in range(30):
            x, y = random.uniform(margem, largura - margem), random.uniform(margem, altura - margem)
            if all(math.hypot(n.x - x, n.y - y) > RAIO_NUCLEO * 4 for n in self.nucleos):
                break
        return x, y

    def _passo_do_nucleo(self, nucleo):
        if nucleo.animacao_seringa > 0:
            nucleo.animacao_seringa -= 1
        if nucleo.pelicula > 0:
            nucleo.pelicula -= 1
            if nucleo.pelicula == 0:
                self.tela._mostrar_evento("🔮 A Película se rompeu por causa do tempo!")
        if nucleo.globulos > 0:
            nucleo.globulos -= 1
            nucleo.proximo_soldado -= 1
            vivos = sum(1 for s in self.soldados if s.nucleo is nucleo)
            if nucleo.proximo_soldado <= 0 and vivos < MAXIMO_SOLDADOS:
                nucleo.proximo_soldado = INTERVALO_SOLDADO
                self.soldados.append(Soldado(nucleo, *nucleo.base_dos_globulos()))
            if nucleo.globulos == 0:
                self.soldados = [s for s in self.soldados if s.nucleo is not nucleo]
                self.tela._mostrar_evento("⚪ Os Glóbulos Brancos foram embora.")

        nucleo.proxima_onda -= 1
        if nucleo.proxima_onda > 0:
            return
        nucleo.proxima_onda = INTERVALO_ONDA
        if nucleo.pelicula > 0:
            # a Película segura a onda inteira, mas se desgasta
            nucleo.pelicula_resistencia -= 1
            if nucleo.pelicula_resistencia <= 0:
                nucleo.pelicula = 0
                self.tela._mostrar_evento("🔮 A Película não aguentou e se rompeu!")
            return
        quantidade = min(6, 2 + bau_dados.trofeus())   # ciclos mais altos, ondas maiores
        for _ in range(quantidade):
            if len(self.virus) >= MAXIMO_DE_VIRUS:
                break
            angulo = random.uniform(0, 2 * math.pi)
            virus = Virus(nucleo.x + math.cos(angulo) * nucleo.raio(), nucleo.y + math.sin(angulo) * nucleo.raio())
            virus.angulo = angulo
            self.virus.append(virus)

    def _empurrar_organismos(self):
        """O Núcleo é sólido: os organismos não passam por cima dele."""
        for nucleo in self.nucleos:
            for organismo in self.tela.organismos:
                if organismo is self.tela.arrastando:
                    continue
                dx, dy = organismo.x - nucleo.x, organismo.y - nucleo.y
                distancia = math.hypot(dx, dy)
                minimo = nucleo.raio() + organismo.raio()
                if 0 < distancia < minimo:
                    organismo.x = nucleo.x + dx / distancia * minimo
                    organismo.y = nucleo.y + dy / distancia * minimo

    def _alvo_do_virus(self, virus):
        melhor, menor = None, VISAO_VIRUS
        for organismo in self.tela.organismos:
            if organismo.tipo == "fusao" or organismo.comportamento == "Infectado":
                continue
            distancia = math.hypot(organismo.x - virus.x, organismo.y - virus.y)
            if distancia < menor:
                melhor, menor = organismo, distancia
        return melhor

    def _mover_virus(self):
        largura, altura = self.tela.camera.largura_mundo, self.tela.camera.altura_mundo
        restantes = []
        for virus in self.virus:
            virus.vida -= 1
            if virus.vida <= 0:
                continue
            alvo = virus.alvo
            # a cada 10 quadros o vírus procura o alvo de novo (o antigo pode ter se fundido ou sido infectado)
            if virus.vida % 10 == 0 or alvo is None or alvo.comportamento == "Infectado":
                alvo = virus.alvo = self._alvo_do_virus(virus)
            if alvo is not None:
                _andar_ate(virus, alvo.x, alvo.y, VELOCIDADE_VIRUS)
                encostou = math.hypot(alvo.x - virus.x, alvo.y - virus.y) <= alvo.raio() + RAIO_VIRUS
                if encostou and alvo in self.tela.organismos:
                    # encostou: o vírus se gasta, e o organismo pode pegar (Imunidade e Guardião valem metade)
                    if random.random() < self.tela.chance_de_pegar(alvo, True, CHANCE_INFECTAR):
                        self.tela._tornar_infectado(alvo, do_nucleo=True)
                        persistencia.incrementar_estatistica("contagio_total")
                        self.tela._mostrar_evento(f"☣️ O vírus do Núcleo infectou um {alvo.dados_estagio()['nome']}")
                        sons.tocar(sons.SOM_CORRUPCAO)
                    continue
            else:
                virus.angulo += random.uniform(-0.4, 0.4)
                virus.x += math.cos(virus.angulo) * VELOCIDADE_VIRUS
                virus.y += math.sin(virus.angulo) * VELOCIDADE_VIRUS
            virus.x = max(RAIO_VIRUS, min(largura - RAIO_VIRUS, virus.x))
            virus.y = max(RAIO_VIRUS, min(altura - RAIO_VIRUS, virus.y))
            restantes.append(virus)
        self.virus = restantes

    def _mover_soldados(self):
        restantes = []
        for soldado in self.soldados:
            base_x, base_y = soldado.nucleo.base_dos_globulos()
            alvo, menor = None, VISAO_SOLDADO
            for virus in self.virus:
                distancia = math.hypot(virus.x - base_x, virus.y - base_y)
                if distancia < menor:
                    alvo, menor = virus, distancia
            if alvo is None:
                # sem vírus por perto: a bolinha fica rondando a base
                soldado.angulo += 0.08
                soldado.x = base_x + math.cos(soldado.angulo) * 24
                soldado.y = base_y + math.sin(soldado.angulo) * 24
                restantes.append(soldado)
                continue
            _andar_ate(soldado, alvo.x, alvo.y, VELOCIDADE_SOLDADO, curva=0.4)
            if math.hypot(alvo.x - soldado.x, alvo.y - soldado.y) <= RAIO_SOLDADO + RAIO_VIRUS + 2:
                self.virus.remove(alvo)
                soldado.forca -= 1
                if soldado.forca <= 0:
                    continue
            restantes.append(soldado)
        self.soldados = restantes

    # ---------- desenho ----------

    def desenhar(self):
        canvas, camera = self.tela.canvas, self.tela.camera
        canvas.delete("nucleo")
        self._imagens = []   # o Tkinter apaga a imagem se ninguém guardar uma referência
        zoom = camera.zoom
        for nucleo in self.nucleos:
            x, y = camera.para_tela(nucleo.x, nucleo.y)
            r = nucleo.raio() * zoom
            if self._fora_da_tela(x, y, r * 1.5):
                continue
            self._desenhar_nucleo(canvas, nucleo, x, y, r)
        for virus in self.virus:
            x, y = camera.para_tela(virus.x, virus.y)
            r = max(2, RAIO_VIRUS * zoom)
            if self._fora_da_tela(x, y, r):
                continue
            if not self._imagem(canvas, "virus", x, y, r):
                canvas.create_oval(x - r, y - r, x + r, y + r, fill=CORES["virus"], outline=CORES["virus_borda"],
                                   tags="nucleo")
        for soldado in self.soldados:
            x, y = camera.para_tela(soldado.x, soldado.y)
            r = max(2.5, RAIO_SOLDADO * zoom)
            if not self._fora_da_tela(x, y, r * 2) and not self._imagem(canvas, "anticorpo", x, y, r):
                self._desenhar_anticorpo(canvas, x, y, r, soldado.angulo, zoom)
        canvas.tag_raise("minimapa")

    def _desenhar_anticorpo(self, canvas, x, y, tamanho, angulo, zoom):
        """Anticorpo em forma de Y (como os de verdade), com os braços virados para onde ele anda."""
        frente_x, frente_y = math.cos(angulo), math.sin(angulo)
        cauda = (x - frente_x * tamanho, y - frente_y * tamanho)
        bracos = [(x + math.cos(angulo + abertura) * tamanho, y + math.sin(angulo + abertura) * tamanho)
                  for abertura in (-0.6, 0.6)]
        for cor, largura in ((CORES["globulo_borda"], max(2, 2.5 * zoom)), (CORES["globulo"], max(1, 1.2 * zoom))):
            canvas.create_line(*cauda, x, y, fill=cor, width=largura, capstyle="round", tags="nucleo")
            for ponta in bracos:
                canvas.create_line(x, y, *ponta, fill=cor, width=largura, capstyle="round", tags="nucleo")

    def _fora_da_tela(self, x, y, folga):
        camera = self.tela.camera
        return x < -folga or y < -folga or x > camera.largura_tela + folga or y > camera.altura_tela + folga

    def _imagem(self, canvas, nome, x, y, raio):
        """Usa o desenho do Alex (assets/nucleo/<nome>.png) se ele existir. Devolve False se não existir."""
        imagem = recursos.imagem_nucleo_redimensionada(nome, int(raio * 2))
        if imagem is None:
            return False
        self._imagens.append(imagem)
        canvas.create_image(x, y, image=imagem, tags="nucleo")
        return True

    def _desenhar_nucleo(self, canvas, nucleo, x, y, r):
        zoom = self.tela.camera.zoom
        # perto de soltar a onda, o Núcleo "pulsa"
        pulso = 1 + 0.06 * max(0, 1 - nucleo.proxima_onda / 50)
        if not self._imagem(canvas, "nucleo", x, y, r * pulso):
            for indice in range(14):
                angulo = indice * 2 * math.pi / 14
                canvas.create_line(x + math.cos(angulo) * r * 0.9, y + math.sin(angulo) * r * 0.9,
                                   x + math.cos(angulo) * r * 1.2 * pulso, y + math.sin(angulo) * r * 1.2 * pulso,
                                   fill=CORES["espinho"], width=max(2, 4 * zoom), tags="nucleo")
            canvas.create_oval(x - r * pulso, y - r * pulso, x + r * pulso, y + r * pulso, fill=CORES["corpo"],
                               outline=CORES["borda"], width=max(2, 3 * zoom), tags="nucleo")
            canvas.create_oval(x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45, fill=CORES["miolo"],
                               outline="", tags="nucleo")
            canvas.create_text(x, y, text="☣", fill=CORES["texto"], font=("Segoe UI", max(8, int(r * 0.45))),
                               tags="nucleo")

        if nucleo.pelicula > 0:
            rp = r * 1.35
            if not self._imagem(canvas, "pelicula", x, y, rp):
                canvas.create_oval(x - rp, y - rp, x + rp, y + rp, outline=CORES["pelicula"],
                                   width=max(2, 3 * zoom), tags="nucleo")
                canvas.create_oval(x - rp * 0.94, y - rp * 0.94, x + rp * 0.94, y + rp * 0.94,
                                   outline=CORES["pelicula"], dash=(4, 6), tags="nucleo")
            segundos = math.ceil(nucleo.pelicula / QUADROS_POR_SEGUNDO)
            canvas.create_text(x, y + rp + 12, text=f"🔮 {segundos}s • {nucleo.pelicula_resistencia} onda(s)",
                               fill=CORES["pelicula"], font=("Segoe UI", 9, "bold"), tags="nucleo")

        if nucleo.globulos > 0:
            bx, by = self.tela.camera.para_tela(*nucleo.base_dos_globulos())
            rb = RAIO_BASE_GLOBULOS * zoom
            if not self._imagem(canvas, "globulo", bx, by, rb):
                canvas.create_oval(bx - rb, by - rb, bx + rb, by + rb, fill=CORES["globulo"],
                                   outline=CORES["globulo_borda"], width=2, tags="nucleo")
                canvas.create_oval(bx - rb * 0.4, by - rb * 0.4, bx + rb * 0.4, by + rb * 0.4,
                                   fill=CORES["globulo_borda"], outline="", tags="nucleo")

        canvas.create_text(x, y - r * 1.35 - 14, text=f"💉 {nucleo.seringas}/{SERINGAS_PARA_DESTRUIR}",
                           fill=CORES["texto"], font=("Segoe UI", 10, "bold"), tags="nucleo")

        if nucleo.animacao_seringa > 0:
            # a seringa gigante desce e espeta o Núcleo
            descida = 1 - nucleo.animacao_seringa / DURACAO_ANIMACAO_SERINGA
            ponta_y = y - r * 1.6 + r * 0.9 * descida
            if not self._imagem(canvas, "seringa", x, ponta_y - r * 0.6, r * 0.6):
                largura = r * 0.18
                canvas.create_line(x, ponta_y, x, ponta_y - r * 0.35, fill=CORES["agulha"], width=max(2, 3 * zoom),
                                   tags="nucleo")
                canvas.create_rectangle(x - largura, ponta_y - r * 0.35, x + largura, ponta_y - r * 1.1,
                                        fill=CORES["seringa"], outline="#7f9fb5", width=2, tags="nucleo")
                canvas.create_rectangle(x - largura * 1.8, ponta_y - r * 1.1, x + largura * 1.8, ponta_y - r * 1.18,
                                        fill=CORES["seringa"], outline="#7f9fb5", tags="nucleo")

    def desenhar_no_minimapa(self, x0, y0, escala):
        canvas = self.tela.canvas
        for nucleo in self.nucleos:
            px, py = x0 + nucleo.x * escala, y0 + nucleo.y * escala
            r = max(3, nucleo.raio() * escala * 1.4)
            canvas.create_oval(px - r, py - r, px + r, py + r, fill=CORES["borda"], outline="#ffffff",
                               tags="minimapa")
