

import chess
import time
import threading

import pygame

from chess_gui import ChessGUI
from chess_ai import (
    RandomAI, GreedyAI, MinimaxAI, AlphaBetaAI,
    NegamaxAI, QuiescenceSearchAI, IterativeDeepeningAI, AdvancedModeAI
)
from evaluation import (
    MaterialEvaluator, PositionalEvaluator, 
    MobilityEvaluator, KingSafetyEvaluator, CompositeEvaluator
)

class ChessGame:


    def __init__(self):


        # this is to initiate the board variable with all the legal moves for pieces
        self.board = chess.Board()


        self.material_evaluator = MaterialEvaluator()
        self.positional_evaluator = PositionalEvaluator()
        self.mobility_evaluator = MobilityEvaluator()
        self.king_safety_evaluator = KingSafetyEvaluator()

        # Create  evaluator with weights
        self.evaluator = CompositeEvaluator([
            (self.material_evaluator, 1.0),
            (self.positional_evaluator, 0.3),
            (self.mobility_evaluator, 0.2),
            (self.king_safety_evaluator, 0.5)
        ])

        # Initialize the AI algorithms
        self.ai_algorithms = {
            "Random": RandomAI(),
            "Greedy": GreedyAI(self.evaluator),
            "Minimax (Depth 2)": MinimaxAI(self.evaluator, 2),
            "Minimax (Depth 3)": MinimaxAI(self.evaluator, 3),
            "Alpha-Beta (Depth 3)": AlphaBetaAI(self.evaluator, 3),
            "Alpha-Beta (Depth 4)": AlphaBetaAI(self.evaluator, 4),
            "Negamax (Depth 3)": NegamaxAI(self.evaluator, 3),
            "Negamax (Depth 4)": NegamaxAI(self.evaluator, 4),
            "Quiescence (Depth 3)": QuiescenceSearchAI(self.evaluator, 3, 5),
            "Iterative Deepening (2s)": IterativeDeepeningAI(self.evaluator, 2.0),
            "Advanced Mode AI (4)": AdvancedModeAI(self.evaluator, 4),
            "Advanced Mode AI (5)": AdvancedModeAI(self.evaluator, 5),
            "Advanced Mode AI (6)": AdvancedModeAI(self.evaluator, 6)
        }
        self.current_ai = self.ai_algorithms["Alpha-Beta (Depth 3)"]
        self.second_ai = self.ai_algorithms["Alpha-Beta (Depth 3)"]

        # Game state
        self.player_color = chess.WHITE
        self.ai_thinking = False
        self.game_over = False
        self.move_history = []
        self.position_evaluations = []
        self.ai_vs_ai_mode = False
        self.ai_vs_ai_running = False
        self.ai_vs_ai_delay = 0.1

        # AI depth settings
        self.depth_options = [1, 2, 3, 4, 5]
        self.white_ai_depth = 3
        self.black_ai_depth = 3
        self.show_thinking = False
        self.engines = {chess.WHITE: None, chess.BLACK: None}
        self.ai_vs_ai_thread = None

        # Time tracking so that game doesn't start until a move is played

        self.game_start_time = None
        self.white_thinking_time = 0.0
        self.black_thinking_time = 0.0
        self.last_move_time = 0.0
        self.move_start_time = None

        # Initialize GUI after setting up game components
        self.gui = ChessGUI(self)



    def set_engine_for_colour(self, colour: chess.Color, engine):

        self.engines[colour] = engine

        both_engines = self.engines[chess.WHITE] and self.engines[chess.BLACK]

        if both_engines and not self.ai_vs_ai_running:
            self.start_ai_vs_ai()
        elif not both_engines and self.ai_vs_ai_running:
            self.stop_ai_vs_ai()

        # If it's that colour's move right now and we've just switched on an engine
        if self.board.turn == colour and engine and not self.ai_vs_ai_running:
            # Flag thinking so the banner shows immediately
            self.ai_thinking = True
            # Kick off the AI on a daemon thread
            threading.Thread(
                target=self._background_ai_move,
                args=(engine,),
                daemon=True
            ).start()

    def _ai_for_turn(self):

        if self.ai_vs_ai_mode:
            return self.current_ai if self.board.turn == chess.WHITE else self.second_ai

        # Any other mode: look up the entry that was set via the picker
        return self.engines.get(self.board.turn)


    def start_game(self):
        #Start the main game loop
        self.gui.main_loop()

        #chess_game.py

    def new_game(self, player_color=chess.WHITE, ai_vs_ai=False):


        self.stop_ai_vs_ai()

        # Reset state
        self.board = chess.Board()
        self.player_color = player_color
        self.ai_thinking = False
        self.game_over = False
        self.move_history = []
        self.position_evaluations = []
        self.ai_vs_ai_mode = ai_vs_ai


        # Reset timers do not start until first move

        self.game_start_time = None
        self.move_start_time = None
        self.white_thinking_time = 0.0
        self.black_thinking_time = 0.0
        self.last_move_time = 0.0

        # Reset GUI popup/timer-freeze state
        self.gui.show_game_over_popup = True
        self.gui.game_end_time = None

        # If the side to move is an engine, schedule its first move asynchronously
        first_engine = self._ai_for_turn()
        if first_engine is not None:
            self.ai_thinking = True
            threading.Thread(
                target=self._background_ai_move,
                args=(first_engine,),
                daemon=True
            ).start()

    def make_move(self, move: chess.Move) -> bool:
        if move not in self.board.legal_moves:
            return False

        now = time.time()

        # Start the total game clock on the first move
        if self.game_start_time is None:
            self.game_start_time = now

        # Record thinking time since last move
        if self.move_start_time is not None:
            elapsed = now - self.move_start_time
            # previous mover is the side that's about to move right now
            prev = self.board.turn
            if prev == chess.WHITE:
                self.white_thinking_time += elapsed
            else:
                self.black_thinking_time += elapsed
            self.last_move_time = elapsed

        # Determine which sound to play
        capture = self.board.is_capture(move)
        castle = self.board.is_castling(move)
        promotion = bool(move.promotion)

        # Push the move onto the board
        san = self.board.san(move)
        self.board.push(move)
        self.move_history.append((move, san))
        self.position_evaluations.append(self.evaluator.evaluate(self.board))
        self.game_over = bool(self.check_game_state())

        # Play the appropriate sound effect
        if capture:
            self.gui.play_sound('capture')
        elif castle:
            self.gui.play_sound('castle')
        elif promotion:
            self.gui.play_sound('promote')
        else:
            self.gui.play_sound('move')

        # Additional sounds for check and game end
        if self.board.is_check():
            self.gui.play_sound('check')
        if self.game_over:
            self.gui.play_sound('game_end')

        # Redraw & flip immediately so the move appears
        self.gui.draw_board()
        pygame.display.flip()

        # Schedule the next AI move if needed
        if not self.game_over and not self.ai_vs_ai_running:
            ai = self._ai_for_turn()
            if ai is not None:
                self.ai_thinking = True
                threading.Thread(
                    target=self._background_ai_move,
                    args=(ai,),
                    daemon=True
                ).start()

        # Mark the start of the next thinking interval
        self.move_start_time = now
        return True

    # Wrapper to call make_ai_move in a background thread.
    # Resets ai_thinking when done.
    def _background_ai_move(self, ai_engine):
        try:
            self.make_ai_move(ai_engine)
        finally:
            self.ai_thinking = False

    def make_ai_move(self, ai) -> None:
        #Ask `ai` for a move and execute it, no-op if it returns None
        # Show thinking banner right away
        self.ai_thinking = True
        self.gui.draw_board()

        # find the move this takes some time when calling big algos
        ai_move = ai.get_best_move(self.board.copy())

        # Done thinking
        self.ai_thinking = False

        # Execute the best move found using make_move
        if ai_move and ai_move in self.board.legal_moves:
            self.make_move(ai_move)

    def start_ai_vs_ai(self) -> None:

        if self.ai_vs_ai_running:
            return
        self.ai_vs_ai_running = True
        self.ai_vs_ai_thread = threading.Thread(target=self.ai_vs_ai_loop,
                                                daemon=True)
        self.ai_vs_ai_thread.start()

    def stop_ai_vs_ai(self) -> None:
        self.ai_vs_ai_running = False
        if self.ai_vs_ai_thread and self.ai_vs_ai_thread.is_alive():
            self.ai_vs_ai_thread.join(0.5)

    def ai_vs_ai_loop(self) -> None:
        while self.ai_vs_ai_running and not self.game_over:
            engine = self._ai_for_turn()  # engine for the *current* side
            if engine:
                self.make_ai_move(engine)  # makes one ply, returns quickly
            time.sleep(self.ai_vs_ai_delay)  # small pause so the GUI can redraw
    
    def set_ai_delay(self, delay):
        #Set delay between AI moves in AI vs AI mode so i can see moves unfold
        self.ai_vs_ai_delay = max(1.0, min(5.0, delay))  # Clamp between 0.1 and 5 seconds
    
    def undo_move(self):
        # Undo the last move(s) made and remove it from the board
        # Stop AI vs AI if running
        if self.ai_vs_ai_running:
            self.stop_ai_vs_ai()
            
        if len(self.move_history) > 0:
            # Undo player's move
            self.board.pop()
            self.move_history.pop()
            
            # If we also need to undo AI's move
            if not self.ai_vs_ai_mode and len(self.move_history) > 0 and self.board.turn != self.player_color:
                self.board.pop()
                self.move_history.pop()
            
            # Update evaluations
            if len(self.position_evaluations) > 0:
                self.position_evaluations.pop()
            if not self.ai_vs_ai_mode and len(self.position_evaluations) > 0 and self.board.turn != self.player_color:
                self.position_evaluations.pop()
                
            self.game_over = False
    
    def set_ai_algorithm(self, algorithm_name, second_ai=False):

        if algorithm_name in self.ai_algorithms:
            if second_ai:
                self.second_ai = self.ai_algorithms[algorithm_name]
            else:
                self.current_ai = self.ai_algorithms[algorithm_name]
    
    def check_game_state(self):
        #Check if the game is over
        if self.board.is_checkmate():
            self.game_over = True
            return "checkmate"
        elif self.board.is_stalemate():
            self.game_over = True
            return "stalemate"
        elif self.board.is_insufficient_material():
            self.game_over = True
            return "insufficient material"
        elif self.board.is_fifty_moves():
            self.game_over = True
            return "fifty-move rule"
        elif self.board.is_repetition():
            self.game_over = True
            return "threefold repetition"
        return None

    def set_ai_depth(self, depth, for_white=True):
        #Set the search depth for an AI
        if depth in self.depth_options:
            if for_white:
                self.white_ai_depth = depth
                # Update depth for depth-based algos
                for name, ai in self.ai_algorithms.items():
                    if "Depth" in name and ai == self.current_ai:
                        if isinstance(ai, MinimaxAI):
                            self.current_ai = MinimaxAI(self.evaluator, depth)
                        elif isinstance(ai, AlphaBetaAI):
                            self.current_ai = AlphaBetaAI(self.evaluator, depth)
                        elif isinstance(ai, NegamaxAI):
                            self.current_ai = NegamaxAI(self.evaluator, depth)
                        elif isinstance(ai, QuiescenceSearchAI):
                            self.current_ai = QuiescenceSearchAI(self.evaluator, depth, 3)
                        elif isinstance(ai, AdvancedModeAI):
                            self.current_ai = AdvancedModeAI(self.evaluator, depth)
            else:
                self.black_ai_depth = depth
                # Update depth for depth-based algos
                for name, ai in self.ai_algorithms.items():
                    if "Depth" in name and ai == self.second_ai:
                        if isinstance(ai, MinimaxAI):
                            self.second_ai = MinimaxAI(self.evaluator, depth)
                        elif isinstance(ai, AlphaBetaAI):
                            self.second_ai = AlphaBetaAI(self.evaluator, depth)
                        elif isinstance(ai, NegamaxAI):
                            self.second_ai = NegamaxAI(self.evaluator, depth)
                        elif isinstance(ai, QuiescenceSearchAI):
                            self.second_ai = QuiescenceSearchAI(self.evaluator, depth, 3)
                        elif isinstance(ai, AdvancedModeAI):
                            self.second_ai = AdvancedModeAI(self.evaluator, depth)
