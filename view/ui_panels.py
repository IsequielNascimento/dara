"""
ui_panels.py — Painéis laterais da interface do Jogo Dara
Responsável por: painel de status do jogo e painel de chat.

Cada painel é um Frame Tkinter independente, instanciado pela janela principal.
"""

import tkinter as tk
from tkinter import scrolledtext
from constants import (
    CLR_BG, CLR_PANEL, CLR_ACCENT, CLR_TEXT,
    CLR_GOLD, CLR_TURN_MY, CLR_TURN_OPP,
    TOTAL_PIECES,
)


class StatusPanel(tk.Frame):
    """
    Exibe: turno atual, fase do jogo, contagem de peças, mensagem de status.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=CLR_PANEL, relief="solid", bd=1, **kwargs)

        # Barra de acento no topo
        tk.Frame(self, bg=CLR_ACCENT, height=2).pack(fill="x")

        inner = tk.Frame(self, bg=CLR_PANEL, padx=12, pady=8)
        inner.pack(fill="x")

        self.lbl_turn = tk.Label(
            inner, text="Aguardando...",
            bg=CLR_PANEL, fg=CLR_GOLD,
            font=("Arial", 13, "bold"), anchor="w"
        )
        self.lbl_turn.pack(fill="x")

        self.lbl_phase = tk.Label(
            inner, text="Fase: Colocação",
            bg=CLR_PANEL, fg=CLR_TEXT,
            font=("Arial", 11), anchor="w"
        )
        self.lbl_phase.pack(fill="x", pady=(2, 0))

        self.lbl_my_pieces = tk.Label(
            inner, text=f"Suas peças: {TOTAL_PIECES} p/ colocar",
            bg=CLR_PANEL, fg="#88FFCC",
            font=("Arial", 10), anchor="w"
        )
        self.lbl_my_pieces.pack(fill="x", pady=(4, 0))

        self.lbl_opp_pieces = tk.Label(
            inner, text=f"Oponente: {TOTAL_PIECES} p/ colocar",
            bg=CLR_PANEL, fg="#FF8888",
            font=("Arial", 10), anchor="w"
        )
        self.lbl_opp_pieces.pack(fill="x")

        self.lbl_status = tk.Label(
            inner, text="Conectando...",
            bg=CLR_PANEL, fg="#AAAAAA",
            font=("Arial", 10, "italic"), anchor="w",
            wraplength=230, justify="left"
        )
        self.lbl_status.pack(fill="x", pady=(6, 0))

    # API pública

    def set_status(self, text: str):
        self.lbl_status.config(text=text)

    def set_turn(self, is_my_turn: bool, name: str):
        """Atualiza o rótulo de turno."""
        text  = "Seu turno!" if is_my_turn else f"{name} está jogando"
        color = CLR_TURN_MY  if is_my_turn else CLR_TURN_OPP
        self.lbl_turn.config(text=text, fg=color)

    def set_phase(self, phase: str):
        label = "Fase: Movimentação" if phase == "MOVEMENT" else "Fase: Colocação"
        self.lbl_phase.config(text=label)

    def set_piece_count(self, phase: str,
                        pieces_placed: int, opp_pieces_placed: int,
                        my_on_board: int, opp_on_board: int,
                        opp_name: str):
        if phase == "PLACEMENT":
            self.lbl_my_pieces.config(
                text=f"Suas peças: {TOTAL_PIECES - pieces_placed} p/ colocar")
            self.lbl_opp_pieces.config(
                text=f"{opp_name}: {TOTAL_PIECES - opp_pieces_placed} p/ colocar")
        else:
            self.lbl_my_pieces.config(text=f"Suas peças no tabuleiro: {my_on_board}")
            self.lbl_opp_pieces.config(text=f"Peças do oponente: {opp_on_board}")


class ChatPanel(tk.Frame):
    """
    Exibe o histórico de mensagens e o campo de entrada do chat.
    Chama `on_send(text)` ao pressionar Enter ou o botão Enviar.
    """

    def __init__(self, parent: tk.Widget, on_send=None, **kwargs):
        super().__init__(parent, bg=CLR_BG, **kwargs)
        self._on_send = on_send

        # Título
        tk.Label(self, text="💬  CHAT", bg=CLR_BG, fg=CLR_ACCENT,
                 font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(6, 2))

        # Área de mensagens
        self.area = scrolledtext.ScrolledText(
            self, width=32, height=14, state="disabled",
            bg="#12121E", fg=CLR_TEXT, font=("Courier", 10),
            relief="solid", bd=1, wrap="word"
        )
        self.area.pack(fill="both", expand=True)

        # Campo de entrada + botão
        input_row = tk.Frame(self, bg=CLR_BG)
        input_row.pack(fill="x", pady=(4, 0))

        self.entry = tk.Entry(
            input_row, bg=CLR_PANEL, fg=CLR_TEXT,
            insertbackground=CLR_TEXT, relief="solid", bd=1,
            font=("Arial", 11)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.entry.bind("<Return>", lambda _e: self._fire_send())

        tk.Button(
            input_row, text="Enviar", command=self._fire_send,
            bg=CLR_ACCENT, fg="white", relief="flat",
            font=("Arial", 10, "bold"), padx=8, cursor="hand2"
        ).pack(side="right")

    # Histórico/Mensagens

    def add_message(self, sender: str, text: str):
        """Adiciona uma linha ao histórico de chat."""
        self.area.config(state="normal")
        self.area.insert("end", f"[{sender}] {text}\n")
        self.area.see("end")
        self.area.config(state="disabled")

    def _fire_send(self):
        text = self.entry.get().strip()
        if text and self._on_send:
            self._on_send(text)
            self.entry.delete(0, "end")


class LegendBar(tk.Frame):
    """Barra de legenda das cores do tabuleiro."""

    ITEMS = [
        ("#1A1A2E", "Jogador 1"),
        ("#E8E8E8", "Jogador 2"),
        ("#00CC88", "Selecionado"),
        ("#FFD700", "Mov. válido"),
        ("#FF3333", "Capturável"),
    ]

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=CLR_BG, **kwargs)
        for color, label in self.ITEMS:
            self._make_item(color, label)

    def _make_item(self, color: str, label: str):
        frame = tk.Frame(self, bg=CLR_BG)
        frame.pack(side="left", padx=8)

        dot = tk.Canvas(frame, width=14, height=14,
                        bg=CLR_BG, highlightthickness=0)
        dot.pack(side="left")
        dot.create_oval(1, 1, 13, 13, fill=color,
                        outline="#555555" if color == "#E8E8E8" else "")

        tk.Label(frame, text=label, bg=CLR_BG, fg=CLR_TEXT,
                 font=("Arial", 9)).pack(side="left")
