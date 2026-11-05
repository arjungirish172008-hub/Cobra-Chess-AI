import os
import sys
import math
import pygame
import chess
from engine import get_best_move, minimax

# --- Default Dimensions ---
DEFAULT_BOARD_SIZE = 512
DEFAULT_PANEL_WIDTH = 180
INITIAL_WIDTH = DEFAULT_BOARD_SIZE + DEFAULT_PANEL_WIDTH
INITIAL_HEIGHT = DEFAULT_BOARD_SIZE
MAX_FPS = 30

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

RAW_IMAGES = {}
SCALED_IMAGES = {}
CURRENT_SQ_SIZE = 0

# --- Smart Image Loader ---
def load_raw_images():
    """Loads piece images once at full resolution so they can be scaled dynamically."""
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    if not os.path.exists(IMAGES_DIR):
        print(f"ERROR: Could not find 'images' folder at: {IMAGES_DIR}")
        sys.exit()

    existing_files = os.listdir(IMAGES_DIR)
    for piece in pieces:
        possible_names = [
            f"{piece}.png",
            f"{piece}.png.png",
            f"{piece[0]}P.png" if piece[1] == 'p' else f"{piece}.png",
            f"{piece[0]}P.png.png" if piece[1] == 'p' else f"{piece}.png.png",
        ]
        found_file = next((name for name in possible_names if name in existing_files), None)
        if found_file:
            img_path = os.path.join(IMAGES_DIR, found_file)
            RAW_IMAGES[piece] = pygame.image.load(img_path)
        else:
            print(f"ERROR: Missing piece image for '{piece}'.")
            sys.exit()

def get_scaled_images(sq_size):
    """Rescales images dynamically when window size changes."""
    global CURRENT_SQ_SIZE, SCALED_IMAGES
    if sq_size != CURRENT_SQ_SIZE and sq_size > 0:
        CURRENT_SQ_SIZE = sq_size
        SCALED_IMAGES = {k: pygame.transform.smoothscale(img, (sq_size, sq_size)) for k, img in RAW_IMAGES.items()}
    return SCALED_IMAGES

# --- Hint Calculation ---
def calculate_hint(board):
    if board.is_game_over() or board.turn != chess.WHITE:
        return None
    best_move = None
    best_val = -math.inf
    for move in board.legal_moves:
        board.push(move)
        val = minimax(board, depth=2, alpha=-math.inf, beta=math.inf, is_maximizing=False)
        board.pop()
        if val > best_val:
            best_val = val
            best_move = move
    return best_move

