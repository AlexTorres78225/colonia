"""Caixinhas de aviso no tema do jogo (no lugar das caixas brancas padrão do Windows).

Os nomes são os mesmos do tkinter.messagebox (showinfo, showwarning, showerror, askyesno)
e do simpledialog (askstring), então trocar um pelo outro é só mudar o 'messagebox.' para 'janelas.'.
"""
import tkinter as tk

import tema

ICONES = {"info": "ℹ️", "aviso": "⚠️", "erro": "❌", "pergunta": "❔", "texto": "✏️"}


def _janela_base(titulo, texto, tipo, parent=None):
    pai = parent or tk._default_root
    janela = tk.Toplevel(pai)
    janela.title(titulo)
    janela.configure(bg=tema.LAB["painel"], padx=22, pady=16)
    janela.resizable(False, False)
    janela.transient(pai.winfo_toplevel())
    tk.Label(janela, text=f"{ICONES[tipo]}  {titulo}", fg=tema.LAB["texto"], bg=tema.LAB["painel"],
             font=("Segoe UI", 12, "bold")).pack(anchor="w")
    tk.Label(janela, text=texto, fg=tema.LAB["texto"], bg=tema.LAB["painel"], font=("Segoe UI", 10),
             justify="left", wraplength=420).pack(anchor="w", pady=(8, 14))
    botoes = tk.Frame(janela, bg=tema.LAB["painel"])
    botoes.pack(fill="x")
    return janela, botoes


def _botao(pai, texto, comando, principal=True):
    cor = tema.LAB["destaque"] if principal else tema.LAB["painel_claro"]
    botao = tk.Button(pai, text=texto, command=comando, bg=cor, fg="white", relief="flat",
                      activebackground=tema.LAB["borda"], padx=16, pady=4)
    botao.pack(side="right", padx=(6, 0))
    return botao


def _mostrar_e_esperar(janela, foco):
    janela.update_idletasks()
    pai = janela.master.winfo_toplevel()
    x = pai.winfo_rootx() + (pai.winfo_width() - janela.winfo_width()) // 2
    y = pai.winfo_rooty() + (pai.winfo_height() - janela.winfo_height()) // 3
    janela.geometry(f"+{max(0, x)}+{max(0, y)}")
    janela.grab_set()
    foco.focus_set()
    janela.wait_window()


def _mensagem(titulo, texto, tipo, parent=None):
    janela, botoes = _janela_base(titulo, texto, tipo, parent)
    ok = _botao(botoes, "OK", janela.destroy)
    janela.bind("<Return>", lambda evento: janela.destroy())
    janela.bind("<Escape>", lambda evento: janela.destroy())
    _mostrar_e_esperar(janela, ok)


def showinfo(titulo, texto, parent=None, **_):
    _mensagem(titulo, texto, "info", parent)


def showwarning(titulo, texto, parent=None, **_):
    _mensagem(titulo, texto, "aviso", parent)


def showerror(titulo, texto, parent=None, **_):
    _mensagem(titulo, texto, "erro", parent)


def askyesno(titulo, texto, parent=None, **_):
    resposta = {"valor": False}
    janela, botoes = _janela_base(titulo, texto, "pergunta", parent)

    def responder(valor):
        resposta["valor"] = valor
        janela.destroy()

    sim = _botao(botoes, "Sim", lambda: responder(True))
    _botao(botoes, "Não", lambda: responder(False), principal=False)
    janela.bind("<Escape>", lambda evento: responder(False))
    _mostrar_e_esperar(janela, sim)
    return resposta["valor"]


def askstring(titulo, texto, parent=None, **_):
    resposta = {"valor": None}
    janela, botoes = _janela_base(titulo, texto, "texto", parent)
    entrada = tk.Entry(janela, width=36, bg=tema.LAB["fundo"], fg=tema.LAB["texto"], relief="flat",
                       insertbackground=tema.LAB["destaque_claro"], highlightthickness=1,
                       highlightbackground=tema.LAB["borda"])
    entrada.pack(before=botoes, fill="x", pady=(0, 12))

    def confirmar():
        resposta["valor"] = entrada.get()
        janela.destroy()

    _botao(botoes, "OK", confirmar)
    _botao(botoes, "Cancelar", janela.destroy, principal=False)
    entrada.bind("<Return>", lambda evento: confirmar())
    janela.bind("<Escape>", lambda evento: janela.destroy())
    _mostrar_e_esperar(janela, entrada)
    return resposta["valor"]
