# ==============================================================================
# ===== ANTES: Importações para o cliente baseado em Sockets ===================
# ==============================================================================
# import socket
# import pickle
# import threading

# ==============================================================================
# ===== DEPOIS: Importações para o cliente baseado em XML-RPC ==================
# ==============================================================================
import xmlrpc.client
import time # Importado para controlar o polling (puxada de dados)
import pygame
import sys
from pygame.locals import *

# ==============================================================================
# ===== ANTES: Configuração de rede com Sockets ================================
# ==============================================================================
# HOST = '127.0.0.1'
# PORT = 55555
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.connect((HOST, PORT))

# ==============================================================================
# ===== DEPOIS: Configuração de rede com XML-RPC ===============================
# ==============================================================================
# A conexão agora é feita através de um "proxy", que representa o servidor remoto.
# Todas as chamadas de função no objeto 'proxy' serão executadas no servidor.
try:
    proxy = xmlrpc.client.ServerProxy('http://127.0.0.1:55555', allow_none=True)
except ConnectionRefusedError:
    print("❌ Erro: Não foi possível conectar ao servidor. Verifique se o servidor está rodando.")
    sys.exit()


# ==============================================================================
# ===== ANTES: Variáveis de estado globais e separadas =========================
# ==============================================================================
# Na versão antiga, cada pedaço de informação do jogo era uma variável global separada.
# meu_id = None
# jogador_atual = None
# tabuleiro = [[0 for _ in range(5)] for _ in range(5)]
# fase = "colocacao"
# mensagens_chat = []
# ultima_selecao = None
# texto_digitado = ""
# campo_chat_ativo = False
# modo_remocao = False
# scroll_offset = 0
# chat_scroll_x = 0

# ==============================================================================
# ===== DEPOIS: Variáveis de estado centralizadas ==============================
# ==============================================================================
# O estado completo do jogo agora é "puxado" do servidor e armazenado em um único dicionário.
# Isso simplifica o gerenciamento do estado.
game_state = {}
meu_id = None
# Variáveis que controlam apenas a interface local (não o estado do jogo) continuam.
ultima_selecao = None
texto_digitado = ""
campo_chat_ativo = False
scroll_offset = 0
chat_scroll_x = 0


# === UI Config (Permanece o mesmo) ===
LARGURA = 900
ALTURA = 600
TAMANHO_CASA = 100
MARGEM = 50
CORES = {
    'fundo': (20, 20, 20),
    'tabuleiro': (255, 255, 255),
    'jogador1': (0, 102, 204),
    'jogador2': (204, 0, 0),
    'selecao': (0, 255, 0),
    'texto': (255, 255, 255),
    'central': (200, 200, 200),
    'linha': (50, 50, 50), # Cor da linha ajustada para melhor visualização
    'botao': (80, 80, 80),
    'botao_hover': (130, 130, 130),
    'botao_texto': (255, 255, 255),
    'campo_chat': (70, 70, 70),
    'campo_chat_ativo': (100, 100, 100),
}

# === Inicialização Pygame (Permanece o mesmo) ===
pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Seega (XML-RPC)') # Título atualizado
fonte = pygame.font.SysFont('Arial', 24)
fonte_chat = pygame.font.SysFont('Arial', 18)
fonte_botao = pygame.font.SysFont('Arial', 20)
clock = pygame.time.Clock()


# ==============================================================================
# ===== ANTES e DEPOIS: Funções de Desenho (Lógica interna ajustada) ===========
# ==============================================================================
# A lógica interna das funções de desenho foi ajustada para ler os dados
# do dicionário `game_state` em vez das variáveis globais separadas. A estrutura
# das funções, no entanto, permanece a mesma.

