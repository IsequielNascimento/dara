"""
dara_client.py — Ponto de entrada do Cliente Dara (Refatorado)
Responsável por: Instanciar o Tkinter, montar o layout da UI, 
iniciar as conexões de rede e repassar o controle para o GameController.
"""

import tkinter as tk

from constants import CLR_BG
from model.game_state import GameState
from network import NetworkManager
from view.board_canvas import BoardCanvas
from view.ui_panels import StatusPanel, ChatPanel, LegendBar

# Importa o controlador que criamos na pasta feat_client
from feat_client.game_controller import GameController


class DaraClientApp:
    def __init__(self):
        # 1. Configuração da Janela Principal (View Raiz)
        self.root = tk.Tk()
        self.root.title("Jogo DARA")
        self.root.configure(bg=CLR_BG)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 2. Instanciação do Modelo (Estado) e da Rede
        self.state = GameState()
        self.network = NetworkManager()

        # 3. Construção da Interface Gráfica (Widgets)
        self._build_layout()

        # 4. Instanciação e ligação do Controlador
        self.controller = GameController(
            root=self.root,
            state=self.state,
            network=self.network,
            board_canvas=self.board_canvas,
            status_panel=self.status,
            chat_panel=self.chat
        )

        # Liga o botão de desistir 
        self.btn_resign.config(command=self.controller.resign)

        # 5. Inicia o fluxo do jogo 
        self.controller.start()

        # 6. Inicia o loop de eventos da interface gráfica
        self.root.mainloop()

    def _build_layout(self):
        """Monta o esqueleto da interface gráfica."""
        main = tk.Frame(self.root, bg=CLR_BG, padx=10, pady=10)
        main.pack()

        # Tabuleiro (coluna 0)
        self.board_canvas = BoardCanvas(main, self.state, my_index=0)
        self.board_canvas.grid(row=0, column=0, rowspan=3, padx=(0, 12))
        self.board_canvas.refresh()

        # Painel direito (coluna 1)
        right = tk.Frame(main, bg=CLR_BG)
        right.grid(row=0, column=1, sticky="nsew")

        self.status = StatusPanel(right)
        self.status.pack(fill="x", pady=(0, 8))

        # Nota: O callback de envio do chat também será injetado pelo GameController
        self.chat = ChatPanel(right)
        self.chat.pack(fill="both", expand=True)

        self.btn_resign = tk.Button(
            right, text="🏳  Desistir",
            bg="#AA2222", fg="white", relief="flat",
            font=("Arial", 11, "bold"), pady=6,
            cursor="hand2", state="disabled"
        )
        self.btn_resign.pack(fill="x", pady=(8, 0))

        # Legenda (linha 3, pegando as duas colunas)
        LegendBar(main).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _on_close(self):
        """Fecha as conexões ao fechar a janela."""
        try:
            self.network.send_game("RESIGN")
        except Exception:
            pass
        self.network.disconnect()
        self.root.destroy()


# Entry point
if __name__ == "__main__":
    DaraClientApp()