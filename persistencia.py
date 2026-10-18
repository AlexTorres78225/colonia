import sqlite3
import json
import os
import sys
from datetime import datetime
from conquistas import gerar_lista_conquistas
from evolucao_dados import TOTAL_ESTAGIOS

# Dois tipos de banco:
#   contas.db           -> só as contas (usuário, senha com hash, pergunta de segurança)
#   saves/conta_N.db    -> o progresso de UMA conta (colônia, geladeira, diário, conquistas, manual)
# Assim cada conta tem o seu próprio jogo e nada vaza de uma para outra.
NOME_BANCO_CONTAS = "contas.db"
PASTA_SAVES = "saves"

_conexao_contas = None
_conexao_save = None
_caminho_save = None


def _pasta_do_projeto():
    """Onde ficam os dados do jogador (contas, saves e diários arquivados).

    - Rodando pelo PyCharm: na pasta do projeto, como sempre.
    - Rodando como Colonia.exe (versão do itch.io): em AppData\\Roaming\\Colonia, o lugar padrão do Windows
      para dados de jogos. Assim o jogo funciona mesmo instalado em "Arquivos de Programas" e uma
      versão nova do .exe não apaga o progresso.
    """
    if getattr(sys, "frozen", False):   # o PyInstaller marca o programa como "frozen" quando vira .exe
        pasta = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Colonia")
        os.makedirs(pasta, exist_ok=True)
        return pasta
    return os.path.dirname(os.path.abspath(__file__))


def _abrir_conexao(caminho):
    conexao = sqlite3.connect(caminho, check_same_thread=False)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA journal_mode = WAL")
    conexao.execute("PRAGMA synchronous = NORMAL")
    return conexao


# ======================================================================
# CONTAS
# ======================================================================

def conectar_contas():
    global _conexao_contas
    if _conexao_contas is None:
        _conexao_contas = _abrir_conexao(os.path.join(_pasta_do_projeto(), NOME_BANCO_CONTAS))
        _conexao_contas.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_usuario TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                sal TEXT NOT NULL,
                pergunta_seguranca TEXT NOT NULL,
                resposta_hash TEXT NOT NULL,
                resposta_sal TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)
        _conexao_contas.commit()
    return _conexao_contas


def criar_usuario_db(nome_usuario, senha_hash, sal, pergunta_seguranca, resposta_hash, resposta_sal):
    conexao = conectar_contas()
    conexao.execute(
        "INSERT INTO usuarios (nome_usuario, senha_hash, sal, pergunta_seguranca, resposta_hash, "
        "resposta_sal, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (nome_usuario, senha_hash, sal, pergunta_seguranca, resposta_hash, resposta_sal,
         datetime.now().isoformat()),
    )
    conexao.commit()


def obter_usuario(nome_usuario):
    conexao = conectar_contas()
    linha = conexao.execute(
        "SELECT * FROM usuarios WHERE nome_usuario = ?", (nome_usuario,)
    ).fetchone()
    return dict(linha) if linha else None


def atualizar_senha(nome_usuario, novo_hash, novo_sal):
    conexao = conectar_contas()
    conexao.execute(
        "UPDATE usuarios SET senha_hash = ?, sal = ? WHERE nome_usuario = ?",
        (novo_hash, novo_sal, nome_usuario),
    )
    conexao.commit()


def atualizar_resposta(nome_usuario, novo_hash, novo_sal):
    conexao = conectar_contas()
    conexao.execute(
        "UPDATE usuarios SET resposta_hash = ?, resposta_sal = ? WHERE nome_usuario = ?",
        (novo_hash, novo_sal, nome_usuario),
    )
    conexao.commit()


def excluir_usuario(nome_usuario):
    """Apaga a conta e o arquivo de save dela (o jogador tem controle total dos próprios dados)."""
    global _caminho_save
    usuario = obter_usuario(nome_usuario)
    if usuario is None:
        return
    caminho = os.path.join(_pasta_do_projeto(), PASTA_SAVES, f"conta_{usuario['id']}.db")
    if _caminho_save == caminho:
        fechar_conexao()
        _caminho_save = None
    for sufixo in ("", "-wal", "-shm"):
        if os.path.exists(caminho + sufixo):
            os.remove(caminho + sufixo)
    conexao = conectar_contas()
    conexao.execute("DELETE FROM usuarios WHERE id = ?", (usuario["id"],))
    conexao.commit()


