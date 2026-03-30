```markdown
# Jogo DARA — Python Modular MVC com Dois Sockets TCP
**Programação Paralela e Distribuída — IFCE 2026.1**

---

## Arquitetura e Estrutura de Arquivos

O projeto utiliza o padrão **MVC (Model-View-Controller)**, separando a interface gráfica, as regras de negócio e a comunicação de rede.

```text
DARA_V2/
│
├── .gitignore
├── constants.py          # Portas, dimensões do tabuleiro e paleta de cores globais
├── dara_client.py        # Entry point do cliente — Instancia a UI e liga o Controller
├── dara_server.py        # Servidor árbitro com 4 threads (2 jogo + 2 chat)
├── network.py            # Gerenciamento de rede (Sockets TCP 9090 e 9091)
├── README.md
│
├── feat_client/          # Controller (O "Cérebro" da interface)
│   └── game_controller.py  # Processa regras, trata cliques e orquestra Model/View/Network
│
├── model/                # Model (Regras de negócio e dados puros)
│   └── game_state.py       # Matriz do tabuleiro, contagem de peças e validação de trincas
│
└── view/                 # View (Interface Gráfica Tkinter)
    ├── board_canvas.py     # Widget Canvas que desenha o tabuleiro 5x6 e as peças
    └── ui_panels.py        # StatusPanel, ChatPanel e LegendBar
```

---

## Arquitetura de Rede (Dois Sockets TCP simultâneos)

Para evitar bloqueios de thread (onde o jogador não conseguiria conversar no chat enquanto espera o turno do adversário), o sistema implementa multiplexação física utilizando duas portas distintas:

```text
              ┌─── Socket JOGO (9090) ────────────────┐
Cliente A ────┤                                        ├──── Servidor
              └─── Socket CHAT (9091) ────────────────┘
                                                         
              ┌─── Socket JOGO (9090) ────────────────┐
Cliente B ────┤                                        ├──── Servidor
              └─── Socket CHAT (9091) ────────────────┘
```

O servidor atua como um roteador passivo, mantendo **4 sockets ativos** (2 jogadores × 2 portas) e **4 threads de leitura independentes** (`Game-0`, `Game-1`, `Chat-0`, `Chat-1`).

No lado do cliente, o `NetworkManager` levanta **2 threads de escuta daemon** (`GameReader`, `ChatReader`) operando em paralelo à thread principal da interface gráfica (Tkinter).

---

## Protocolo de Comunicação

### 1. Socket de Jogo (Porta TCP 9090)
Fluxo exclusivo para regras de negócio e sincronização de estado.

| Comando / Mensagem     | Origem → Destino   | Ação / Significado                                 |
|------------------------|--------------------|----------------------------------------------------|
| `ASSIGN:N`             | Srv → Cli          | Define o ID do jogador (0 ou 1) na conexão inicial |
| `NAMES:p1:p2`          | Srv → Cli          | Distribui os nomes de exibição                     |
| `START:N`              | Srv → Cli          | Libera o tabuleiro; `N` indica quem começa         |
| `TURN:N`               | Srv → Cli          | Transfere o controle da UI para o jogador `N`      |
| `PHASE:MOVEMENT`       | Srv → Cli          | Transição global para a fase de movimentação       |
| `MOVE:r:c`             | Cli ↔ Srv ↔ Cli    | Peça inserida na coordenada [linha:coluna]         |
| `MOVE:r1:c1:r2:c2`     | Cli ↔ Srv ↔ Cli    | Peça movida da origem [r1,c1] para o destino [r2,c2]|
| `LINE3:N`              | Cli ↔ Srv ↔ Cli    | Jogador `N` formou uma trinca (Habilita Captura)   |
| `CAPTURED:r:c`         | Cli ↔ Srv ↔ Cli    | Peça inimiga na coordenada [r,c] foi removida      |
| `TURN_DONE`            | Cli → Srv          | Finaliza o turno atual sem incidentes              |
| `PHASE_MOVEMENT`       | Cli → Srv          | Solicita ao servidor a transição de fase           |
| `RESIGN`               | Cli → Srv          | Declara desistência formal da partida              |
| `WINNER:N:nome`        | Srv → Cli          | Encerra o jogo e declara o vencedor                |
| `DISCONNECT:nome`      | Srv → Cli          | Alerta sobre queda de conexão do adversário        |

### 2. Socket de Chat (Porta TCP 9091)
Fluxo exclusivo para comunicação textual em tempo real.

| Formato                | Origem → Destino   | Ação / Significado                                 |
|------------------------|--------------------|----------------------------------------------------|
| `<texto livre>`        | Cli → Srv          | String bruta enviada pelo usuário via UI           |
| `<nome_remetente>: <texto>` | Srv → Cli     | Servidor formata e entrega ao adversário           |

---

## Como Executar

### Pré-requisitos
```bash
python --version        # Necessário Python 3.8 ou superior
python -c "import tkinter; print('OK')"   # O módulo Tkinter deve retornar OK
```
*No Ubuntu/Debian:* `sudo apt-get install python3-tk`

### 1. Iniciar o Servidor (O Árbitro)
Abra o terminal na máquina que atuará como host e execute:
```bash
python dara_server.py
```
*O servidor aguardará silenciosamente nas portas 9090 e 9091.*

### 2. Iniciar os Clientes (Os Jogadores)

**Cenário A: Teste Local (Mesma Máquina)**
Abra dois terminais distintos na mesma máquina do servidor:
```bash
# Terminal 1 (Jogador 1)
python dara_client.py   # Utilize IP: localhost na interface

# Terminal 2 (Jogador 2)
python dara_client.py   # Utilize IP: localhost na interface
```

**Cenário B: Rede Real (Máquina Física ↔ Máquina Virtual)**
1. Descubra o IP IPv4 da máquina onde o servidor está rodando (`ipconfig` no Windows, `ip a` no Linux).
2. Certifique-se de que a Máquina Virtual está configurada em **Modo Bridge** (Bridged Adapter).
3. Desative temporariamente o Firewall do host ou crie regras de permissão de entrada para as portas TCP 9090 e 9091.

```bash
# Na Máquina A (Física)
python dara_client.py   # Utilize o IP da rede (ex: 192.168.1.15)

# Na Máquina B (Virtual)
python dara_client.py   # Utilize o mesmo IP da rede (ex: 192.168.1.15)
```

---

## Tabela de Concorrência (Threads)


| Aplicação      | Nome da Thread | Responsabilidade Principal                           |
|----------------|----------------|------------------------------------------------------|
| `dara_server`  | `Game-0`       | Roteamento de comandos de jogo do P1                 |
| `dara_server`  | `Game-1`       | Roteamento de comandos de jogo do P2                 |
| `dara_server`  | `Chat-0`       | Roteamento de mensagens de texto do P1               |
| `dara_server`  | `Chat-1`       | Roteamento de mensagens de texto do P2               |
| `dara_client`  | `GameReader`   | Escuta contínua de comandos oriundos do servidor     |
| `dara_client`  | `ChatReader`   | Escuta contínua de mensagens oriundas do servidor    |
| `dara_client`  | `MainThread`   | Renderização do Canvas e processamento de eventos UI |