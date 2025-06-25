import xmlrpc.client
import time 
import pygame
import sys
from pygame.locals import *

try:
    proxy = xmlrpc.client.ServerProxy('http://127.0.0.1:55555', allow_none=True)
except ConnectionRefusedError:
    print("❌ Erro: Não foi possível conectar ao servidor. Verifique se o servidor está rodando.")
    sys.exit()

game_state = {}
meu_id = None

ultima_selecao = None
texto_digitado = ""
campo_chat_ativo = False
scroll_offset = 0
chat_scroll_x = 0

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
    'linha': (50, 50, 50),
    'botao': (80, 80, 80),
    'botao_hover': (130, 130, 130),
    'botao_texto': (255, 255, 255),
    'campo_chat': (70, 70, 70),
    'campo_chat_ativo': (100, 100, 100),
}

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Seega (XML-RPC)')
fonte = pygame.font.SysFont('Arial', 24)
fonte_chat = pygame.font.SysFont('Arial', 18)
fonte_botao = pygame.font.SysFont('Arial', 20)
clock = pygame.time.Clock()

def desenhar_tabuleiro():
    """Desenha todos os elementos do tabuleiro: fundo, grid, casa central e peças."""
    tabuleiro_atual = game_state.get("tabuleiro", [])

    pygame.draw.rect(tela, CORES['tabuleiro'], (MARGEM, MARGEM, TAMANHO_CASA * 5, TAMANHO_CASA * 5))

    for i in range(6):
        pygame.draw.line(tela, CORES['linha'], (MARGEM, MARGEM + i * TAMANHO_CASA), (MARGEM + 5 * TAMANHO_CASA, MARGEM + i * TAMANHO_CASA), 2)
        pygame.draw.line(tela, CORES['linha'], (MARGEM + i * TAMANHO_CASA, MARGEM), (MARGEM + i * TAMANHO_CASA, MARGEM + 5 * TAMANHO_CASA), 2)
    centro = 2
    pygame.draw.rect(tela, CORES['central'], (MARGEM + centro * TAMANHO_CASA, MARGEM + centro * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA))

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

    if ultima_selecao:
        l, c = ultima_selecao
        pygame.draw.rect(tela, CORES['selecao'], (MARGEM + c * TAMANHO_CASA + 2, MARGEM + l * TAMANHO_CASA + 2, TAMANHO_CASA - 4, TAMANHO_CASA - 4), 3)

def desenhar_botao(texto, rect, cor_normal, cor_hover):
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
    global texto_digitado, scroll_offset, chat_scroll_x
    tela.fill(CORES['fundo'])
    desenhar_tabuleiro()

    fase = game_state.get('fase', 'Aguardando...')
    jogador_atual = game_state.get('jogador_atual', '?')
    seu_turno = game_state.get('seu_turno', False)
    chat_log = game_state.get("chat_log", [])
    error_msg = game_state.get('error')
    vencedor = game_state.get('vencedor')
    modo_remocao = game_state.get('modo_remocao', False)

    status_text = f"Jogador: {meu_id or '?'} | Turno: {jogador_atual} | Fase: {fase}"
    if seu_turno and not vencedor:
        status_text += " (Sua vez!)"
    texto = fonte.render(status_text, True, CORES['texto'])
    tela.blit(texto, (20, 10))

    botao_desistir_rect = pygame.Rect(600, 20, 120, 40)
    desenhar_botao("Desistir", botao_desistir_rect, CORES['botao'], CORES['botao_hover'])
    botao_enviar_rect = pygame.Rect(810, 540, 70, 30)
    desenhar_botao("Enviar", botao_enviar_rect, CORES['botao'], CORES['botao_hover'])

    pygame.draw.rect(tela, (40, 40, 40), (600, 80, 280, 440))
    y_pos = 90
    for msg in chat_log[-21:]:
        texto_chat = fonte_chat.render(msg, True, CORES['texto'])
        tela.blit(texto_chat, (610, y_pos))
        y_pos += 20

    cor_input = CORES['campo_chat_ativo'] if campo_chat_ativo else CORES['campo_chat']
    pygame.draw.rect(tela, cor_input, (600, 540, 200, 30))
    texto_surface = fonte_chat.render(texto_digitado, True, CORES['texto'])
    tela.blit(texto_surface, (610, 545))
    
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
            game_state = proxy.get_state(meu_id)
            if game_state.get("vencedor"):
                desenhar_interface()
                pygame.time.delay(5000)
                pygame.quit()
                sys.exit()
    except Exception as e:
        print(f"❌ Erro de comunicação com o servidor: {e}")
        game_state['error'] = "Perda de conexão com o servidor."

def main_loop():
    global texto_digitado, campo_chat_ativo, ultima_selecao, scroll_offset, chat_scroll_x
    
    last_update_time = 0
    update_interval = 0.5

    running = True
    while running:
        if time.time() - last_update_time > update_interval:
            update_game_state()
            last_update_time = time.time()
        
        botao_desistir_rect, botao_enviar_rect = desenhar_interface()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            if event.type == KEYDOWN and campo_chat_ativo:
                if event.key == K_RETURN and texto_digitado.strip():
                    proxy.send_chat_message(meu_id, texto_digitado)
                    texto_digitado = ""
                elif event.key == K_BACKSPACE:
                    texto_digitado = texto_digitado[:-1]
                else:
                    texto_digitado += event.unicode
            
            elif event.type == MOUSEBUTTONDOWN:
                x, y = event.pos
                
                if botao_desistir_rect.collidepoint(event.pos) and game_state.get('seu_turno'):
                    proxy.surrender(meu_id)
                
                elif botao_enviar_rect.collidepoint(event.pos) and texto_digitado.strip():
                    proxy.send_chat_message(meu_id, texto_digitado)
                    texto_digitado = ""
                
                elif pygame.Rect(600, 540, 200, 30).collidepoint(x, y):
                    campo_chat_ativo = True
                else:
                    campo_chat_ativo = False
                
                if (MARGEM <= x < MARGEM + 5 * TAMANHO_CASA and
                    MARGEM <= y < MARGEM + 5 * TAMANHO_CASA):
                    coluna = (x - MARGEM) // TAMANHO_CASA
                    linha = (y - MARGEM) // TAMANHO_CASA
                    handle_board_click(linha, coluna)

        clock.tick(30)

    pygame.quit()
    sys.exit()

def handle_board_click(linha, coluna):
    """Função chamada quando há um clique no tabuleiro. Ela faz a chamada RPC apropriada."""
    global ultima_selecao
    
    if not game_state.get('seu_turno') or game_state.get('vencedor'):
        return

    fase = game_state.get('fase')
    tabuleiro = game_state.get('tabuleiro', [])
    modo_remocao = game_state.get('modo_remocao', False)

    if modo_remocao:
        proxy.remove_piece_when_blocked(meu_id, linha, coluna)
        return

    if fase == "colocacao":
        proxy.place_piece(meu_id, linha, coluna)
    
    elif fase == "movimentacao":
        if ultima_selecao is None:
            if tabuleiro and tabuleiro[linha][coluna] == meu_id:
                ultima_selecao = (linha, coluna)
        else:
            orig_l, orig_c = ultima_selecao

            proxy.move_piece(meu_id, orig_l, orig_c, linha, coluna)
            ultima_selecao = None

if __name__ == "__main__":
    main_loop()