# ======================================================================
# SAVE DA CONTA
# ======================================================================

def abrir_save(nome_usuario):
    """Chamada logo depois do login: a partir daqui tudo lê e grava no save dessa conta."""
    global _conexao_save, _caminho_save
    fechar_conexao()
    usuario = obter_usuario(nome_usuario)
    if usuario is None:
        raise ValueError(f"Conta não encontrada: {nome_usuario}")
    pasta_saves = os.path.join(_pasta_do_projeto(), PASTA_SAVES)
    os.makedirs(pasta_saves, exist_ok=True)
    _caminho_save = os.path.join(pasta_saves, f"conta_{usuario['id']}.db")
    inicializar_banco()


def conectar():
    global _conexao_save
    if _caminho_save is None:
        raise RuntimeError("Nenhum save aberto. Faça login antes (persistencia.abrir_save).")
    if _conexao_save is None:
        _conexao_save = _abrir_conexao(_caminho_save)
    return _conexao_save


def fechar_conexao():
    global _conexao_save
    if _conexao_save is not None:
        _conexao_save.commit()
        _conexao_save.close()
        _conexao_save = None


def inicializar_banco():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organismos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estagio INTEGER NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            velocidade_mod REAL NOT NULL,
            tamanho_mod REAL NOT NULL,
            comportamento TEXT NOT NULL,
            tipo TEXT DEFAULT 'normal',
            criado_em TEXT NOT NULL,
            local TEXT DEFAULT 'placa',
            variante TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geladeira (
            slot INTEGER PRIMARY KEY,
            nome TEXT,
            dados_json TEXT,
            data_salvo TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conquistas (
            chave TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            desbloqueada INTEGER DEFAULT 0,
            data_desbloqueio TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estatisticas (
            chave TEXT PRIMARY KEY,
            valor INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estagios_descobertos (
            estagio INTEGER PRIMARY KEY,
            descoberto INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    # Baú: nível de cada upgrade comprado e quantos frascos de cada tipo o jogador tem
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upgrades (
            chave TEXT PRIMARY KEY,
            nivel INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            chave TEXT PRIMARY KEY,
            quantidade INTEGER DEFAULT 0
        )
    """)

    # Manual por ciclo: o que foi descoberto em cada ciclo (nunca é apagado)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS descobertas_ciclo (
            ciclo INTEGER,
            estagio INTEGER,
            PRIMARY KEY (ciclo, estagio)
        )
    """)

    lista = gerar_lista_conquistas()
    for conquista in lista:
        cursor.execute(
            "INSERT OR IGNORE INTO conquistas (chave, nome, descricao, categoria, desbloqueada) "
            "VALUES (?, ?, ?, ?, 0)",
            (conquista["chave"], conquista["nome"], conquista["descricao"], conquista["categoria"]),
        )
        # nome e descrição podem ter mudado numa versão nova do jogo
        cursor.execute("UPDATE conquistas SET nome = ?, descricao = ?, categoria = ? WHERE chave = ?",
                       (conquista["nome"], conquista["descricao"], conquista["categoria"], conquista["chave"]))
    # conquistas que não existem mais (ex.: o marco antigo de 5000) saem da lista
    marcadores = ",".join("?" for _ in lista)
    cursor.execute(f"DELETE FROM conquistas WHERE chave NOT IN ({marcadores})", [c["chave"] for c in lista])

    for estagio in range(1, TOTAL_ESTAGIOS + 1):
        cursor.execute(
            "INSERT OR IGNORE INTO estagios_descobertos (estagio, descoberto) VALUES (?, 0)",
            (estagio,),
        )

    # saves antigos (antes do Manual por ciclo): os ciclos já fechados contam como completos
    # e o ciclo atual copia o que já estava descoberto
    conexao.commit()
    ciclo = ciclo_atual()
    for ciclo_fechado in range(1, ciclo):
        for estagio in range(1, TOTAL_ESTAGIOS + 1):
            cursor.execute("INSERT OR IGNORE INTO descobertas_ciclo (ciclo, estagio) VALUES (?, ?)",
                           (ciclo_fechado, estagio))
    cursor.execute("INSERT OR IGNORE INTO descobertas_ciclo (ciclo, estagio) "
                   "SELECT ?, estagio FROM estagios_descobertos WHERE descoberto = 1", (ciclo,))

    conexao.commit()


# ---------- organismos ----------

def criar_organismo(estagio, x, y, velocidade_mod, tamanho_mod, comportamento, tipo="normal",
                    local="placa", variante=""):
    conexao = conectar()
    cursor = conexao.execute(
        "INSERT INTO organismos (estagio, x, y, velocidade_mod, tamanho_mod, comportamento, "
        "tipo, criado_em, local, variante) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (estagio, x, y, velocidade_mod, tamanho_mod, comportamento, tipo,
         datetime.now().isoformat(), local, variante),
    )
    novo_id = cursor.lastrowid
    conexao.commit()
    return novo_id


def listar_organismos(local=None):
    conexao = conectar()
    if local is None:
        linhas = conexao.execute("SELECT * FROM organismos").fetchall()
    else:
        linhas = conexao.execute("SELECT * FROM organismos WHERE local = ?", (local,)).fetchall()
    return [dict(linha) for linha in linhas]


def contar_organismos():
    conexao = conectar()
    linha = conexao.execute("SELECT COUNT(*) AS total FROM organismos").fetchone()
    return linha["total"]


def atualizar_posicao(organismo_id, x, y):
    conexao = conectar()
    conexao.execute("UPDATE organismos SET x = ?, y = ? WHERE id = ?", (x, y, organismo_id))
    conexao.commit()


def atualizar_posicoes_em_lote(lista_id_x_y):
    if not lista_id_x_y:
        return
    conexao = conectar()
    conexao.executemany(
        "UPDATE organismos SET x = ?, y = ? WHERE id = ?",
        [(x, y, organismo_id) for (organismo_id, x, y) in lista_id_x_y],
    )
    conexao.commit()


def mover_organismo_para(organismo_id, local, x, y):
    conexao = conectar()
    conexao.execute(
        "UPDATE organismos SET local = ?, x = ?, y = ? WHERE id = ?", (local, x, y, organismo_id)
    )
    conexao.commit()


def atualizar_estagio(organismo_id, estagio):
    conexao = conectar()
    conexao.execute("UPDATE organismos SET estagio = ? WHERE id = ?", (estagio, organismo_id))
    conexao.commit()


def atualizar_comportamento(organismo_id, comportamento):
    conexao = conectar()
    conexao.execute("UPDATE organismos SET comportamento = ? WHERE id = ?", (comportamento, organismo_id))
    conexao.commit()


def remover_organismo(organismo_id):
    conexao = conectar()
    conexao.execute("DELETE FROM organismos WHERE id = ?", (organismo_id,))
    conexao.commit()


def limitar_populacao(maximo):
    conexao = conectar()
    linhas_manter = conexao.execute(
        "SELECT id FROM organismos ORDER BY id DESC LIMIT ?", (maximo,)
    ).fetchall()
    ids_manter = [linha["id"] for linha in linhas_manter]
    if not ids_manter:
        return 0
    marcadores = ",".join("?" for _ in ids_manter)
    cursor = conexao.execute(
        f"DELETE FROM organismos WHERE id NOT IN ({marcadores})", ids_manter
    )
    removidos = cursor.rowcount
    conexao.commit()
    return removidos


def limpar_colonia(local=None):
    conexao = conectar()
    if local is None:
        conexao.execute("DELETE FROM organismos")
    else:
        conexao.execute("DELETE FROM organismos WHERE local = ?", (local,))
    conexao.commit()


# ---------- geladeira ----------

def salvar_slot_geladeira(slot, nome):
    organismos = listar_organismos()
    dados_json = json.dumps(organismos)
    conexao = conectar()
    conexao.execute(
        "INSERT INTO geladeira (slot, nome, dados_json, data_salvo) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(slot) DO UPDATE SET nome = excluded.nome, dados_json = excluded.dados_json, "
        "data_salvo = excluded.data_salvo",
        (slot, nome, dados_json, datetime.now().isoformat()),
    )
    conexao.commit()


def carregar_slot_geladeira(slot):
    conexao = conectar()
    linha = conexao.execute("SELECT * FROM geladeira WHERE slot = ?", (slot,)).fetchone()
    if not linha:
        return None
    organismos = json.loads(linha["dados_json"])
    limpar_colonia()
    for organismo in organismos:
        conexao.execute(
            "INSERT INTO organismos (estagio, x, y, velocidade_mod, tamanho_mod, comportamento, "
            "tipo, criado_em, local, variante) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (organismo["estagio"], organismo["x"], organismo["y"], organismo["velocidade_mod"],
             organismo["tamanho_mod"], organismo["comportamento"], organismo["tipo"],
             datetime.now().isoformat(), organismo.get("local") or "placa", organismo.get("variante") or ""),
        )
    conexao.commit()
    return organismos


def listar_slots_geladeira():
    conexao = conectar()
    linhas = conexao.execute("SELECT slot, nome, data_salvo FROM geladeira").fetchall()
    ocupados = {linha["slot"]: dict(linha) for linha in linhas}
    slots = []
    for slot in range(1, 7):
        if slot in ocupados:
            slots.append({"slot": slot, "ocupado": True, **ocupados[slot]})
        else:
            slots.append({"slot": slot, "ocupado": False, "nome": None, "data_salvo": None})
    return slots


# ---------- estatísticas, manual e conquistas ----------

def incrementar_estatistica(chave, quantidade=1):
    conexao = conectar()
    conexao.execute(
        "INSERT INTO estatisticas (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = valor + ?",
        (chave, quantidade, quantidade),
    )
    conexao.commit()


def obter_estatistica(chave):
    conexao = conectar()
    linha = conexao.execute("SELECT valor FROM estatisticas WHERE chave = ?", (chave,)).fetchone()
    return linha["valor"] if linha else 0


def marcar_estagio_descoberto(estagio):
    conexao = conectar()
    ja_descoberto = conexao.execute(
        "SELECT descoberto FROM estagios_descobertos WHERE estagio = ?", (estagio,)
    ).fetchone()
    era_novo = not (ja_descoberto and ja_descoberto["descoberto"])
    conexao.execute(
        "UPDATE estagios_descobertos SET descoberto = 1 WHERE estagio = ?", (estagio,)
    )
    conexao.execute("INSERT OR IGNORE INTO descobertas_ciclo (ciclo, estagio) VALUES (?, ?)",
                    (ciclo_atual(), estagio))
    conexao.commit()
    return era_novo


TOTAL_CICLOS = 5   # um por troféu (Madeira, Bronze, Prata, Ouro, Diamante)


def ciclo_atual():
    """Ciclo 1 até ganhar a Madeira, ciclo 2 até o Bronze... depois do Diamante continua no 5."""
    return min(obter_estatistica("trofeus") + 1, TOTAL_CICLOS)


def listar_descobertas_por_ciclo():
    """{ciclo: {estágios descobertos naquele ciclo}} — é o que o Manual mostra lado a lado."""
    conexao = conectar()
    resultado = {ciclo: set() for ciclo in range(1, TOTAL_CICLOS + 1)}
    for linha in conexao.execute("SELECT ciclo, estagio FROM descobertas_ciclo").fetchall():
        resultado.setdefault(linha["ciclo"], set()).add(linha["estagio"])
    return resultado


def listar_estagios_descobertos():
    conexao = conectar()
    linhas = conexao.execute("SELECT estagio, descoberto FROM estagios_descobertos").fetchall()
    return {linha["estagio"]: bool(linha["descoberto"]) for linha in linhas}


def desbloquear_conquista(chave):
    conexao = conectar()
    linha = conexao.execute("SELECT desbloqueada FROM conquistas WHERE chave = ?", (chave,)).fetchone()
    if not linha or linha["desbloqueada"]:
        return None
    conexao.execute(
        "UPDATE conquistas SET desbloqueada = 1, data_desbloqueio = ? WHERE chave = ?",
        (datetime.now().isoformat(), chave),
    )
    conexao.commit()
    resultado = conexao.execute("SELECT * FROM conquistas WHERE chave = ?", (chave,)).fetchone()
    return dict(resultado)


def listar_conquistas():
    conexao = conectar()
    linhas = conexao.execute("SELECT * FROM conquistas ORDER BY categoria, nome").fetchall()
    return [dict(linha) for linha in linhas]


# ---------- Baú: Membrana, upgrades e frascos ----------
# O saldo de Membrana fica na tabela de estatísticas (chave "membrana").

def obter_membrana():
    return obter_estatistica("membrana")


def ganhar_membrana(quantidade):
    incrementar_estatistica("membrana", quantidade)
    incrementar_estatistica("membrana_total", quantidade)


def definir_membrana(valor):
    conexao = conectar()
    conexao.execute(
        "INSERT INTO estatisticas (chave, valor) VALUES ('membrana', ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor", (valor,),
    )
    conexao.commit()


def zerar_estatistica(chave):
    conexao = conectar()
    conexao.execute("UPDATE estatisticas SET valor = 0 WHERE chave = ?", (chave,))
    conexao.commit()


def recomecar_ciclo(membrana_inicial, membrana_que_fica=0):
    """Troféu conquistado: começa um ciclo novo.

    Zera: organismos (placa, fusão e mutação), Geladeira e os estágios descobertos do ciclo.
    A Membrana volta ao valor inicial + a parte que o jogador leva (membrana_que_fica).
    Fica: troféus, conquistas, upgrades, frascos, diário, estatísticas e o Manual dos ciclos anteriores.
    """
    conexao = conectar()
    conexao.execute("DELETE FROM organismos")
    conexao.execute("DELETE FROM geladeira")
    conexao.execute("UPDATE estagios_descobertos SET descoberto = 0")
    conexao.execute("UPDATE estatisticas SET valor = 0 WHERE chave = 'evolutivos_comprados_ciclo'")
    conexao.commit()
    definir_membrana(membrana_inicial + membrana_que_fica)


def gastar_membrana(quantidade):
    """Desconta do saldo. Devolve False (e não desconta nada) se não tiver Membrana suficiente."""
    if obter_membrana() < quantidade:
        return False
    incrementar_estatistica("membrana", -quantidade)
    return True


def obter_nivel_upgrade(chave):
    conexao = conectar()
    linha = conexao.execute("SELECT nivel FROM upgrades WHERE chave = ?", (chave,)).fetchone()
    return linha["nivel"] if linha else 0


def definir_nivel_upgrade(chave, nivel):
    conexao = conectar()
    conexao.execute(
        "INSERT INTO upgrades (chave, nivel) VALUES (?, ?) ON CONFLICT(chave) DO UPDATE SET nivel = excluded.nivel",
        (chave, nivel),
    )
    conexao.commit()


def obter_quantidade_item(chave):
    conexao = conectar()
    linha = conexao.execute("SELECT quantidade FROM inventario WHERE chave = ?", (chave,)).fetchone()
    return linha["quantidade"] if linha else 0


def ajustar_item(chave, diferenca):
    conexao = conectar()
    conexao.execute(
        "INSERT INTO inventario (chave, quantidade) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET quantidade = MAX(0, quantidade + ?)",
        (chave, max(0, diferenca), diferenca),
    )
    conexao.commit()


# ---------- diário ----------

def adicionar_entrada_diario(texto):
    conexao = conectar()
    conexao.execute(
        "INSERT INTO diario (texto, data) VALUES (?, ?)",
        (texto, datetime.now().isoformat()),
    )
    conexao.commit()


def listar_diario():
    conexao = conectar()
    linhas = conexao.execute("SELECT * FROM diario ORDER BY id DESC").fetchall()
    return [dict(linha) for linha in linhas]


def contar_diario():
    conexao = conectar()
    linha = conexao.execute("SELECT COUNT(*) AS total FROM diario").fetchone()
    return linha["total"]


def limpar_diario():
    conexao = conectar()
    conexao.execute("DELETE FROM diario")
    conexao.commit()


def pasta_do_projeto():
    return _pasta_do_projeto()
