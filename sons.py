import os
import threading
import time

try:
    import winsound
    _WINSOUND_DISPONIVEL = True
except ImportError:
    _WINSOUND_DISPONIVEL = False

PASTA_SONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sons")

SOM_MERGE = "merge.wav"
SOM_REPRODUCAO = "reproducao.wav"
SOM_FUSAO = "fusao.wav"
SOM_CORRUPCAO = "corrupcao.wav"
SOM_CONQUISTA = "conquista.wav"
SOM_GELADEIRA = "geladeira.wav"
SOM_CLIQUE = "clique.wav"
SOM_TROFEU = "trofeu.wav"

_SOM_ATIVADO = True


def definir_som_ativado(ativado):
    global _SOM_ATIVADO
    _SOM_ATIVADO = ativado


def som_esta_ativado():
    return _SOM_ATIVADO


_ULTIMA_VEZ = {}
INTERVALO_MINIMO = 0.12   # segundos: no 4× acontecem muitas fusões; assim os sons não viram uma "metralhadora"


def tocar(nome_arquivo):
    if not _SOM_ATIVADO or not _WINSOUND_DISPONIVEL:
        return
    agora = time.time()
    if agora - _ULTIMA_VEZ.get(nome_arquivo, 0) < INTERVALO_MINIMO:
        return
    _ULTIMA_VEZ[nome_arquivo] = agora
    caminho = os.path.join(PASTA_SONS, nome_arquivo)
    if not os.path.isfile(caminho):
        return
    threading.Thread(
        target=lambda: winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC),
        daemon=True,
    ).start()