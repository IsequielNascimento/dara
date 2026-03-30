"""
feat_client/game_controller.py — Controlador principal do Jogo Dara
Responsável por: 
- Processar eventos de clique na interface (View)
- Atualizar o estado do jogo (Model)
- Enviar e receber mensagens via rede (Network)
- Atualizar a interface com base nas respostas
obs buscar dividir em vários controllers dps.
"""

import tkinter as tk
from tkinter import messagebox
from constants import TOTAL_PIECES, CLR_BG, CLR_ACCENT, CLR_PANEL, CLR_TEXT

class GameController:
    def __init__(self, root, state, network, board_canvas, status_panel, chat_panel):
        # Injeção de Dependências
        self.root = root
        self.state = state
        self.network = network
        self.board_canvas = board_canvas
        self.status = status_panel
        self.chat = chat_panel

        self.my_name = "Jogador"
        self.opp_name = "Oponente"

        # Registra os callbacks de rede no controlador
        self.network.on_game_message(
            lambda msg: self.root.after(0, self._handle_game_msg, msg)
        )
        self.network.on_chat_message(
            lambda sender, text: self.root.after(0, self.chat.add_message, sender, text)
        )
        self.network.on_disconnect(
            lambda err: self.root.after(0, self._on_disconnect, err)
        )

        # Registra o callback de clique do tabuleiro
        self.board_canvas._on_click = self._on_cell_click

        # Registra o callback de envio do chat
        self.chat._on_send = self._send_chat

    def start(self):
        """Inicia o fluxo do jogo abrindo a tela de conexão."""
        self._connect_dialog()

    # Diálogo de conexão

    def _connect_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Conectar ao Servidor DARA")
        dlg.configure(bg=CLR_BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Jogo DARA", bg=CLR_BG, fg=CLR_ACCENT,
                 font=("Arial", 16, "bold")).grid(
                     row=0, column=0, columnspan=2, pady=(16, 12), padx=24)

        fields = [("Seu nome:", "Jogador"), ("IP do Servidor:", "localhost")]
        vars_  = []
        for i, (lbl, default) in enumerate(fields):
            tk.Label(dlg, text=lbl, bg=CLR_BG, fg=CLR_TEXT,
                     font=("Arial", 11)).grid(
                         row=i + 1, column=0, sticky="e", padx=(24, 8), pady=6)
            v = tk.StringVar(value=default)
            vars_.append(v)
            tk.Entry(dlg, textvariable=v, bg=CLR_PANEL, fg=CLR_TEXT,
                     insertbackground=CLR_TEXT, relief="solid", bd=1,
                     font=("Arial", 11), width=20).grid(
                         row=i + 1, column=1, padx=(0, 24), pady=6)

        def attempt():
            name = vars_[0].get().strip() or "Jogador"
            host = vars_[1].get().strip() or "localhost"
            err  = self.network.connect(host, name)
            if err:
                messagebox.showerror("Erro de Conexão",
                                     f"Não foi possível conectar:\n{err}",
                                     parent=dlg)
            else:
                self.my_name = name
                dlg.destroy()
                self.status.set_status("Conectado! Aguardando oponente...")

        tk.Button(dlg, text="Conectar", command=attempt,
                  bg=CLR_ACCENT, fg="white", relief="flat",
                  font=("Arial", 11, "bold"), padx=16, pady=6,
                  cursor="hand2").grid(
                      row=3, column=0, columnspan=2, pady=(8, 16))

        dlg.bind("<Return>", lambda _e: attempt())
        self.root.wait_window(dlg)

    # Tratamento de mensagens do socket de jogo

    def _handle_game_msg(self, msg: str):
        if msg.startswith("ASSIGN:"):
            self._on_assign(int(msg[7:]))

        elif msg.startswith("NAMES:"):
            _, p1, p2 = msg.split(":")
            self.opp_name = p2 if self.state.current_turn == 0 else p1
            self._refresh_counts()

        elif msg.startswith("START:"):
            self.state.current_turn = int(msg[6:])
            self._update_turn()
            self.status.set_status("Jogo iniciado! Fase de Colocação.")
            self.chat.add_message("Sistema",
                f" !Jogo iniciado! {self._name_of(self.state.current_turn)} começa.")
            self.board_canvas.refresh()

        elif msg.startswith("TURN:"):
            self.state.current_turn = int(msg[5:])
            self.state.waiting_capture = False
            self.state.selected = None
            self._update_turn()
            self.board_canvas.refresh()

        elif msg.startswith("PHASE:"):
            self.state.enter_movement_phase()
            self.status.set_phase("MOVEMENT")
            self.chat.add_message("Sistema", "⚔ Fase de Movimentação iniciada!")
            self.board_canvas.refresh()

        elif msg.startswith("MOVE:"):
            self._apply_opponent_move(msg)

        elif msg.startswith("LINE3:"):
            if int(msg[6:]) == self.board_canvas.my_index:
                self.state.waiting_capture = True
                self.status.set_status(
                    "Você formou 3 em linha! Clique na peça do oponente para capturar.")
                self.board_canvas.refresh()

        elif msg.startswith("CAPTURED:"):
            _, r, c = msg.split(":")
            self.state.remove_piece(int(r), int(c))
            self.state.waiting_capture = False
            self._refresh_counts()
            self.board_canvas.refresh()

        elif msg.startswith("RESIGN:"):
            self.chat.add_message("Sistema", f"🏳 {msg[7:]} desistiu.")

        elif msg.startswith("WINNER:"):
            parts = msg.split(":")
            self._show_winner(int(parts[1]), parts[2])

        elif msg.startswith("DISCONNECT:"):
            self.chat.add_message("Sistema", f"⚠ {msg[11:]} desconectou.")

    # Jogadas do oponente

    def _apply_opponent_move(self, msg: str):
        parts  = msg.split(":")
        opp_id = (1 - self.board_canvas.my_index) + 1
        if len(parts) == 3:
            r, c = int(parts[1]), int(parts[2])
            self.state.board[r][c] = opp_id
            self.state.pieces_placed[opp_id - 1] += 1
            self._check_phase_transition()
            self._refresh_counts()
        elif len(parts) == 5:
            r1, c1, r2, c2 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
            self.state.move_piece(r1, c1, r2, c2)
        self.board_canvas.refresh()

    # Clique no tabuleiro

    def _on_cell_click(self, row: int, col: int):
        if self.state.current_turn != self.board_canvas.my_index:
            return
        if self.state.phase == "PLACEMENT":
            self._do_placement(row, col)
        elif self.state.phase == "MOVEMENT":
            if self.state.waiting_capture:
                self._do_capture(row, col)
            else:
                self._do_movement(row, col)

    def _do_placement(self, row: int, col: int):
        my_id = self.board_canvas.my_index + 1
        if self.state.pieces_placed[my_id - 1] >= TOTAL_PIECES:
            return
        if self.state.cell(row, col) != 0:
            self.status.set_status("Casa ocupada!")
            return
        self.state.place_piece(row, col, my_id)
        
        # Impede formação de trinca na fase de colocação
        if self.state.makes_line3(row, col, my_id):
            self.state.remove_piece(row, col)
            self.state.pieces_placed[my_id - 1] -= 1
            self.status.set_status("Proibido formar 3 em linha na fase de colocação!")
            return
            
        self._refresh_counts()
        self.board_canvas.refresh()
        self.network.send_game(f"MOVE:{row}:{col}")
        self._check_phase_transition()
        self.network.send_game("TURN_DONE")

    def _do_movement(self, row: int, col: int):
        my_id = self.board_canvas.my_index + 1
        sel   = self.state.selected

        if sel is None:
            if self.state.cell(row, col) != my_id:
                self.status.set_status("Selecione uma de suas peças.")
                return
            self.state.selected = (row, col)
            self.status.set_status("Peça selecionada. Clique em uma casa adjacente vazia.")
            self.board_canvas.refresh()
        else:
            sr, sc = sel
            if (row, col) == sel:
                self.state.selected = None
                self.board_canvas.refresh()
                return
            if not self.state.is_adjacent(sr, sc, row, col):
                self.status.set_status("Mova para uma casa adjacente (horizontal/vertical).")
                return
            if self.state.cell(row, col) != 0:
                self.status.set_status("Casa ocupada!")
                return
            
            self.state.move_piece(sr, sc, row, col)
            self.network.send_game(f"MOVE:{sr}:{sc}:{row}:{col}")
            self.state.selected = None
            self.board_canvas.refresh()
            
            # Verifica captura após movimento
            if self.state.makes_line3(row, col, my_id):
                self.state.waiting_capture = True
                self.network.send_game(f"LINE3:{self.board_canvas.my_index}")
                self.status.set_status(
                    "Você formou 3 em linha! Clique na peça do oponente para capturar.")
                self.board_canvas.refresh()
                return
            self.network.send_game("TURN_DONE")

    def _do_capture(self, row: int, col: int):
        opp_id = (1 - self.board_canvas.my_index) + 1
        if self.state.cell(row, col) != opp_id:
            self.status.set_status("Clique em uma peça do oponente para capturar!")
            return
        self.state.remove_piece(row, col)
        self.state.waiting_capture = False
        self._refresh_counts()
        self.board_canvas.refresh()
        self.network.send_game(f"CAPTURED:{row}:{col}")

    # Helpers

    def _on_assign(self, idx: int):
        self.board_canvas.update_owner(idx)
        self.root.title(f"Jogo DARA — {self.my_name} (Jogador {idx + 1})")

    def _name_of(self, idx: int) -> str:
        return self.my_name if idx == self.board_canvas.my_index else self.opp_name

    def _update_turn(self):
        is_my = self.state.current_turn == self.board_canvas.my_index
        self.status.set_turn(is_my, self._name_of(self.state.current_turn))
        self.status.set_status(
            "Sua vez de jogar." if is_my
            else f"Aguardando {self._name_of(self.state.current_turn)}..."
        )

    def _refresh_counts(self):
        my_id  = self.board_canvas.my_index + 1
        opp_id = (1 - self.board_canvas.my_index) + 1
        self.status.set_piece_count(
            phase             = self.state.phase,
            pieces_placed     = self.state.pieces_placed[my_id - 1],
            opp_pieces_placed = self.state.pieces_placed[opp_id - 1],
            my_on_board       = self.state.count_pieces(my_id),
            opp_on_board      = self.state.count_pieces(opp_id),
            opp_name          = self.opp_name,
        )

    def _check_phase_transition(self):
        if self.state.phase == "PLACEMENT" and self.state.all_placed():
            self.state.enter_movement_phase()
            self.status.set_phase("MOVEMENT")
            self.network.send_game("PHASE_MOVEMENT")

    def _send_chat(self, text: str):
        self.network.send_chat(text)
        self.chat.add_message("Você", text)

    def resign(self):
        if messagebox.askyesno("Desistir", "Deseja realmente desistir?"):
            self.network.send_game("RESIGN")

    def _show_winner(self, win_idx: int, win_name: str):
        i_won = win_idx == self.board_canvas.my_index
        title = ":D Você Venceu!" if i_won else ":( Você Perdeu"
        msg   = (f"Parabéns, {win_name}! Você venceu!" if i_won
                 else f"{win_name} venceu o jogo!")
        self.chat.add_message("Sistema", (":D " if i_won else "💀 ") + msg)
        messagebox.showinfo(title, msg)

    def _on_disconnect(self, err: str):
        self.status.set_status("Conexão perdida.")
        messagebox.showwarning("Desconectado", f"Conexão encerrada:\n{err}")