import janelas
import random

import persistencia
import sons
import tema
import bau_dados
from evolucao_dados import receitas_fusao_do_estagio, nome_do_estagio, TOTAL_ESTAGIOS
from habilidades import habilidades_de_fusao
from conquistas import avaliar_e_desbloquear
from placa import PlacaBase

SALTO_DAS_MUTACOES = 2   # duas Mutações iguais que se encostam pulam este tanto de estágios


def _habilidades_de(organismo):
    return {
        "velocidade_mod": organismo.velocidade_mod,
        "tamanho_mod": organismo.tamanho_mod,
        "comportamento": organismo.comportamento,
    }


class TelaMutacao(PlacaBase):
    """🧬 Área de Mutação: aberta pelo troféu de Madeira.

    - Fusão manual: escolha 2 do mesmo estágio, um deles com o comportamento da receita -> nasce uma Mutação.
    - Duas Mutações iguais que se encostam aqui se fundem e pulam +2 estágios.
    """

    LOCAL = "mutacao"
    TITULO = "🧬 Área de Mutação"
    DICA = ("Clique em 2 do mesmo estágio e use “Tentar Fusão” (receita) para criar uma Mutação  •  "
            "Duas Mutações iguais que se encostam pulam +2 estágios  •  Botão direito: menu")
    TEXTO_VAZIO = ("Área de Mutação vazia nesta região.\nNa Simulação, clique com o botão direito num organismo "
                   "e escolha “Coletar para a Área de Mutação”.")
    NOME_FUNDO = "mutacao"
    COR_FUNDO = tema.MUTACAO["fundo"]
    COR_CANVAS = tema.MUTACAO["fundo"]
    COR_GRADE = tema.MUTACAO["grade"]
    COR_BORDA = tema.MUTACAO["borda"]
    COR_TEXTO = tema.MUTACAO["texto"]
    COR_TEXTO_SUAVE = tema.MUTACAO["texto_suave"]
    COR_PAINEL = tema.MUTACAO["painel"]
    COR_BOTAO = tema.MUTACAO["painel_claro"]
    COR_BOTAO_LIGADO = tema.MUTACAO["destaque"]
    COR_TEXTO_BOTAO = "white"
    COR_AVISO = tema.MUTACAO["aviso"]

    def __init__(self, master, controlador):
        self.selecionados = []
        self._itens_selecao = []
        super().__init__(master, controlador)

    def _montar_botoes(self, rodape):
        self._botao(rodape, "🧬 Tentar Fusão", self._tentar_fusao, self.COR_BOTAO_LIGADO,
                    padx=10).pack(side="left")
        self._botao(rodape, "↩️ Soltar todos na placa", self._soltar_todos, self.COR_BOTAO,
                    padx=10).pack(side="left", padx=6)

    # ---------- Mutação + Mutação: pulam +2 estágios ----------

    def _pode_colidir(self, organismo):
        return organismo.tipo == "fusao"   # aqui só as Mutações se fundem sozinhas

    def _resolver_interacao(self, organismo_a, organismo_b):
        if organismo_a.estagio >= TOTAL_ESTAGIOS:
            return
        novo_estagio = min(TOTAL_ESTAGIOS, organismo_a.estagio + SALTO_DAS_MUTACOES)
        x = (organismo_a.x + organismo_b.x) / 2
        y = (organismo_a.y + organismo_b.y) / 2
        habilidades = _habilidades_de(organismo_a)
        variante = organismo_a.variante
        self._remover_organismo(organismo_a)
        self._remover_organismo(organismo_b)
        novo = self._criar_e_mostrar(novo_estagio, x, y, habilidades, tipo="fusao", variante=variante)
        persistencia.incrementar_estatistica("merge_total")
        persistencia.incrementar_estatistica("mutacoes_fundidas_total")
        ganho = bau_dados.ganhar(bau_dados.recompensa_fusao())
        self._mostrar_ganho(x, y - novo.raio(), ganho)
        if not novo.ganho_descoberta:
            self._mostrar_evento(f"🧬 Mutação + Mutação: pulou para {nome_do_estagio(novo_estagio)}! (+{ganho} ⬡)")
        sons.tocar(sons.SOM_FUSAO)

    # ---------- seleção para a fusão manual ----------

    def _ao_clicar_organismo(self, organismo):
        if organismo.tipo == "fusao":
            self._mostrar_evento("Mutações não entram em receitas: junte duas iguais para pularem +2 estágios.")
            return
        if organismo in self.selecionados:
            self.selecionados.remove(organismo)
        else:
            self.selecionados.append(organismo)
            if len(self.selecionados) > 2:
                self.selecionados.pop(0)
        self._atualizar_extras()

    def _ao_remover(self, organismo):
        if organismo in self.selecionados:
            self.selecionados.remove(organismo)

    def _atualizar_extras(self):
        super()._atualizar_extras()
        for item in self._itens_selecao:
            self.canvas.delete(item)
        self._itens_selecao = []
        for organismo in self.selecionados:
            x, y = self.camera.para_tela(organismo.x, organismo.y)
            raio = organismo.raio() * self.camera.zoom + 6
            self._itens_selecao.append(self.canvas.create_oval(
                x - raio, y - raio, x + raio, y + raio, outline=self.COR_AVISO, width=2, dash=(4, 3),
            ))

    def _redesenhar_tudo_do_zero(self):
        self._itens_selecao = []
        super()._redesenhar_tudo_do_zero()

    def _carregar_organismos(self):
        self.selecionados = []
        super()._carregar_organismos()

    def _tentar_fusao(self):
        if len(self.selecionados) != 2:
            janelas.showwarning("Fusão", "Clique em exatamente dois organismos para selecioná-los.")
            return

        organismo_a, organismo_b = self.selecionados

        if organismo_a.estagio != organismo_b.estagio:
            janelas.showerror("Fusão", "Os dois organismos precisam estar no mesmo estágio.")
            return

        receitas = receitas_fusao_do_estagio(organismo_a.estagio)
        comportamentos_par = {organismo_a.comportamento, organismo_b.comportamento}
        receita_escolhida = None
        for receita in receitas:
            if receita["comportamento_exigido"] in comportamentos_par:
                receita_escolhida = receita
                break

        if receita_escolhida is None:
            exigidos = ", ".join(r["comportamento_exigido"] for r in receitas)
            janelas.showerror(
                "Fusão", f"Nenhuma receita compatível.\nPara este estágio, um dos dois precisa ser: {exigidos}"
            )
            return

        novas_habilidades = habilidades_de_fusao(_habilidades_de(organismo_a), _habilidades_de(organismo_b))
        x = (organismo_a.x + organismo_b.x) / 2
        y = (organismo_a.y + organismo_b.y) / 2
        self._remover_organismo(organismo_a)
        self._remover_organismo(organismo_b)
        self._criar_e_mostrar(organismo_a.estagio, x, y, novas_habilidades, tipo="fusao",
                              variante=receita_escolhida["comportamento_exigido"])

        persistencia.incrementar_estatistica("fusao_manual_total")
        persistencia.adicionar_entrada_diario(
            f"Fusão manual bem-sucedida: {receita_escolhida['nome']} (nasceu uma Mutação)."
        )

        sons.tocar(sons.SOM_FUSAO)
        novas_conquistas = avaliar_e_desbloquear({"fusoes_realizadas": [receita_escolhida["chave"]]})
        mensagem = f"🧬 Fusão concluída: {receita_escolhida['nome']}"
        if novas_conquistas:
            mensagem += "  •  Conquistas: " + ", ".join(c["nome"] for c in novas_conquistas)
            sons.tocar(sons.SOM_CONQUISTA)
        self._mostrar_evento(mensagem)

    # ---------- menu e devolução para a placa ----------

    def _opcoes_menu(self, organismo):
        opcoes = [("🔍  Inspecionar", self._inspecionar)]
        if organismo.tipo != "fusao":
            texto = "✖️  Tirar da seleção" if organismo in self.selecionados else "🎯  Selecionar para fusão"
            opcoes.append((texto, self._ao_clicar_organismo))
        opcoes += [
            ("↩️  Soltar na placa", self._soltar),
            ("💥  Destruir", self._destruir),
        ]
        return opcoes

    def _soltar(self, organismo):
        self._transferir(organismo, "placa", "soltar_total")
        self._mostrar_evento(f"{organismo.dados_estagio()['nome']} devolvido à placa ↩️")

    def _soltar_todos(self):
        if not self.organismos:
            return
        quantidade = len(self.organismos)
        for organismo in list(self.organismos):
            self._transferir(organismo, "placa", "soltar_total")
        self._mostrar_evento(f"{quantidade} organismos devolvidos à placa ↩️")
