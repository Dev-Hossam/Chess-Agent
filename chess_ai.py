import chess
import random
import time
import math

class ChessAI:
    def __init__(self, evaluator=None):
        #Initialize the ChessAI with an evaluator
        self.evaluator = evaluator
        self.nodes_evaluated = 0

    def get_best_move(self, board):
        #Get the best move for the current position
        raise NotImplementedError("Subclasses must implement get_best_move")

    def reset_stats(self):
        #Reset all our statistics for a new search
        self.nodes_evaluated = 0


class RandomAI(ChessAI):
    #AI that makes random moves that are legal

    def get_best_move(self, board):
        #Return a random legal move
        self.reset_stats()
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None


class GreedyAI(ChessAI):
    #AI that makes the move with the best immediate evaluation

    def get_best_move(self, board):
        #Return the move with the best immediate evaluation
        self.reset_stats()
        best_move = None
        best_eval = float('-inf') if board.turn == chess.WHITE else float('inf')

        for move in board.legal_moves:
            board.push(move)
            self.nodes_evaluated += 1

            # Evaluate the position after the move
            evaluation = self.evaluator.evaluate(board)

            # Update best move if this is better
            if board.turn == chess.BLACK:  # We just made a move for white
                if evaluation > best_eval:
                    best_eval = evaluation
                    best_move = move
            else:  # We just made a move for black
                if evaluation < best_eval:
                    best_eval = evaluation
                    best_move = move

            board.pop()

        return best_move


class MinimaxAI(ChessAI):
    #AI that uses the minimax algorithm

    def __init__(self, evaluator, depth=3):
        #Initialize with evaluator again and the wanted search depth
        super().__init__(evaluator)
        self.depth = depth

    def get_best_move(self, board):
        #Return the best move according to minimax
        self.reset_stats()
        best_move = None
        best_eval = float('-inf') if board.turn == chess.WHITE else float('inf')

        for move in board.legal_moves:
            board.push(move)

            # Evaluate this move using minimax
            if board.turn == chess.WHITE:  # We just made a move for black
                eval_score = self.minimax(board, self.depth - 1, False)
                if eval_score < best_eval:
                    best_eval = eval_score
                    best_move = move
            else:  # move made for white
                eval_score = self.minimax(board, self.depth - 1, True)
                if eval_score > best_eval:
                    best_eval = eval_score
                    best_move = move

            board.pop()

        return best_move

    def minimax(self, board, depth, maximizing_player):
        #Minimax algorithm implementation
        self.nodes_evaluated += 1

        # the base case leaf node or terminal position
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board)

        if maximizing_player:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
            return min_eval


class AlphaBetaAI(ChessAI):
    """AI that uses the minimax algorithm with alpha-beta pruning"""

    def __init__(self, evaluator, depth=3):
        """Initialize with evaluator and search depth"""
        super().__init__(evaluator)
        self.depth = depth

    def get_best_move(self, board):
        """Return the best move according to alpha-beta pruning"""
        self.reset_stats()
        best_move = None
        alpha = float('-inf')
        beta = float('inf')

        if board.turn == chess.WHITE:
            best_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, self.depth - 1, alpha, beta, False)
                board.pop()

                if eval_score > best_eval:
                    best_eval = eval_score
                    best_move = move

                alpha = max(alpha, best_eval)
        else:
            best_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, self.depth - 1, alpha, beta, True)
                board.pop()

                if eval_score < best_eval:
                    best_eval = eval_score
                    best_move = move

                beta = min(beta, best_eval)

        return best_move

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player):
        """Alpha-beta pruning algorithm implementation"""
        self.nodes_evaluated += 1

        # Base case: leaf node or terminal position
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board)

        if maximizing_player:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval


class NegamaxAI(ChessAI):
    """AI that uses the negamax algorithm (a variant of minimax)"""

    def __init__(self, evaluator, depth=3):
        """Initialize with evaluator and search depth"""
        super().__init__(evaluator)
        self.depth = depth

    def get_best_move(self, board):
        """Return the best move according to negamax"""
        self.reset_stats()
        best_move = None
        best_eval = float('-inf')

        for move in board.legal_moves:
            board.push(move)
            eval_score = -self.negamax(board, self.depth - 1)
            board.pop()

            if eval_score > best_eval:
                best_eval = eval_score
                best_move = move

        return best_move

    def negamax(self, board, depth):
        """Negamax algorithm implementation"""
        self.nodes_evaluated += 1

        # Base case: leaf node or terminal position
        if depth == 0 or board.is_game_over():
            return self.evaluate_for_side(board)

        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval_score = -self.negamax(board, depth - 1)
            board.pop()
            max_eval = max(max_eval, eval_score)

        return max_eval

    def evaluate_for_side(self, board):
        """Evaluate the position from the perspective of the side to move"""
        eval_score = self.evaluator.evaluate(board)
        return eval_score if board.turn == chess.WHITE else -eval_score