# --- Board & Coordinates Rendering ---
def draw_board(screen, board, sq_selected, hint_move, sq_size, board_size, coord_font):
    colors = [pygame.Color("#EEEED2"), pygame.Color("#769656")]
    
    # 1. Base Squares
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(col * sq_size, row * sq_size, sq_size, sq_size))

    # 2. Coordinates Overlay (1-8 vertically, a-h horizontally)
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

    for row in range(8):
        sq_color = colors[row % 2]
        txt_color = colors[1] if sq_color == colors[0] else colors[0]
        lbl = coord_font.render(ranks[row], True, txt_color)
        screen.blit(lbl, (4, row * sq_size + 2))

    for col in range(8):
        sq_color = colors[(7 + col) % 2]
        txt_color = colors[1] if sq_color == colors[0] else colors[0]
        lbl = coord_font.render(files[col], True, txt_color)
        lbl_rect = lbl.get_rect(bottomright=(col * sq_size + sq_size - 4, board_size - 2))
        screen.blit(lbl, lbl_rect)

    # 3. Check Warning (Red Square)
    if board.is_check():
        king_square = board.king(board.turn)
        if king_square is not None:
            k_row = 7 - chess.square_rank(king_square)
            k_col = chess.square_file(king_square)
            pygame.draw.rect(screen, pygame.Color("#FF4444"), pygame.Rect(k_col * sq_size, k_row * sq_size, sq_size, sq_size))

    # 4. Cyan Hint Highlight
    if hint_move:
        for sq in [hint_move.from_square, hint_move.to_square]:
            h_row = 7 - chess.square_rank(sq)
            h_col = chess.square_file(sq)
            s = pygame.Surface((sq_size, sq_size))
            s.set_alpha(150)
            s.fill(pygame.Color("#00E5FF"))
            screen.blit(s, (h_col * sq_size, h_row * sq_size))

    # 5. Selected Square & Legal Destinations
    if sq_selected:
        row, col = sq_selected
        s = pygame.Surface((sq_size, sq_size))
        s.set_alpha(120)
        s.fill(pygame.Color("yellow"))
        screen.blit(s, (col * sq_size, row * sq_size))

        selected_square = chess.square(col, 7 - row)
        piece = board.piece_at(selected_square)
        
        if piece and piece.color == board.turn:
            legal_destinations = [m.to_square for m in board.legal_moves if m.from_square == selected_square]
            for dest_square in legal_destinations:
                d_row = 7 - chess.square_rank(dest_square)
                d_col = chess.square_file(dest_square)
                hint_surface = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
                
                if board.piece_at(dest_square):
                    pygame.draw.circle(hint_surface, (230, 50, 50, 180), (sq_size // 2, sq_size // 2), sq_size // 2 - 4, max(2, sq_size // 16))
                else:
                    pygame.draw.circle(hint_surface, (0, 0, 0, 70), (sq_size // 2, sq_size // 2), sq_size // 6)
                    
                screen.blit(hint_surface, (d_col * sq_size, d_row * sq_size))

def draw_pieces(screen, board, sq_size):
    images = get_scaled_images(sq_size)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - chess.square_rank(square)
            col = chess.square_file(square)
            symbol = piece.symbol()
            color_prefix = 'w' if piece.color == chess.WHITE else 'b'
            piece_key = f"{color_prefix}{symbol.upper() if symbol.lower() != 'p' else 'p'}"
            screen.blit(images[piece_key], pygame.Rect(col * sq_size, row * sq_size, sq_size, sq_size))

# --- Sidebar UI ---
def draw_button(screen, rect, text, font, bg_color):
    pygame.draw.rect(screen, bg_color, rect, border_radius=6)
    pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=6)
    txt_surf = font.render(text, True, (255, 255, 255))
    txt_rect = txt_surf.get_rect(center=rect.center)
    screen.blit(txt_surf, txt_rect)

def draw_panel(screen, board, font, btn_undo, btn_hint, btn_resign, btn_reset, btn_fullscreen, resigned, board_size, panel_width, screen_height):
    panel_rect = pygame.Rect(board_size, 0, panel_width, screen_height)
    pygame.draw.rect(screen, pygame.Color("#262421"), panel_rect)
    
    # Title Header (Cobra AI)
    title_font = pygame.font.SysFont("Arial", max(14, int(board_size * 0.04)), bold=True)
    title_surf = title_font.render("COBRA AI", True, pygame.Color("#4CAF50"))
    title_rect = title_surf.get_rect(center=(board_size + panel_width // 2, int(screen_height * 0.06)))
    screen.blit(title_surf, title_rect)

    draw_button(screen, btn_undo, "Back (Undo)", font, pygame.Color("#4A6984"))
    draw_button(screen, btn_hint, "Get Hint", font, pygame.Color("#2E7D32"))
    draw_button(screen, btn_resign, "Resign", font, pygame.Color("#C62828"))
    draw_button(screen, btn_reset, "New Game", font, pygame.Color("#E65100"))
    draw_button(screen, btn_fullscreen, "Toggle Fullscreen", font, pygame.Color("#5E35B1"))

    status_text = ""
    if resigned:
        status_text = "White Resigned!"
    elif board.is_checkmate():
        status_text = "Checkmate!"
    elif board.is_stalemate():
        status_text = "Stalemate!"
    elif board.is_check():
        status_text = "CHECK!"

    if status_text:
        msg_font = pygame.font.SysFont("Arial", max(14, int(screen_height * 0.03)), bold=True)
        msg_surf = msg_font.render(status_text, True, pygame.Color("#FFD700"))
        msg_rect = msg_surf.get_rect(center=(board_size + panel_width // 2, int(screen_height * 0.72)))
        screen.blit(msg_surf, msg_rect)

# --- Main Game Loop ---
def main():
    pygame.init()
    
    screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Cobra Chess AI")
    clock = pygame.time.Clock()

    load_raw_images()

    board = chess.Board()
    sq_selected = ()
    player_clicks = []
    hint_move = None
    resigned = False
    is_fullscreen = False

    running = True
    while running:
        win_w, win_h = screen.get_size()
        
        panel_width = max(180, int(win_w * 0.25))
        board_size = min(win_h, win_w - panel_width)
        sq_size = max(1, board_size // 8)
        board_size = sq_size * 8

        font = pygame.font.SysFont("Arial", max(12, int(board_size * 0.032)), bold=True)
        coord_font = pygame.font.SysFont("Arial", max(10, int(sq_size * 0.22)), bold=True)

        btn_w = int(panel_width * 0.82)
        btn_h = int(board_size * 0.08)
        btn_x = board_size + (panel_width - btn_w) // 2
        
        btn_undo       = pygame.Rect(btn_x, int(board_size * 0.12), btn_w, btn_h)
        btn_hint       = pygame.Rect(btn_x, int(board_size * 0.23), btn_w, btn_h)
        btn_resign     = pygame.Rect(btn_x, int(board_size * 0.34), btn_w, btn_h)
        btn_reset      = pygame.Rect(btn_x, int(board_size * 0.45), btn_w, btn_h)
        btn_fullscreen = pygame.Rect(btn_x, int(board_size * 0.56), btn_w, btn_h)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
                
            elif e.type == pygame.MOUSEBUTTONDOWN:
                location = pygame.mouse.get_pos()
                x, y = location

                if x >= board_size:
                    if btn_undo.collidepoint(location) and not resigned:
                        if len(board.move_stack) >= 2:
                            board.pop()
                            board.pop()
                        elif len(board.move_stack) == 1:
                            board.pop()
                        sq_selected = ()
                        player_clicks = []
                        hint_move = None

                    elif btn_hint.collidepoint(location) and not resigned:
                        hint_move = calculate_hint(board)

                    elif btn_resign.collidepoint(location) and not board.is_game_over():
                        resigned = True
                        sq_selected = ()
                        player_clicks = []

                    elif btn_reset.collidepoint(location):
                        board.reset()
                        sq_selected = ()
                        player_clicks = []
                        hint_move = None
                        resigned = False

                    elif btn_fullscreen.collidepoint(location):
                        is_fullscreen = not is_fullscreen
                        if is_fullscreen:
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)

                elif x < board_size and y < board_size and board.turn == chess.WHITE and not board.is_game_over() and not resigned:
                    col = x // sq_size
                    row = y // sq_size
                    hint_move = None
                    
                    if sq_selected == (row, col):
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected)
                    
                    if len(player_clicks) == 2:
                        start_sq = chess.square(player_clicks[0][1], 7 - player_clicks[0][0])
                        end_sq = chess.square(player_clicks[1][1], 7 - player_clicks[1][0])
                        move = chess.Move(start_sq, end_sq)
                        
                        if board.piece_at(start_sq) and board.piece_at(start_sq).piece_type == chess.PAWN:
                            if chess.square_rank(end_sq) == 7:
                                move = chess.Move(start_sq, end_sq, promotion=chess.QUEEN)

                        if move in board.legal_moves:
                            board.push(move)
                            sq_selected = ()
                            player_clicks = []
                        else:
                            player_clicks = [sq_selected]

        if board.turn == chess.BLACK and not board.is_game_over() and not resigned:
            draw_board(screen, board, sq_selected, hint_move, sq_size, board_size, coord_font)
            draw_pieces(screen, board, sq_size)
            draw_panel(screen, board, font, btn_undo, btn_hint, btn_resign, btn_reset, btn_fullscreen, resigned, board_size, panel_width, win_h)
            pygame.display.flip()
            
            ai_move = get_best_move(board, depth=3)
            if ai_move:
                board.push(ai_move)

        draw_board(screen, board, sq_selected, hint_move, sq_size, board_size, coord_font)
        draw_pieces(screen, board, sq_size)
        draw_panel(screen, board, font, btn_undo, btn_hint, btn_resign, btn_reset, btn_fullscreen, resigned, board_size, panel_width, win_h)
        pygame.display.flip()
        clock.tick(MAX_FPS)
        
    pygame.quit()

if __name__ == "__main__":
    main()