def desenhar_tabuleiro():
    """Desenha todos os elementos do tabuleiro: fundo, grid, casa central e peças."""
    # ANTES: A função usava a variável global `tabuleiro`
    # DEPOIS: Agora ela busca o tabuleiro de dentro do `game_state`
    tabuleiro_atual = game_state.get("tabuleiro", [])

    # Desenha o fundo branco do tabuleiro
    pygame.draw.rect(tela, CORES['tabuleiro'], (MARGEM, MARGEM, TAMANHO_CASA * 5, TAMANHO_CASA * 5))

    # Desenha as linhas do grid e a casa central
    for i in range(6):
        pygame.draw.line(tela, CORES['linha'], (MARGEM, MARGEM + i * TAMANHO_CASA), (MARGEM + 5 * TAMANHO_CASA, MARGEM + i * TAMANHO_CASA), 2)
        pygame.draw.line(tela, CORES['linha'], (MARGEM + i * TAMANHO_CASA, MARGEM), (MARGEM + i * TAMANHO_CASA, MARGEM + 5 * TAMANHO_CASA), 2)
    centro = 2
    pygame.draw.rect(tela, CORES['central'], (MARGEM + centro * TAMANHO_CASA, MARGEM + centro * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA))

    # Desenha as peças
    if tabuleiro_atual:
        for l, linha in enumerate(tabuleiro_atual):
            for c, valor in enumerate(linha):
                if valor == 1:
                    cor = CORES['jogador1']
                elif valor == 2:
                    cor = CORES['jogador2']
                else:
                    continue
                pygame.draw.circle(tela, cor, (MARGEM + c * TAMANHO_CASA + TAMANHO_CASA // 2, MARGEM + l * TAMANHO_CASA + TAMANHO_CASA // 2), TAMANHO_CASA // 2 - 10)

    # Desenha a seleção da peça
    if ultima_selecao:
        l, c = ultima_selecao
        pygame.draw.rect(tela, CORES['selecao'], (MARGEM + c * TAMANHO_CASA + 2, MARGEM + l * TAMANHO_CASA + 2, TAMANHO_CASA - 4, TAMANHO_CASA - 4), 3)

def desenhar_botao(texto, rect, cor_normal, cor_hover):
    # Esta função não precisou de mudanças
    mouse = pygame.mouse.get_pos()
    clique = pygame.mouse.get_pressed()
    hover = rect.collidepoint(mouse)
    cor = cor_hover if hover else cor_normal
    pygame.draw.rect(tela, cor, rect)
    texto_surf = fonte_botao.render(texto, True, CORES['botao_texto'])
    texto_rect = texto_surf.get_rect(center=rect.center)
    tela.blit(texto_surf, texto_rect)
    return clique[0] and hover

def desenhar_interface():
    """Desenha a UI completa, incluindo status, chat e mensagens de erro."""
    global texto_digitado, scroll_offset, chat_scroll_x # Variáveis locais da UI
    tela.fill(CORES['fundo'])
    desenhar_tabuleiro()

    # ANTES: As variáveis vinham de diferentes locais globais
    # status = f"Jogador: {meu_id or '?'} | Turno: {jogador_atual or '?'} | Fase: {fase}"
    # DEPOIS: Tudo vem do dicionário 'game_state'
    fase = game_state.get('fase', 'Aguardando...')
    jogador_atual = game_state.get('jogador_atual', '?')
    seu_turno = game_state.get('seu_turno', False)
    chat_log = game_state.get("chat_log", [])
    error_msg = game_state.get('error')
    vencedor = game_state.get('vencedor')
    modo_remocao = game_state.get('modo_remocao', False)

    # Exibe o status do jogo
    status_text = f"Jogador: {meu_id or '?'} | Turno: {jogador_atual} | Fase: {fase}"
    if seu_turno and not vencedor:
        status_text += " (Sua vez!)"
    texto = fonte.render(status_text, True, CORES['texto'])
    tela.blit(texto, (20, 10))

    # Desenha os botões
    botao_desistir_rect = pygame.Rect(600, 20, 120, 40)
    desenhar_botao("Desistir", botao_desistir_rect, CORES['botao'], CORES['botao_hover'])
    botao_enviar_rect = pygame.Rect(810, 540, 70, 30)
    desenhar_botao("Enviar", botao_enviar_rect, CORES['botao'], CORES['botao_hover'])

    # Área do chat
    pygame.draw.rect(tela, (40, 40, 40), (600, 80, 280, 440))
    y_pos = 90
    for msg in chat_log[-21:]: # Mostra as últimas 21 mensagens
        texto_chat = fonte_chat.render(msg, True, CORES['texto'])
        tela.blit(texto_chat, (610, y_pos))
        y_pos += 20

    # Campo de entrada de texto
    cor_input = CORES['campo_chat_ativo'] if campo_chat_ativo else CORES['campo_chat']
    pygame.draw.rect(tela, cor_input, (600, 540, 200, 30))
    texto_surface = fonte_chat.render(texto_digitado, True, CORES['texto'])
    tela.blit(texto_surface, (610, 545))
    
    # Exibe mensagens de vitória, erro ou modo de remoção
    if vencedor:
        aviso_txt = f"🏆 Jogador {vencedor} venceu!"
        aviso_cor = (255, 215, 0)
    elif modo_remocao:
        aviso_txt = "Você está bloqueado! Clique em uma peça adversária para remover."
        aviso_cor = (255, 0, 0)
    elif error_msg:
        aviso_txt = f"❌ {error_msg}"
        aviso_cor = (255, 100, 100)
    else:
        aviso_txt = None

    if aviso_txt:
        aviso = fonte.render(aviso_txt, True, aviso_cor)
        tela.blit(aviso, (MARGEM, ALTURA - 40))

    pygame.display.flip()
    return botao_desistir_rect, botao_enviar_rect


# ==============================================================================
# ===== ANTES: Thread dedicada para receber mensagens do servidor ==============
# ==============================================================================
# Esta era a parte mais complexa e propensa a erros do cliente antigo.
# Ela rodava em paralelo, modificando o estado do jogo a qualquer momento.
# def receber_mensagens():
#     global meu_id, jogador_atual, tabuleiro, fase, mensagens_chat, modo_remocao
#     while True:
#         try:
#             data = pickle.loads(sock.recv(4096))
#             tipo = data["tipo"]
#             if tipo == "id":
#                 meu_id = data["jogador"]
#                 mensagens_chat.append(f"Você é o Jogador {meu_id}")
#             elif tipo == "estado":
#                 tabuleiro = data["tabuleiro"]
#                 jogador_atual = data["jogador"]
#                 fase = data["fase"]
#                 mensagens_chat.append(f"Turno do Jogador {jogador_atual} ({fase})")
#             elif tipo == "vitoria":
#                 # ...
#             elif tipo == "chat":
#                 # ...
#             elif tipo == "erro":
#                 # ...
#             elif data["tipo"] == "bloqueado":
#                 # ...
#         except Exception as e:
#             print("Erro:", e)
#             pygame.quit()
#             sys.exit()

# A inicialização da thread também é removida.
# threading.Thread(target=receber_mensagens, daemon=True).start()

# ==============================================================================
# ===== DEPOIS: Função para "puxar" o estado do servidor (sem threads) ========
# ==============================================================================
# Esta função substitui completamente a necessidade da thread 'receber_mensagens'.
# Ela é chamada de forma controlada dentro do loop principal do jogo.
def update_game_state():
    """Pede ao servidor o estado completo do jogo e atualiza o cliente."""
    global game_state, meu_id
    try:
        if meu_id is None:
            meu_id = proxy.register_player()
            if meu_id == 0:
                print("Servidor cheio. Tentando novamente...")
                meu_id = None
                time.sleep(2)
                return
            elif meu_id in [1, 2]:
                print(f"✅ Conectado como Jogador {meu_id}")

        if meu_id:
            # A chamada RPC que busca todo o estado de uma vez.
            game_state = proxy.get_state(meu_id)
            if game_state.get("vencedor"):
                # Pequena pausa para mostrar a mensagem de vitória antes de fechar
                desenhar_interface()
                pygame.time.delay(5000)
                pygame.quit()
                sys.exit()
    except Exception as e:
        print(f"❌ Erro de comunicação com o servidor: {e}")
        game_state['error'] = "Perda de conexão com o servidor."


# ==============================================================================
# ===== DEPOIS: Loop Principal do Jogo com Polling =============================
# ==============================================================================
def main_loop():
    global texto_digitado, campo_chat_ativo, ultima_selecao, scroll_offset, chat_scroll_x
    
    last_update_time = 0
    update_interval = 0.5 # Pergunta ao servidor por atualizações a cada 0.5 segundos

    running = True
    while running:
        # --- Lógica de Polling (NOVO) ---
        if time.time() - last_update_time > update_interval:
            update_game_state()
            last_update_time = time.time()
        
        # --- Processamento de Eventos (Lógica de envio ajustada) ---
        botao_desistir_rect, botao_enviar_rect = desenhar_interface() # Retorna os rects para checar cliques
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            # Lógica de input no chat
            if event.type == KEYDOWN and campo_chat_ativo:
                if event.key == K_RETURN and texto_digitado.strip():
                    proxy.send_chat_message(meu_id, texto_digitado)
                    texto_digitado = ""
                elif event.key == K_BACKSPACE:
                    texto_digitado = texto_digitado[:-1]
                else:
                    texto_digitado += event.unicode
            
            # Lógica de cliques do mouse
            elif event.type == MOUSEBUTTONDOWN:
                x, y = event.pos
                
                # Clique no botão de desistir
                if botao_desistir_rect.collidepoint(event.pos) and game_state.get('seu_turno'):
                    proxy.surrender(meu_id)
                
                # Clique no botão de enviar chat
                elif botao_enviar_rect.collidepoint(event.pos) and texto_digitado.strip():
                    proxy.send_chat_message(meu_id, texto_digitado)
                    texto_digitado = ""
                
                # Ativa/desativa o campo de chat
                elif pygame.Rect(600, 540, 200, 30).collidepoint(x, y):
                    campo_chat_ativo = True
                else:
                    campo_chat_ativo = False
                
                # Clique no tabuleiro
                if (MARGEM <= x < MARGEM + 5 * TAMANHO_CASA and
                    MARGEM <= y < MARGEM + 5 * TAMANHO_CASA):
                    coluna = (x - MARGEM) // TAMANHO_CASA
                    linha = (y - MARGEM) // TAMANHO_CASA
                    handle_board_click(linha, coluna)

        clock.tick(30)

    # ANTES: Fechava o socket antes de sair
    # sock.close()
    pygame.quit()
    sys.exit()

def handle_board_click(linha, coluna):
    """Função chamada quando há um clique no tabuleiro. Ela faz a chamada RPC apropriada."""
    global ultima_selecao
    
    # Validações com base no estado atual
    if not game_state.get('seu_turno') or game_state.get('vencedor'):
        return

    fase = game_state.get('fase')
    tabuleiro = game_state.get('tabuleiro', [])
    modo_remocao = game_state.get('modo_remocao', False)

    if modo_remocao:
        # ANTES: sock.sendall(pickle.dumps({"tipo": "remover", ...}))
        # DEPOIS:
        proxy.remove_piece_when_blocked(meu_id, linha, coluna)
        return

    if fase == "colocacao":
        # ANTES: sock.sendall(pickle.dumps({"tipo": "colocacao", ...}))
        # DEPOIS:
        proxy.place_piece(meu_id, linha, coluna)
    
    elif fase == "movimentacao":
        if ultima_selecao is None:
            if tabuleiro and tabuleiro[linha][coluna] == meu_id:
                ultima_selecao = (linha, coluna)
        else:
            orig_l, orig_c = ultima_selecao
            # ANTES: sock.sendall(pickle.dumps({"tipo": "movimento", ...}))
            # DEPOIS:
            proxy.move_piece(meu_id, orig_l, orig_c, linha, coluna)
            ultima_selecao = None

# ==============================================================================
# ===== ANTES: Loop principal antigo que chamava a interface ===================
# ==============================================================================
# O loop foi completamente reestruturado e agora é a função main_loop()
# while True:
#     botao_desistir_rect, botao_enviar_rect = desenhar_interface()
#     for event in pygame.event.get():
#         # ... (toda a lógica de eventos estava aqui)


# ==============================================================================
# ===== DEPOIS: Ponto de entrada do programa ===================================
# ==============================================================================
if __name__ == "__main__":
    main_loop()