class QuiescenceSearchAI(AlphaBetaAI):
    """AI that uses alpha-beta pruning with quiescence search to handle the horizon effect"""

    def __init__(self, evaluator, depth=3, quiescence_depth=3):
        """Initialize with evaluator, main search depth, and quiescence depth"""
        super().__init__(evaluator, depth)
        self.quiescence_depth = quiescence_depth

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player):
        """Alpha-beta pruning with quiescence search"""
        self.nodes_evaluated += 1

        # If at leaf node, perform quiescence search
        if depth == 0:
            return self.quiescence(board, alpha, beta, maximizing_player, self.quiescence_depth)

        # Terminal position
        if board.is_game_over():
            return self.evaluator.evaluate(board)

        if maximizing_player:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval

    def quiescence(self, board, alpha, beta, maximizing_player, depth):
        """Quiescence search to handle the horizon effect"""
        self.nodes_evaluated += 1

        # Base evaluation
        stand_pat = self.evaluator.evaluate(board)

        # Return immediately if maximum depth reached or game over
        if depth == 0 or board.is_game_over():
            return stand_pat

        if maximizing_player:
            max_eval = stand_pat
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)

            # Only consider captures for quiescence
            for move in self.get_capture_moves(board):
                board.push(move)
                eval_score = self.quiescence(board, alpha, beta, False, depth - 1)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = stand_pat
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)

            # Only consider captures for quiescence
            for move in self.get_capture_moves(board):
                board.push(move)
                eval_score = self.quiescence(board, alpha, beta, True, depth - 1)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_capture_moves(self, board):
        """Get all capture moves from the current position"""
        captures = []
        for move in board.legal_moves:
            if board.is_capture(move):
                captures.append(move)
        return captures


class IterativeDeepeningAI(AlphaBetaAI):
    """AI that uses iterative deepening with a time limit"""

    def __init__(self, evaluator, time_limit=2.0):
        """Initialize with evaluator and time limit in seconds"""
        super().__init__(evaluator, 1)  # Start with depth 1
        self.time_limit = time_limit

    def get_best_move(self, board):
        """Return the best move using iterative deepening"""
        self.reset_stats()
        start_time = time.time()
        depth = 1
        best_move = None

        # Start with a simple move in case we run out of time
        legal_moves = list(board.legal_moves)
        if legal_moves:
            best_move = legal_moves[0]

        # Iterative deepening loop
        while time.time() - start_time < self.time_limit:
            try:
                # Set the current search depth
                self.depth = depth

                # Run alpha-beta at the current depth
                move = super().get_best_move(board)
                if move:
                    best_move = move

                # Increase depth for next iteration
                depth += 1

                # If we've searched very deeply or found a forced mate, we can stop
                if depth > 10:
                    break

            except Exception as e:
                print(f"Error in iterative deepening at depth {depth}: {e}")
                break

        print(f"Iterative deepening reached depth {depth-1} in {time.time() - start_time:.2f} seconds")
        return best_move


