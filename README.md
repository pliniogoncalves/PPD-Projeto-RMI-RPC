# Jogo Seega com Comunicação XML-RPC

Este é um projeto do jogo de tabuleiro Seega, implementado em Python. O jogo utiliza XML-RPC para a comunicação entre o servidor e os clientes, e possui uma interface gráfica (com Pygame).

## Estrutura do Projeto

-   **`server_rpc.py`**: O servidor central do jogo. Ele gerencia o estado do tabuleiro, as regras, os turnos dos jogadores e a comunicação.
-   **`gui_rpc.py`**: O cliente com interface gráfica. Utiliza a biblioteca Pygame para desenhar o tabuleiro e interagir com o jogador.
-   **`game_logic.py`**: Um módulo que contém toda a lógica de regras do jogo Seega (validação de movimentos, capturas, condição de vitória, etc.). É utilizado pelo servidor.

## Requisitos

-   Python 3.x
-   Pygame

Para instalar o Pygame, execute:

```bash
pip install pygame
```

## Como Executar o Jogo

Para jogar, você precisa iniciar o servidor e, em seguida, dois clientes.

### 1. Iniciar o Servidor

Abra um terminal e execute o arquivo do servidor. Ele ficará aguardando as conexões dos jogadores.

```bash
python server.py
```

Você deverá ver a mensagem: `🎮 Servidor XML-RPC do jogo Seega iniciado em http://127.0.0.1:55555`

### 2. Iniciar os Clientes

#### Para jogar com a Interface Gráfica:

Abra **dois novos terminais** (um para cada jogador) e execute o seguinte comando em cada um:

```bash
python gui.py
```

Duas janelas do jogo aparecerão, uma para o Jogador 1 e outra para o Jogador 2.

**Importante**: O servidor deve estar em execução antes que qualquer cliente possa se conectar. O primeiro cliente a se conectar será o Jogador 1, e o segundo será o Jogador 2.
