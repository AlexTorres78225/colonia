"""Contas do jogo: senha e resposta de segurança guardadas com segurança.

Nada aqui usa internet: as contas existem só no computador do jogador.

Como a senha é guardada: nunca a senha em si, só um "hash" PBKDF2 (repete o cálculo 200 mil vezes).
Isso deixa MUITO lento para alguém que copiou o arquivo tentar adivinhar senhas.
Contas antigas (hash SHA-256 simples) são atualizadas sozinhas no próximo login certo.
"""
import hashlib
import hmac
import os

import persistencia

ITERACOES = 200_000
PREFIXO = "pbkdf2"           # hashes novos ficam assim: "pbkdf2$200000$<hex>"
TAMANHO_MINIMO_SENHA = 6


def _gerar_sal():
    return os.urandom(16).hex()


def _hash_forte(texto, sal):
    resumo = hashlib.pbkdf2_hmac("sha256", texto.encode("utf-8"), bytes.fromhex(sal), ITERACOES)
    return f"{PREFIXO}${ITERACOES}${resumo.hex()}"


def _hash_antigo(texto, sal):
    """O formato antigo (até a v1.0). Só serve para conferir e atualizar contas que já existiam."""
    return hashlib.sha256((sal + texto).encode("utf-8")).hexdigest()


def _confere(texto, sal, guardado):
    """Confere o texto com o hash guardado. Devolve (está_certo, é_formato_antigo)."""
    if guardado.startswith(PREFIXO + "$"):
        _prefixo, iteracoes, resumo = guardado.split("$")
        calculado = hashlib.pbkdf2_hmac("sha256", texto.encode("utf-8"), bytes.fromhex(sal), int(iteracoes)).hex()
        return hmac.compare_digest(calculado, resumo), False
    return hmac.compare_digest(_hash_antigo(texto, sal), guardado), True


def _normalizar_resposta(resposta):
    return resposta.strip().lower()


def usuario_existe(nome_usuario):
    return persistencia.obter_usuario(nome_usuario) is not None


def criar_usuario(nome_usuario, senha, pergunta_seguranca, resposta_seguranca):
    if usuario_existe(nome_usuario):
        return False
    sal_senha = _gerar_sal()
    sal_resposta = _gerar_sal()
    persistencia.criar_usuario_db(
        nome_usuario,
        _hash_forte(senha, sal_senha), sal_senha,
        pergunta_seguranca,
        _hash_forte(_normalizar_resposta(resposta_seguranca), sal_resposta), sal_resposta,
    )
    return True


def verificar_login(nome_usuario, senha):
    usuario = persistencia.obter_usuario(nome_usuario)
    if not usuario:
        return False
    certo, antigo = _confere(senha, usuario["sal"], usuario["senha_hash"])
    if certo and antigo:
        # conta da versão antiga: aproveita o login certo para trocar pelo formato seguro
        novo_sal = _gerar_sal()
        persistencia.atualizar_senha(nome_usuario, _hash_forte(senha, novo_sal), novo_sal)
    return certo


def obter_pergunta_seguranca(nome_usuario):
    usuario = persistencia.obter_usuario(nome_usuario)
    return usuario["pergunta_seguranca"] if usuario else None


def resposta_confere(nome_usuario, resposta):
    usuario = persistencia.obter_usuario(nome_usuario)
    if not usuario:
        return False
    certo, antigo = _confere(_normalizar_resposta(resposta), usuario["resposta_sal"], usuario["resposta_hash"])
    if certo and antigo:
        novo_sal = _gerar_sal()
        persistencia.atualizar_resposta(nome_usuario, _hash_forte(_normalizar_resposta(resposta), novo_sal), novo_sal)
    return certo


def redefinir_senha_com_resposta(nome_usuario, resposta, nova_senha):
    if not resposta_confere(nome_usuario, resposta):
        return False
    novo_sal = _gerar_sal()
    persistencia.atualizar_senha(nome_usuario, _hash_forte(nova_senha, novo_sal), novo_sal)
    return True


def excluir_conta(nome_usuario, senha):
    """Apaga a conta e o save dela. Pede a senha para ninguém apagar a conta de outra pessoa."""
    if not verificar_login(nome_usuario, senha):
        return False
    persistencia.excluir_usuario(nome_usuario)
    return True