class AdvancedModeAI(ChessAI):
    """
    - Alpha-beta pruning
    - Quiescence search
    - Move ordering
    - Transposition table
    - Killer move heuristic
    - Iterative deepening
    """

    def __init__(self, evaluator, depth=4):
        #Initialize with evaluator and search depth
        super().__init__(evaluator)
        self.depth = depth
        self.transposition_table = {}
        self.killer_moves = [[None for _ in range(20)] for _ in range(2)]  # Store 2 killer moves per depth

    def get_best_move(self, board):
        #Iterative-deepened alpha-beta + quiescence + transposition +
        #killer moves, with correct root‐side comparisons.

        self.reset_stats()
        # clear tables at new root
        self.transposition_table.clear()
        self.killer_moves = [[None for _ in range(20)] for _ in range(2)]

        best_move = None
        root_turn = board.turn  # ← remember who’s to move at the root

        # iterative deepening from 1 to self.depth
        for current_depth in range(1, self.depth + 1):
            alpha = float('-inf')
            beta = float('inf')
            ordered_moves = self.order_moves(board, None, 0)

            # track best eval at this depth based on root_turn
            if root_turn == chess.WHITE:
                best_eval = float('-inf')
            else:
                best_eval = float('inf')

            for move in ordered_moves:
                board.push(move)
                # now call alpha_beta exactly as before
                eval_score = self.alpha_beta(
                    board,
                    current_depth - 1,
                    alpha,
                    beta,
                    maximizing_player=(not root_turn),  # next ply is opposite side
                    ply=0
                )
                board.pop()

                # compare *always* from root_turn’s POV:
                if root_turn == chess.WHITE:
                    if eval_score > best_eval:
                        best_eval, best_move = eval_score, move
                        alpha = max(alpha, best_eval)
                else:
                    if eval_score < best_eval:
                        best_eval, best_move = eval_score, move
                        beta = min(beta, best_eval)

            # end for each move
        # end iterative‐deepening

        return best_move

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player, ply):
        #Alpha-beta pruning with advanced techniques
        self.nodes_evaluated += 1

        # Check for repetition or fifty-move rule
        if board.is_repetition(2) or board.is_fifty_moves():
            return 0.0  # Draw

        # Check transposition table
        board_hash = self.get_board_hash(board)
        if board_hash in self.transposition_table and self.transposition_table[board_hash]['depth'] >= depth:
            return self.transposition_table[board_hash]['score']

        # If at leaf node, perform quiescence search
        if depth == 0:
            return self.quiescence(board, alpha, beta, maximizing_player, 5)
        # Terminal position
        if board.is_game_over():
            if board.is_checkmate():
                # Return a score based on how quickly checkmate was found
                return -10000 + ply if maximizing_player else 10000 - ply
            return 0.0  # Draw

        # Get ordered moves
        ordered_moves = self.order_moves(board, self.killer_moves[0][ply], ply)

        if maximizing_player:
            max_eval = float('-inf')
            for move in ordered_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, False, ply + 1)
                board.pop()

                if eval_score > max_eval:
                    max_eval = eval_score

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    # Store killer move
                    if not board.is_capture(move):
                        self.killer_moves[1][ply] = self.killer_moves[0][ply]
                        self.killer_moves[0][ply] = move
                    break  # Beta cutoff

            # Store in transposition table
            self.transposition_table[board_hash] = {'score': max_eval, 'depth': depth}
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, True, ply + 1)
                board.pop()

                if eval_score < min_eval:
                    min_eval = eval_score

                beta = min(beta, eval_score)
                if beta <= alpha:
                    # Store killer move
                    if not board.is_capture(move):
                        self.killer_moves[1][ply] = self.killer_moves[0][ply]
                        self.killer_moves[0][ply] = move
                    break  # Alpha cutoff

            # Store in transposition table
            self.transposition_table[board_hash] = {'score': min_eval, 'depth': depth}
            return min_eval

    def quiescence(self, board, alpha, beta, maximizing_player, depth):
        #Quiescence search to handle the horizon effect
        self.nodes_evaluated += 1

        # Base evaluation
        stand_pat = self.evaluator.evaluate(board)

        # Return immediately if maximum depth reached or game over
        if depth == 0 or board.is_game_over():
            return stand_pat

        if maximizing_player:
            max_eval = stand_pat
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)

            # Only consider captures for quiescence
            for move in self.get_capture_moves(board):
                board.push(move)
                eval_score = self.quiescence(board, alpha, beta, False, depth - 1)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = stand_pat
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)

            # Only consider captures for quiescence
            for move in self.get_capture_moves(board):
                board.push(move)
                eval_score = self.quiescence(board, alpha, beta, True, depth - 1)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_capture_moves(self, board):
        #Get all capture moves from the current position
        captures = []
        for move in board.legal_moves:
            if board.is_capture(move):
                captures.append(move)
        return captures

    def order_moves(self, board, killer_move, ply):
        """Order moves for more efficient pruning, with endgame-aware promotion weighting."""
        # 0) Compute an endgame multiplier based on how few non-pawn pieces remain
        non_king_non_pawn = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type not in (chess.KING, chess.PAWN):
                non_king_non_pawn += 1
        # As pieces drop off, multiplier goes from 1.0 up to ~2.0
        endgame_factor = max(0.0, (10 - non_king_non_pawn) / 10.0)
        multiplier = 1.0 + endgame_factor

        moves = list(board.legal_moves)
        scored_moves = []

        for move in moves:
            score = 0

            # 1) MVV-LVA: prioritize captures
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                aggressor = board.piece_at(move.from_square)
                if victim and aggressor:
                    v_val = self.get_piece_value(victim.piece_type)
                    a_val = self.get_piece_value(aggressor.piece_type)
                    score = 10 * v_val - a_val

            # 2) Promotions: boosted by multiplier, but penalize unsafe ones
            if move.promotion:
                base_promo = 1200
                promo_score = int(base_promo * multiplier)
                score += promo_score
                board.push(move)
                if board.is_attacked_by(not board.turn, move.to_square):
                    score -= 300
                board.pop()

            # 3) Pawn pushes one step from queening: also boosted in endgame
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                target_rank = chess.square_rank(move.to_square)
                if (piece.color == chess.WHITE and target_rank == 6) or \
                        (piece.color == chess.BLACK and target_rank == 1):
                    base_push = 200
                    push_score = int(base_push * multiplier)
                    score += push_score

            # 4) Delivering checks
            board.push(move)
            if board.is_check():
                score += 50
            board.pop()

            # 5) Killer-move heuristic
            if killer_move and move == killer_move:
                score += 30

            # 6) Pawn center-control (opening bonus)
            if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.PAWN:
                if move.to_square in [27, 28, 35, 36]:  # e4, d4, e5, d5
                    score += 10

            scored_moves.append((move, score))

        # Sort descending by score and return moves
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in scored_moves]

    def get_piece_value(self, piece_type):
        """Get the value of a piece type"""
        if piece_type == chess.PAWN:
            return 1
        elif piece_type == chess.KNIGHT:
            return 3
        elif piece_type == chess.BISHOP:
            return 3
        elif piece_type == chess.ROOK:
            return 5
        elif piece_type == chess.QUEEN:
            return 9
        elif piece_type == chess.KING:
            return 100
        return 0

    def get_board_hash(self, board):
        """Get a hash of the current board position"""
        return board.fen()
