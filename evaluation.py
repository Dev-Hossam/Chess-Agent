

import chess
import math

class Evaluator:
    def evaluate(self, board):
        raise NotImplementedError("Subclasses must implement evaluate")


class MaterialEvaluator(Evaluator):

    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
    
    def evaluate(self, board):
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        white_material = 0
        black_material = 0
        
        # Count material for each side
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
        
        return white_material - black_material


class PositionalEvaluator(Evaluator):

    def __init__(self):
        # Piece-square tables from white's perspective
        self.pawn_table = [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ]
        
        self.knight_table = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ]
        
        self.bishop_table = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5,  5,  5,  5,  5,-10,
            -10,  0,  5,  0,  0,  5,  0,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ]
        
        self.rook_table = [
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0
        ]
        
        self.queen_table = [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ]
        
        self.king_middle_table = [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20
        ]
        
        self.king_end_table = [
            -50,-40,-30,-20,-20,-30,-40,-50,
            -30,-20,-10,  0,  0,-10,-20,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-30,  0,  0,  0,  0,-30,-30,
            -50,-30,-30,-30,-30,-30,-30,-50
        ]
        
        self.piece_tables = {
            chess.PAWN: self.pawn_table,
            chess.KNIGHT: self.knight_table,
            chess.BISHOP: self.bishop_table,
            chess.ROOK: self.rook_table,
            chess.QUEEN: self.queen_table,
            chess.KING: self.king_middle_table  # Default to middle game
        }
    
    def evaluate(self, board):
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Determine if we're in the endgame
        is_endgame = self.is_endgame(board)
        
        white_position = 0
        black_position = 0
        
        # Evaluate each piece's position
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # Get the appropriate table
                if piece.piece_type == chess.KING and is_endgame:
                    table = self.king_end_table
                else:
                    table = self.piece_tables[piece.piece_type]
                
                # Get the position value
                if piece.color == chess.WHITE:
                    position_value = table[square]
                    white_position += position_value
                else:
                    # Flip the square for black's perspective
                    position_value = table[chess.square_mirror(square)]
                    black_position += position_value
        
        return white_position - black_position
    
    def is_endgame(self, board):
        # Count the total material
        white_material = 0
        black_material = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                if piece.color == chess.WHITE:
                    white_material += 1
                else:
                    black_material += 1
        
        # If either side has <= 3 non-pawn pieces, it's an endgame
        return white_material <= 3 or black_material <= 3


class MobilityEvaluator(Evaluator):

    def evaluate(self, board):
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Save the current turn
        original_turn = board.turn
        
        # Count white's mobility
        board.turn = chess.WHITE
        white_mobility = len(list(board.legal_moves))
        
        # Count black's mobility
        board.turn = chess.BLACK
        black_mobility = len(list(board.legal_moves))
        
        # Restore the original turn
        board.turn = original_turn
        
        return white_mobility - black_mobility


class KingSafetyEvaluator(Evaluator):

    def evaluate(self, board):
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        white_king_safety = self.evaluate_king_safety(board, chess.WHITE)
        black_king_safety = self.evaluate_king_safety(board, chess.BLACK)
        
        return white_king_safety - black_king_safety
    
    def evaluate_king_safety(self, board, color):
        """Evaluate the safety of a king"""
        king_square = board.king(color)
        if king_square is None:
            return 0
        
        safety = 0
        
        # Check if the king is in check
        if board.is_check() and board.turn == color:
            safety -= 50
        
        # Check pawn shield
        safety += self.evaluate_pawn_shield(board, king_square, color)
        
        # Check open files near the king
        safety += self.evaluate_open_files(board, king_square, color)
        
        # Check piece attacks near the king
        safety += self.evaluate_piece_attacks(board, king_square, color)
        
        return safety
    
    def evaluate_pawn_shield(self, board, king_square, color):
        shield_value = 0
        
        # Define the squares in front of the king based on color
        if color == chess.WHITE:
            # For white, check the squares above the king
            shield_squares = [
                king_square + 8,  # Directly above
                king_square + 7,  # Diagonally left
                king_square + 9   # Diagonally right
            ]
        else:
            # For black, check the squares below the king
            shield_squares = [
                king_square - 8,  # Directly below
                king_square - 7,  # Diagonally right
                king_square - 9   # Diagonally left
            ]
        
        # Check each shield square
        for square in shield_squares:
            if 0 <= square < 64:  # Make sure the square is on the board
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    shield_value += 10
        
        return shield_value
    
    def evaluate_open_files(self, board, king_square, color):
        file_value = 0
        king_file = chess.square_file(king_square)
        
        # Check the king's file and adjacent files
        for file in range(max(0, king_file - 1), min(8, king_file + 2)):
            is_open = True
            
            # Check if there are any pawns on this file
            for rank in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN:
                    is_open = False
                    break
            
            if is_open:
                file_value -= 15  # Open file near the king is bad
        
        return file_value
    
    def evaluate_piece_attacks(self, board, king_square, color):
        attack_value = 0
        enemy_color = not color
        
        # Define the squares around the king
        king_rank = chess.square_rank(king_square)
        king_file = chess.square_file(king_square)
        
        for rank in range(max(0, king_rank - 1), min(8, king_rank + 2)):
            for file in range(max(0, king_file - 1), min(8, king_file + 2)):
                square = chess.square(file, rank)
                
                # Check if this square is attacked by the enemy
                if board.is_attacked_by(enemy_color, square):
                    attack_value -= 5
        
        return attack_value


class CompositeEvaluator(Evaluator):

    def __init__(self, evaluator_weights):
        self.evaluator_weights = evaluator_weights
    
    def evaluate(self, board):
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        total_score = 0
        
        for evaluator, weight in self.evaluator_weights:
            score = evaluator.evaluate(board)
            total_score += score * weight
        
        return total_score
