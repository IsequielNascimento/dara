"""
board_canvas.py — Widget de tabuleiro do Jogo Dara
Responsável por: desenho do tabuleiro 5×6, peças, destaques e
captura de cliques do mouse.

Recebe um referência ao GameState para ler o estado atual;
notifica jogadas via callback `on_cell_click(row, col)`.
"""

import tkinter as tk
from constants import (
    ROWS, COLS,
    CLR_BG, CLR_BOARD_BG, CLR_BOARD_LINE,
    CLR_P1, CLR_P1_LT, CLR_P1_SHADOW,
    CLR_P2, CLR_P2_DK, CLR_P2_SHADOW,
    CLR_SELECT, CLR_VALID, CLR_CAPTURE,
)
from model.game_state import GameState


class BoardCanvas(tk.Canvas):
    """
    Canvas Tkinter que renderiza o tabuleiro Dara.

    Uso:
        board = BoardCanvas(parent, state, on_click=handler)
        board.refresh()   # redesenha a partir do estado atual
    """

    CELL   = 75   
    PAD    = 30   # margem 
    PIECE_R = 24  

    def __init__(self, parent: tk.Widget, state: GameState,
                 my_index: int, on_click=None, **kwargs):
        w = COLS * self.CELL + self.PAD * 2 + 40
        h = ROWS * self.CELL + self.PAD * 2 + 30
        super().__init__(parent, width=w, height=h,
                         bg=CLR_BG, highlightthickness=0, **kwargs)

        self.state     = state
        self.my_index  = my_index   
        self._on_click = on_click   

        # Origem do tabuleiro em pixels
        self.ox = self.PAD
        self.oy = self.PAD

        self.bind("<Button-1>", self._handle_click)

    # Ponto de entrada público 
    def refresh(self):
        """Apaga e redesenha todo o tabuleiro a partir do GameState atual."""
        self.delete("all")
        self._draw_background()
        self._draw_grid()
        self._draw_labels()
        self._draw_cells()
        self._draw_border()

    def update_owner(self, my_index: int):
        """Atualiza qual jogador é o 'dono' deste canvas (chamado após ASSIGN)."""
        self.my_index = my_index

    # Clique do mouse 

    def _handle_click(self, event: tk.Event):
        col = (event.x - self.ox) // self.CELL
        row = (event.y - self.oy) // self.CELL
        if 0 <= row < ROWS and 0 <= col < COLS and self._on_click:
            self._on_click(row, col)

    # Desenho 

    def _draw_background(self):
        ox, oy = self.ox, self.oy
        bw = COLS * self.CELL
        bh = ROWS * self.CELL
        self.create_rectangle(
            ox - 10, oy - 10, ox + bw + 10, oy + bh + 10,
            fill=CLR_BOARD_BG, outline=CLR_BOARD_LINE, width=2
        )

    def _draw_grid(self):
        ox, oy, sz = self.ox, self.oy, self.CELL
        bw = COLS * sz
        bh = ROWS * sz
        for r in range(ROWS + 1):
            self.create_line(ox, oy + r * sz, ox + bw, oy + r * sz,
                             fill=CLR_BOARD_LINE, width=1)
        for c in range(COLS + 1):
            self.create_line(ox + c * sz, oy, ox + c * sz, oy + bh,
                             fill=CLR_BOARD_LINE, width=1)

    def _draw_labels(self):
        ox, oy, sz = self.ox, self.oy, self.CELL
        for c in range(COLS):
            self.create_text(
                ox + c * sz + sz // 2, oy - 14,
                text=chr(ord('A') + c),
                fill=CLR_BOARD_LINE, font=("Arial", 10, "bold")
            )
        for r in range(ROWS):
            self.create_text(
                ox - 18, oy + r * sz + sz // 2,
                text=str(r + 1),
                fill=CLR_BOARD_LINE, font=("Arial", 10, "bold")
            )

    def _draw_cells(self):
        state  = self.state
        my_id  = self.my_index + 1
        opp_id = (1 - self.my_index) + 1
        ox, oy, sz, cr = self.ox, self.oy, self.CELL, self.PIECE_R

        for r in range(ROWS):
            for c in range(COLS):
                cx = ox + c * sz + sz // 2
                cy = oy + r * sz + sz // 2

                self._draw_cell_highlight(r, c, cx, cy, sz, my_id, opp_id)

                pid = state.cell(r, c)
                if pid == 0:
                    # ponto de intersecção
                    self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                     fill=CLR_BOARD_LINE, outline="")
                else:
                    self._draw_piece(cx, cy, cr, pid, opp_id)

    def _draw_cell_highlight(self, r: int, c: int,
                              cx: int, cy: int, sz: int,
                              my_id: int, opp_id: int):
        state = self.state
        ox, oy = self.ox, self.oy
        x0, y0 = ox + c * sz + 3, oy + r * sz + 3
        x1, y1 = ox + c * sz + sz - 3, oy + r * sz + sz - 3

        # Célula selecionada para mover
        if state.selected == (r, c):
            self.create_rectangle(x0, y0, x1, y1, fill=CLR_SELECT, outline="")

        # Casas de destino válidas na fase de movimentação
        if (state.selected is not None
                and state.phase == "MOVEMENT"
                and not state.waiting_capture
                and state.current_turn == self.my_index
                and state.cell(r, c) == 0
                and state.is_adjacent(*state.selected, r, c)):
            self.create_rectangle(x0, y0, x1, y1,
                                  fill=CLR_VALID, outline="", stipple="gray50")

    def _draw_piece(self, cx: int, cy: int, cr: int, pid: int, opp_id: int):
        capturable = self.state.waiting_capture and pid == opp_id

        # Anel de captura
        if capturable:
            self.create_oval(cx - cr - 5, cy - cr - 5,
                             cx + cr + 5, cy + cr + 5,
                             fill=CLR_CAPTURE, outline="")

        # Sombra (cor sólida — Tkinter não suporta alpha)
        shadow = CLR_P1_SHADOW if pid == 1 else CLR_P2_SHADOW
        self.create_oval(cx - cr + 3, cy - cr + 3,
                         cx + cr + 3, cy + cr + 3,
                         fill=shadow, outline="")

        # Corpo da peça
        base    = CLR_P1    if pid == 1 else CLR_P2
        hilite  = CLR_P1_LT if pid == 1 else "#FFFFFF"
        border  = "#444466" if pid == 1 else CLR_P2_DK
        self.create_oval(cx - cr, cy - cr, cx + cr, cy + cr,
                         fill=base, outline=border, width=2)

        # Brilho
        self.create_oval(cx - cr + 5, cy - cr + 5,
                         cx - cr + 14, cy - cr + 14,
                         fill=hilite, outline="")

        # Número do jogador
        txt_color = "#FFFFFF" if pid == 1 else "#333333"
        self.create_text(cx, cy, text=str(pid),
                         fill=txt_color, font=("Arial", 10, "bold"))

    def _draw_border(self):
        ox, oy = self.ox, self.oy
        bw = COLS * self.CELL
        bh = ROWS * self.CELL
        self.create_rectangle(ox - 10, oy - 10, ox + bw + 10, oy + bh + 10,
                              outline=CLR_BOARD_LINE, width=2, fill="")
