import time
import tkinter as tk
import janelas

import autenticacao
import recursos
import tema

# clima "laboratório holográfico" (tema.LAB)
COR_FUNDO = tema.LAB["fundo"]
COR_ROTULO = tema.LAB["texto_suave"]
COR_BOTAO_PRIMARIO = tema.LAB["destaque"]
COR_BOTAO_SECUNDARIO = tema.LAB["painel_claro"]

PERGUNTAS_SEGURANCA = [
    "Nome do seu primeiro animal de estimação?",
    "Cidade onde você nasceu?",
    "Comida favorita da infância?",
    "Nome do seu professor favorito?",
]
TENTATIVAS_ANTES_DE_ESPERAR = 5
SEGUNDOS_DE_ESPERA = 30
AVISO_PRIVACIDADE = ("🔒 Esta conta é só deste jogo e fica só neste computador (o Colônia não usa internet). "
                     "Não use a mesma senha de outros sites.")


class TelaLogin(tk.Tk):
    def __init__(self, ao_autenticar):
        super().__init__()
        self.ao_autenticar = ao_autenticar
        self.title("Colônia — Acesso do Cientista")
        self.geometry("440x520")
        self.configure(bg=COR_FUNDO)
        self.resizable(False, False)
        self._nome_em_recuperacao = None
        self._erros = 0                 # erros seguidos de senha/resposta
        self._bloqueado_ate = 0         # depois de muitos erros, espera um pouco

        # option_add muda o padrão de TODOS os campos de texto desta janela de uma vez
        self.option_add("*Entry.background", tema.LAB["painel"])
        self.option_add("*Entry.foreground", tema.LAB["texto"])
        self.option_add("*Entry.insertBackground", tema.LAB["destaque_claro"])
        self.option_add("*Entry.relief", "flat")
        self.option_add("*Entry.highlightThickness", 1)
        self.option_add("*Entry.highlightBackground", tema.LAB["borda"])
        self.option_add("*Entry.highlightColor", tema.LAB["destaque_claro"])

        recursos.aplicar_fundo_frame(self, "login")
        self._montar_tela_login()

    # ---------- proteção contra adivinhação ----------

    def _esta_bloqueado(self):
        restante = int(self._bloqueado_ate - time.time())
        if restante > 0:
            janelas.showwarning("Muitas tentativas", f"Muitas tentativas erradas. Aguarde {restante} segundos.")
            return True
        return False

    def _registrar_erro(self):
        self._erros += 1
        if self._erros >= TENTATIVAS_ANTES_DE_ESPERAR:
            self._erros = 0
            self._bloqueado_ate = time.time() + SEGUNDOS_DE_ESPERA

    # ---------- montagem ----------

    def _limpar(self):
        for widget in self.winfo_children():
            widget.destroy()
        recursos.aplicar_fundo_frame(self, "login")

    def _rotulo_campo(self, texto):
        # centralizado, igual aos campos, para o rótulo ficar logo em cima do seu campo
        tk.Label(self, text=texto, fg=COR_ROTULO, bg=COR_FUNDO, font=("Segoe UI", 9)).pack()

    def _aviso(self):
        tk.Label(self, text=AVISO_PRIVACIDADE, fg=tema.LAB["aviso"], bg=COR_FUNDO, wraplength=360,
                 font=("Segoe UI", 8), justify="center").pack(pady=(0, 10))

    def _montar_tela_login(self):
        self._limpar()

        tk.Label(self, text="🧪 Acesso do Cientista", fg="#e8f6ef", bg=COR_FUNDO,
                 font=("Segoe UI", 16, "bold")).pack(pady=(28, 20))

        self._rotulo_campo("Usuário")
        self.entrada_usuario = tk.Entry(self, width=32)
        self.entrada_usuario.pack(padx=40, pady=(0, 12))

        self._rotulo_campo("Senha")
        self.entrada_senha = tk.Entry(self, width=32, show="*")
        self.entrada_senha.pack(padx=40, pady=(0, 18))
        self.entrada_senha.bind("<Return>", lambda evento: self._tentar_login())

        tk.Button(self, text="Entrar", command=self._tentar_login, bg=COR_BOTAO_PRIMARIO, fg="white",
                  relief="flat", padx=10, pady=8, width=28).pack(pady=4)
        tk.Button(self, text="Criar nova conta", command=self._montar_tela_registro, bg=COR_BOTAO_SECUNDARIO,
                  fg="#d8e8e0", relief="flat", width=28).pack(pady=4)
        tk.Button(self, text="Esqueci minha senha", command=self._montar_tela_recuperacao_nome,
                  bg=COR_BOTAO_SECUNDARIO, fg="#d8e8e0", relief="flat", width=28).pack(pady=4)
        tk.Button(self, text="Excluir uma conta", command=self._montar_tela_excluir,
                  bg=tema.LAB["perigo"], fg="white", relief="flat", width=28).pack(pady=(14, 4))

        self.entrada_usuario.focus_set()

    def _tentar_login(self):
        if self._esta_bloqueado():
            return
        nome = self.entrada_usuario.get().strip()
        senha = self.entrada_senha.get()
        if not nome or not senha:
            janelas.showwarning("Login", "Preencha usuário e senha.")
            return
        if autenticacao.verificar_login(nome, senha):
            self.destroy()
            self.ao_autenticar(nome)
        else:
            self._registrar_erro()
            janelas.showerror("Login", "Usuário ou senha incorretos.")

    def _montar_tela_registro(self):
        self._limpar()

        tk.Label(self, text="📝 Criar Nova Conta", fg="#e8f6ef", bg=COR_FUNDO,
                 font=("Segoe UI", 15, "bold")).pack(pady=(16, 6))
        self._aviso()

        self._rotulo_campo("Usuário")
        self.entrada_registro_usuario = tk.Entry(self, width=32)
        self.entrada_registro_usuario.pack(padx=40, pady=(0, 8))

        self._rotulo_campo(f"Senha (mínimo {autenticacao.TAMANHO_MINIMO_SENHA} caracteres)")
        self.entrada_registro_senha = tk.Entry(self, width=32, show="*")
        self.entrada_registro_senha.pack(padx=40, pady=(0, 8))

        self._rotulo_campo("Confirmar Senha")
        self.entrada_registro_confirmar = tk.Entry(self, width=32, show="*")
        self.entrada_registro_confirmar.pack(padx=40, pady=(0, 8))

        self._rotulo_campo("Pergunta de segurança")
        self.variavel_pergunta = tk.StringVar(value=PERGUNTAS_SEGURANCA[0])
        menu_pergunta = tk.OptionMenu(self, self.variavel_pergunta, *PERGUNTAS_SEGURANCA)
        menu_pergunta.config(bg=tema.LAB["painel"], fg=tema.LAB["texto"], activebackground=tema.LAB["painel_claro"],
                             activeforeground="white", relief="flat", highlightthickness=1,
                             highlightbackground=tema.LAB["borda"])
        menu_pergunta["menu"].config(bg=tema.LAB["painel"], fg=tema.LAB["texto"])
        menu_pergunta.pack(padx=40, pady=(0, 8), fill="x")

        self._rotulo_campo("Resposta")
        self.entrada_registro_resposta = tk.Entry(self, width=32)
        self.entrada_registro_resposta.pack(padx=40, pady=(0, 16))

        tk.Button(self, text="Registrar", command=self._tentar_registrar, bg=COR_BOTAO_PRIMARIO, fg="white",
                  relief="flat", padx=10, pady=8, width=28).pack(pady=4)
        tk.Button(self, text="Voltar", command=self._montar_tela_login, bg=COR_BOTAO_SECUNDARIO,
                  fg="#d8e8e0", relief="flat", width=28).pack(pady=4)

    def _tentar_registrar(self):
        nome = self.entrada_registro_usuario.get().strip()
        senha = self.entrada_registro_senha.get()
        confirmar = self.entrada_registro_confirmar.get()
        resposta = self.entrada_registro_resposta.get().strip()
        pergunta = self.variavel_pergunta.get()

        if not nome or not senha or not resposta:
            janelas.showwarning("Registro", "Preencha todos os campos.")
            return
        if len(nome) > 24:
            janelas.showwarning("Registro", "O nome de usuário pode ter no máximo 24 caracteres.")
            return
        if len(senha) < autenticacao.TAMANHO_MINIMO_SENHA:
            janelas.showwarning("Registro", f"A senha precisa ter pelo menos {autenticacao.TAMANHO_MINIMO_SENHA} "
                                            "caracteres.")
            return
        if senha != confirmar:
            janelas.showerror("Registro", "As senhas não coincidem.")
            return

        sucesso = autenticacao.criar_usuario(nome, senha, pergunta, resposta)
        if sucesso:
            janelas.showinfo("Registro", "Conta criada com sucesso! Faça login.")
            self._montar_tela_login()
        else:
            janelas.showerror("Registro", "Esse nome de usuário já existe.")

    def _montar_tela_recuperacao_nome(self):
        self._limpar()

        tk.Label(self, text="🔑 Recuperar Senha", fg="#e8f6ef", bg=COR_FUNDO,
                 font=("Segoe UI", 15, "bold")).pack(pady=(28, 16))

        self._rotulo_campo("Usuário")
        self.entrada_recuperacao_usuario = tk.Entry(self, width=32)
        self.entrada_recuperacao_usuario.pack(padx=40, pady=(0, 16))

        tk.Button(self, text="Continuar", command=self._buscar_pergunta_seguranca, bg=COR_BOTAO_PRIMARIO,
                  fg="white", relief="flat", padx=10, pady=8, width=28).pack(pady=4)
        tk.Button(self, text="Voltar", command=self._montar_tela_login, bg=COR_BOTAO_SECUNDARIO,
                  fg="#d8e8e0", relief="flat", width=28).pack(pady=4)

    def _buscar_pergunta_seguranca(self):
        nome = self.entrada_recuperacao_usuario.get().strip()
        pergunta = autenticacao.obter_pergunta_seguranca(nome)
        if not pergunta:
            janelas.showerror("Recuperação", "Usuário não encontrado.")
            return
        self._nome_em_recuperacao = nome
        self._montar_tela_resposta_seguranca(pergunta)

    def _montar_tela_resposta_seguranca(self, pergunta):
        self._limpar()

        tk.Label(self, text="🔑 Pergunta de Segurança", fg="#e8f6ef", bg=COR_FUNDO,
                 font=("Segoe UI", 14, "bold")).pack(pady=(28, 6))
        tk.Label(self, text=pergunta, fg="#c9e0d8", bg=COR_FUNDO, wraplength=360,
                 font=("Segoe UI", 10, "italic"), justify="center").pack(pady=(0, 16))

        self._rotulo_campo("Resposta")
        self.entrada_resposta_seguranca = tk.Entry(self, width=32)
        self.entrada_resposta_seguranca.pack(padx=40, pady=(0, 12))

        self._rotulo_campo(f"Nova senha (mínimo {autenticacao.TAMANHO_MINIMO_SENHA} caracteres)")
        self.entrada_nova_senha = tk.Entry(self, width=32, show="*")
        self.entrada_nova_senha.pack(padx=40, pady=(0, 16))

        tk.Button(self, text="Redefinir Senha", command=self._redefinir_senha, bg=COR_BOTAO_PRIMARIO,
                  fg="white", relief="flat", padx=10, pady=8, width=28).pack(pady=4)
        tk.Button(self, text="Voltar", command=self._montar_tela_login, bg=COR_BOTAO_SECUNDARIO,
                  fg="#d8e8e0", relief="flat", width=28).pack(pady=4)

    def _redefinir_senha(self):
        if self._esta_bloqueado():
            return
        resposta = self.entrada_resposta_seguranca.get().strip()
        nova_senha = self.entrada_nova_senha.get()
        if not nova_senha:
            janelas.showwarning("Recuperação", "Digite uma nova senha.")
            return
        if len(nova_senha) < autenticacao.TAMANHO_MINIMO_SENHA:
            janelas.showwarning("Recuperação", f"A senha precisa ter pelo menos {autenticacao.TAMANHO_MINIMO_SENHA} "
                                               "caracteres.")
            return

        sucesso = autenticacao.redefinir_senha_com_resposta(self._nome_em_recuperacao, resposta, nova_senha)
        if sucesso:
            self._erros = 0
            janelas.showinfo("Recuperação", "Senha redefinida com sucesso! Faça login com a nova senha.")
            self._montar_tela_login()
        else:
            self._registrar_erro()
            janelas.showerror("Recuperação", "Resposta de segurança incorreta.")

    # ---------- excluir conta (o jogador controla os próprios dados) ----------

    def _montar_tela_excluir(self):
        self._limpar()

        tk.Label(self, text="🗑 Excluir Conta", fg="#e8f6ef", bg=COR_FUNDO,
                 font=("Segoe UI", 15, "bold")).pack(pady=(28, 6))
        tk.Label(self, text="Apaga a conta e todo o progresso dela (colônia, Baú, troféus, conquistas). "
                            "Não dá para desfazer.", fg=tema.LAB["aviso"], bg=COR_FUNDO, wraplength=360,
                 font=("Segoe UI", 9), justify="center").pack(pady=(0, 14))

        self._rotulo_campo("Usuário")
        self.entrada_excluir_usuario = tk.Entry(self, width=32)
        self.entrada_excluir_usuario.pack(padx=40, pady=(0, 12))

        self._rotulo_campo("Senha")
        self.entrada_excluir_senha = tk.Entry(self, width=32, show="*")
        self.entrada_excluir_senha.pack(padx=40, pady=(0, 18))

        tk.Button(self, text="Excluir para sempre", command=self._excluir_conta, bg=tema.LAB["perigo"],
                  fg="white", relief="flat", padx=10, pady=8, width=28).pack(pady=4)
        tk.Button(self, text="Voltar", command=self._montar_tela_login, bg=COR_BOTAO_SECUNDARIO,
                  fg="#d8e8e0", relief="flat", width=28).pack(pady=4)

    def _excluir_conta(self):
        if self._esta_bloqueado():
            return
        nome = self.entrada_excluir_usuario.get().strip()
        senha = self.entrada_excluir_senha.get()
        if not nome or not senha:
            janelas.showwarning("Excluir conta", "Preencha usuário e senha.")
            return
        if not janelas.askyesno("Excluir conta", f"Excluir a conta '{nome}' e TODO o progresso dela?\n"
                                                 "Isso não pode ser desfeito."):
            return
        if autenticacao.excluir_conta(nome, senha):
            janelas.showinfo("Excluir conta", f"A conta '{nome}' foi excluída.")
            self._montar_tela_login()
        else:
            self._registrar_erro()
            janelas.showerror("Excluir conta", "Usuário ou senha incorretos.")


def iniciar_fluxo_login(ao_autenticar):
    tela = TelaLogin(ao_autenticar)
    tela.mainloop()
