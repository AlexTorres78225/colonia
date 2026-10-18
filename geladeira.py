import tkinter as tk
import janelas

import persistencia
import recursos
import sons
import tema
from conquistas import avaliar_e_desbloquear

COR_FUNDO = tema.LAB["fundo"]
COR_PRATELEIRA = tema.LAB["painel"]
COR_SLOT_VAZIO = tema.LAB["painel"]
COR_SLOT_OCUPADO = tema.LAB["destaque"]
COR_TEXTO = tema.LAB["texto"]
COR_TEXTO_SUAVE = tema.LAB["texto_suave"]


class TelaGeladeira(tk.Frame):
    def __init__(self, master, controlador):
        super().__init__(master, bg=COR_FUNDO)
        self.controlador = controlador

        tk.Label(self, text="🧊 Geladeira de Amostras", fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 14, "bold")).pack(pady=(14, 4))
        tk.Label(self, text="Congele o cenário atual da colônia em um dos 6 compartimentos, "
                             "ou descongele um cenário salvo anteriormente.",
                 fg=COR_TEXTO_SUAVE, bg=COR_FUNDO, font=("Segoe UI", 9)).pack(pady=(0, 10))

        self.canvas = tk.Canvas(self, width=760, height=420, bg=COR_FUNDO, highlightthickness=0)
        self.canvas.pack(pady=6)
        self.canvas.bind("<Button-1>", self._ao_clicar)

        self._areas_slots = {}
        self._desenhar_geladeira()

    def _desenhar_geladeira(self):
        self.canvas.delete("all")
        self._areas_slots = {}

        imagem_fundo = recursos.aplicar_fundo_canvas(self.canvas, "geladeira", 760, 420)
        self._imagem_fundo_referencia = imagem_fundo

        if imagem_fundo is None:
            self.canvas.create_rectangle(30, 20, 730, 400, fill=COR_PRATELEIRA, outline="#3f6a86", width=4)
            self.canvas.create_rectangle(30, 20, 730, 70, fill="#0f2c3f", outline="")
            self.canvas.create_text(380, 45, text="PAINEL DE CONSERVAÇÃO — 6 AMOSTRAS", fill="#8fd6ff",
                                     font=("Segoe UI", 11, "bold"))

        slots = persistencia.listar_slots_geladeira()
        colunas = 3
        largura_slot, altura_slot = 210, 140
        margem_x, margem_y = 45, 90

        for indice, slot in enumerate(slots):
            coluna = indice % colunas
            linha = indice // colunas
            x0 = margem_x + coluna * (largura_slot + 20)
            y0 = margem_y + linha * (altura_slot + 20)
            x1 = x0 + largura_slot
            y1 = y0 + altura_slot

            cor = COR_SLOT_OCUPADO if slot["ocupado"] else COR_SLOT_VAZIO
            borda = tema.LAB["aviso"] if slot["ocupado"] else tema.LAB["borda"]
            # stipple="gray50" pinta só metade dos pixels: o compartimento fica "transparente"
            # e a geladeira desenhada aparece por trás
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=cor, stipple="gray50", outline=borda, width=2)
            titulo = f"Slot {slot['slot']}"
            self.canvas.create_text((x0 + x1) / 2, y0 + 20, text=titulo, fill=COR_TEXTO,
                                     font=("Segoe UI", 10, "bold"))
            if slot["ocupado"]:
                self.canvas.create_text((x0 + x1) / 2, y0 + 55, text=slot["nome"] or "Sem nome",
                                         fill=COR_TEXTO, font=("Segoe UI", 9, "bold"))
                data_curta = (slot["data_salvo"] or "")[:16].replace("T", " ")
                self.canvas.create_text((x0 + x1) / 2, y0 + 78, text=data_curta,
                                         fill=COR_TEXTO_SUAVE, font=("Segoe UI", 8))
                self.canvas.create_text((x0 + x1) / 2, y0 + 105, text="Clique: opções",
                                         fill=COR_TEXTO, font=("Segoe UI", 8, "italic"))
            else:
                self.canvas.create_text((x0 + x1) / 2, y0 + 65, text="Vazio",
                                         fill=COR_TEXTO, font=("Segoe UI", 9))
                self.canvas.create_text((x0 + x1) / 2, y0 + 90, text="Clique para salvar",
                                         fill=COR_TEXTO_SUAVE, font=("Segoe UI", 8, "italic"))

            self._areas_slots[(x0, y0, x1, y1)] = slot

    def _ao_clicar(self, evento):
        # descobre o compartimento pela posição do clique (funciona mesmo com o desenho "transparente")
        slot = None
        for (x0, y0, x1, y1), slot_da_area in self._areas_slots.items():
            if x0 <= evento.x <= x1 and y0 <= evento.y <= y1:
                slot = slot_da_area
                break
        if slot is None:
            return
        if slot["ocupado"]:
            self._abrir_opcoes_slot(slot)
        else:
            self._salvar_no_slot(slot["slot"])

    def _salvar_no_slot(self, numero_slot):
        organismos_atuais = persistencia.listar_organismos()
        if not organismos_atuais:
            janelas.showwarning("Geladeira", "A colônia atual está vazia. Nada para salvar.")
            return
        nome = janelas.askstring("Salvar Amostra", "Nome para este cenário:", parent=self)
        if not nome:
            nome = f"Amostra {numero_slot}"
        persistencia.salvar_slot_geladeira(numero_slot, nome)
        sons.tocar(sons.SOM_GELADEIRA)
        novas = avaliar_e_desbloquear({
            "slots_salvos": [numero_slot],
            "salvou_com_organismos": len(organismos_atuais),
            "salvou_com_maior_estagio": max(o["estagio"] for o in organismos_atuais),
        })
        self._desenhar_geladeira()
        mensagem = f"Cenário salvo no slot {numero_slot}."
        if novas:
            mensagem += "\nConquistas: " + ", ".join(c["nome"] for c in novas)
            sons.tocar(sons.SOM_CONQUISTA)
        janelas.showinfo("Geladeira", mensagem)

    def _abrir_opcoes_slot(self, slot):
        janela = tk.Toplevel(self)
        janela.title(f"Slot {slot['slot']} — {slot['nome']}")
        janela.configure(bg=COR_FUNDO)
        janela.geometry("300x180")

        tk.Label(janela, text=slot["nome"], fg=COR_TEXTO, bg=COR_FUNDO,
                 font=("Segoe UI", 12, "bold")).pack(pady=10)

        tk.Button(janela, text="Descongelar (carregar na placa)",
                  command=lambda: self._carregar_slot(slot["slot"], janela),
                  bg=tema.LAB["destaque"], fg="white", relief="flat").pack(fill="x", padx=20, pady=6)
        tk.Button(janela, text="Sobrescrever com cenário atual",
                  command=lambda: self._sobrescrever_slot(slot["slot"], janela),
                  bg="#9a6a2a", fg="white", relief="flat").pack(fill="x", padx=20, pady=6)
        tk.Button(janela, text="Fechar", command=janela.destroy,
                  bg=tema.LAB["painel_claro"], fg="white", relief="flat").pack(fill="x", padx=20, pady=6)

    def _carregar_slot(self, numero_slot, janela):
        if not janelas.askyesno("Confirmar", "Isso substituirá a colônia atual pela do slot. Continuar?"):
            return
        placa_vazia = not persistencia.listar_organismos("placa")
        persistencia.carregar_slot_geladeira(numero_slot)
        persistencia.incrementar_estatistica("geladeira_carregar_total")
        sons.tocar(sons.SOM_GELADEIRA)
        novas = avaliar_e_desbloquear({"slots_carregados": [numero_slot], "carregou_com_placa_vazia": placa_vazia})
        janela.destroy()
        mensagem = f"Cenário do slot {numero_slot} carregado na placa principal."
        if novas:
            mensagem += "\nConquistas: " + ", ".join(c["nome"] for c in novas)
            sons.tocar(sons.SOM_CONQUISTA)
        janelas.showinfo("Geladeira", mensagem)
        self._desenhar_geladeira()

    def _sobrescrever_slot(self, numero_slot, janela):
        janela.destroy()
        self._salvar_no_slot(numero_slot)

    def atualizar_ao_exibir(self):
        self._desenhar_geladeira()