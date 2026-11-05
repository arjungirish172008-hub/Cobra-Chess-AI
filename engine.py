import chess
import math

# --- 1. Basic Chess Knowledge (Evaluation Function) ---
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 1000
}

KNIGHT_PST = [
    -0.5, -0.4, -0.3, -0.3, -0.3, -0.3, -0.4, -0.5,
    -0.4, -0.2,  0.0,  0.0,  0.0,  0.0, -0.2, -0.4,
    -0.3,  0.0,  0.1,  0.15, 0.15, 0.1,  0.0, -0.3,
    -0.3,  0.05, 0.15, 0.2,  0.2,  0.15, 0.05,-0.3,
    -0.3,  0.0,  0.15, 0.2,  0.2,  0.15, 0.0, -0.3,
    -0.3,  0.5,  0.1,  0.15, 0.15, 0.1,  0.5, -0.3,
    -0.4, -0.2,  0.0,  0.5,  0.5,  0.0, -0.2, -0.4,
    -0.5, -0.4, -0.3, -0.3, -0.3, -0.3, -0.4, -0.5
]

PAWN_PST = [
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,
     0.5,  0.5,  0.5,  0.5,  0.5,  0.5,  0.5,  0.5,
     0.1,  0.1,  0.2,  0.3,  0.3,  0.2,  0.1,  0.1,
     0.05, 0.05, 0.1,  0.25, 0.25, 0.1,  0.05, 0.05,
     0.0,  0.0,  0.0,  0.2,  0.2,  0.0,  0.0,  0.0,
     0.05, -0.05,-0.1,  0.0,  0.0, -0.1, -0.05, 0.05,
     0.05, 0.1,  0.1,  -0.2, -0.2, 0.1,  0.1,  0.05,
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0
]

def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn == chess.WHITE else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    evaluation = 0.0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            val = PIECE_VALUES[piece.piece_type]
            pst_square = square if piece.color == chess.WHITE else chess.square_mirror(square)
            
            pst_val = 0.0
            if piece.piece_type == chess.KNIGHT:
                pst_val = KNIGHT_PST[pst_square]
            elif piece.piece_type == chess.PAWN:
                pst_val = PAWN_PST[pst_square]

            if piece.color == chess.WHITE:
                evaluation += (val + pst_val)
            else:
                evaluation -= (val + pst_val)
                
    return evaluation

# --- 2. Search Algorithm ---
def minimax(board, depth, alpha, beta, is_maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if is_maximizing:
        max_eval = -math.inf
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_best_move(board, depth=3):
    best_move = None
    best_value = math.inf
    
    for move in board.legal_moves:
        board.push(move)
        board_value = minimax(board, depth - 1, -math.inf, math.inf, True)
        board.pop()
        
        if board_value < best_value:
            best_value = board_value
            best_move = move
            
    return best_move