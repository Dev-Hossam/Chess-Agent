

import pygame
import chess
import os
import math
import random
import time

class ChessGUI:

    
    def __init__(self, game):
        #Initialize the GUI with the game controller
        self.game = game
        
        # Set up display
        self.width, self.height = 1000, 700
        self.board_size = min(self.height, 600)
        self.square_size = self.board_size // 8
        self.ai_target_colour = chess.WHITE   # colour we’re editing in the picker

        # Create the window
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("LoveChess")
        
        # Load chess piece images
        self.pieces = {}
        self.load_pieces()
        
        # Initialize sound effects, going to leave it empty ofr now
        pygame.mixer.init()
        self.sounds = {
            'move': pygame.mixer.Sound('assets/sounds/move.wav') if os.path.exists('assets/sounds/move.wav') else None,
            'capture': pygame.mixer.Sound('assets/sounds/capture.wav') if os.path.exists('assets/sounds/capture.wav') else None,
            'check': pygame.mixer.Sound('assets/sounds/check.wav') if os.path.exists('assets/sounds/check.wav') else None,
            'castle': pygame.mixer.Sound('assets/sounds/castle.wav') if os.path.exists('assets/sounds/castle.wav') else None,
            'promote': pygame.mixer.Sound('assets/sounds/promote.wav') if os.path.exists('assets/sounds/promote.wav') else None,
            'game_end': pygame.mixer.Sound('assets/sounds/game_end.wav') if os.path.exists('assets/sounds/game_end.wav') else None
        }

        # Background music attributes
        # Path to the music file (None by default)
        self.background_music = None
        # Default volume (0.0 – 1.0) so it’s in the background
        self.background_music_volume = 0.2
        
        # Colors
        self.light_square = (240, 217, 181)
        self.dark_square = (181, 136, 99)
        self.highlight_color = (124, 252, 0, 128)
        self.move_indicator = (100, 200, 255, 150)
        self.check_color = (255, 0, 0, 150)
        self.hint_color = (0, 191, 255, 180)
        
        # UI state
        self.selected_square = None
        self.legal_moves = []
        self.current_tab = "stats"  # "moves", "analysis", "stats"
        self.dragging = False
        self.drag_piece = None
        self.drag_pos = (0, 0)
        self.hint_move = None
        self.show_hint = False
        self.show_ai_menu = False
        self.selecting_first_ai = True

        self.show_game_over_popup = True
        self.game_end_time = None
        # Fonts
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 16)
        self.large_font = pygame.font.SysFont("Arial", 24)
        self.bold_font = pygame.font.SysFont("Arial", 16, bold=True)

        self.game_start_time = None  # will set on first move
        self.move_start_time = None  # last‐move timestamp
        self.white_thinking_time = 0.0
        self.black_thinking_time = 0.0
        self.last_move_time = 0.0

        self.show_promotion_menu = False
        self.pending_promotion_move = None  # will store (from_sq, to_sq)
        self.promotion_rects = {}  # maps chess.PieceType to pygame.Rect


    def load_background_music(self, music_path: str, volume: float = 0.2) -> None:
        """
        Load and play background music in a continuous loop.
        Volume is between 0.0 (silent) and 1.0 (full).
        """
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                self.background_music = music_path
                self.background_music_volume = volume
            except Exception as e:
                print(f"Error loading background music '{music_path}': {e}")
        else:
            print(f"Background music file '{music_path}' not found.")

    def draw_promotion_menu(self):

        # semi-transparent full-screen overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # menu dimensions
        menu_w, menu_h = 240, 60
        mx = (self.width - menu_w) // 2
        my = (self.height - menu_h) // 2

        # background box
        pygame.draw.rect(self.screen, (240, 240, 240), (mx, my, menu_w, menu_h))
        pygame.draw.rect(self.screen, (0, 0, 0), (mx, my, menu_w, menu_h), 2)

        # determine pawn color from pending move
        from_sq, to_sq = self.pending_promotion_move
        pawn = self.game.board.piece_at(from_sq)
        is_white = pawn.color == chess.WHITE

        # order and positions for the four choices
        choices = [
            (chess.QUEEN, 'Q'),
            (chess.ROOK, 'R'),
            (chess.BISHOP, 'B'),
            (chess.KNIGHT, 'N'),
        ]
        icon_size = fifty = menu_h - 10
        gap = (menu_w - 4 * icon_size) // 5
        x = mx + gap

        self.promotion_rects.clear()
        for piece_type, sym in choices:
            # pick correct key for self.pieces (uppercase for white, lowercase for black)
            key = sym if is_white else sym.lower()
            img = pygame.transform.scale(self.pieces[key], (icon_size, icon_size))
            rect = pygame.Rect(x, my + 5, icon_size, icon_size)
            self.screen.blit(img, rect.topleft)
            self.promotion_rects[piece_type] = rect
            x += icon_size + gap

    def load_pieces(self):
        """Load chess piece images from assets directory"""
        piece_mapping = {
            'P': 'wp', 'N': 'wN', 'B': 'wB', 'R': 'wR', 'Q': 'wQ', 'K': 'wK',
            'p': 'bp', 'n': 'bN', 'b': 'bB', 'r': 'bR', 'q': 'bQ', 'k': 'bK'
        }
        
        for piece_char, filename in piece_mapping.items():
            try:
                img_path = os.path.join('assets', 'pieces', f"{filename}.png")
                img = pygame.image.load(img_path)
                img = pygame.transform.scale(img, (self.square_size, self.square_size))
                self.pieces[piece_char] = img
            except pygame.error as e:
                print(f"Error loading piece image {filename}: {e}")
                # Create a fallback colored square with text
                fallback = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                fallback.fill((200, 200, 200, 200))
                text = self.font.render(piece_char, True, (0, 0, 0))
                fallback.blit(text, (self.square_size//2 - text.get_width()//2, 
                                    self.square_size//2 - text.get_height()//2))
                self.pieces[piece_char] = fallback
    
    def resize(self, width, height):
        """Handle window resize events"""
        self.width, self.height = width, height
        self.board_size = min(self.height - 50, 600)
        self.square_size = self.board_size // 8
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        # Reload pieces with new size
        self.load_pieces()
    
    def main_loop(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_press(event)
            
            # Draw the game
            self.draw_board()
            
            # Update display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)

    def draw_clocks(self):
        """Draw game timing clocks at the top-left corner."""
        x, y = 20, 20

        # 1) If the game just ended, stamp the end time and
        #    flush any remaining interval into the next side’s total.
        if self.game.game_over:
            if self.game_end_time is None:
                # mark the moment we first detect game-over
                self.game_end_time = time.time()
                # compute leftover since last move finished (if any)
                if self.game.move_start_time is not None:
                    leftover = self.game_end_time - self.game.move_start_time
                    next_side = self.game.board.turn
                    if next_side == chess.WHITE:
                        self.game.white_thinking_time += leftover
                    else:
                        self.game.black_thinking_time += leftover
            current_time = self.game_end_time
        else:
            current_time = time.time()

        # 2) Compute totals (guard against None before first move)
        if self.game.game_start_time is None:
            total_game = 0.0
        else:
            total_game = current_time - self.game.game_start_time

        white_think = self.game.white_thinking_time
        black_think = self.game.black_thinking_time
        last_move = self.game.last_move_time

        # 3) Helper to format MM:SS
        def fmt(sec):
            m = int(sec) // 60
            s = int(sec) % 60
            return f"{m:02d}:{s:02d}"

        # 4) Render lines
        for i, text in enumerate([
            f"Total Game Time:           {fmt(total_game)}",
            f"Total White Thinking Time: {fmt(white_think)}",
            f"Total Black Thinking Time: {fmt(black_think)}",
            f"Last Move Time:            {fmt(last_move)}",
        ]):
            surf = self.font.render(text, True, (0, 0, 0))
            line_h = self.font.get_linesize() + 2
            self.screen.blit(surf, (x, y + i * line_h))

    def draw_board(self):
        """Draw the chess board and pieces"""
        # Clear the screen
        if self.game.game_over and self.game_end_time is None:
            self.game_end_time = time.time()
        self.screen.fill((240, 240, 240))

        self.draw_clocks()
        # Calculate board position (centered)
        board_x = (self.width - self.board_size) // 2
        board_y = 50

        # Draw turn indicator
        self.draw_turn_indicator(board_x, board_y - 30)

        # Draw board squares, highlights and move‐indicators
        for row in range(8):
            for col in range(8):
                # Screen coords
                x = board_x + col * self.square_size
                if self.game.player_color == chess.WHITE:
                    y = board_y + (7 - row) * self.square_size
                else:
                    y = board_y + row * self.square_size

                # Square color
                color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                pygame.draw.rect(self.screen, color, (x, y, self.square_size, self.square_size))

                # Board‐index mapping corrected:
                if self.game.player_color == chess.WHITE:
                    square_idx = row * 8 + col
                else:
                    square_idx = (7 - row) * 8 + col

                # 1) highlight selected square
                if self.selected_square is not None and square_idx == self.selected_square:
                    hl = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    hl.fill(self.highlight_color)
                    self.screen.blit(hl, (x, y))

                # 2) highlight legal moves
                for move in self.legal_moves:
                    if move.from_square == self.selected_square:
                        to_sq = move.to_square
                        to_col = to_sq % 8
                        to_row = to_sq // 8
                        if self.game.player_color == chess.WHITE:
                            vy = board_y + (7 - to_row) * self.square_size
                        else:
                            vy = board_y + to_row * self.square_size
                        vx = board_x + to_col * self.square_size
                        indic = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                        indic.fill(self.move_indicator)
                        self.screen.blit(indic, (vx, vy))

                # 3) highlight hint move, if active
                if self.show_hint and self.hint_move:
                    for sq in (self.hint_move.from_square, self.hint_move.to_square):
                        c = sq % 8
                        r = sq // 8
                        if self.game.player_color == chess.WHITE:
                            hy = board_y + (7 - r) * self.square_size
                        else:
                            hy = board_y + r * self.square_size
                        hx = board_x + c * self.square_size
                        hint_surf = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                        hint_surf.fill(self.hint_color)
                        self.screen.blit(hint_surf, (hx, hy))

                # 4) highlight king in check
                if self.game.board.is_check():
                    ks = self.game.board.king(self.game.board.turn)
                    if square_idx == ks:
                        chk = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                        chk.fill(self.check_color)
                        self.screen.blit(chk, (x, y))

        # Draw file & rank labels
        for i in range(8):
            # Files (a–h)
            f_label = self.font.render(chess.FILE_NAMES[i], True, (0, 0, 0))
            self.screen.blit(f_label,
                             (board_x + i * self.square_size + self.square_size // 2 - f_label.get_width() // 2,
                              board_y + self.board_size + 5))
            # Ranks (1–8)
            rank = i if self.game.player_color == chess.BLACK else 7 - i
            r_label = self.font.render(str(rank + 1), True, (0, 0, 0))
            self.screen.blit(r_label,
                             (board_x - 15,
                              board_y + i * self.square_size + self.square_size // 2 - r_label.get_height() // 2))

        # Draw pieces (skip the one being dragged)
        for row in range(8):
            for col in range(8):
                if self.game.player_color == chess.WHITE:
                    square_idx = row * 8 + col
                else:
                    square_idx = (7 - row) * 8 + col
                piece = self.game.board.piece_at(square_idx)
                if piece and (not self.dragging or square_idx != self.selected_square):
                    px = board_x + col * self.square_size
                    if self.game.player_color == chess.WHITE:
                        py = board_y + (7 - row) * self.square_size
                    else:
                        py = board_y + row * self.square_size
                    self.screen.blit(self.pieces[piece.symbol()], (px, py))

        # Draw a dragged piece, if any
        if self.dragging and self.drag_piece:
            dx, dy = self.drag_pos
            dx -= self.square_size // 2
            dy -= self.square_size // 2
            self.screen.blit(self.pieces[self.drag_piece.symbol()], (dx, dy))

        # Draw all UI chrome
        self.draw_ui(board_x, board_y)

        # Draw game‐over overlay, if applicable (unless user closed it)
        if self.game.game_over and self.show_game_over_popup:
            self.draw_game_over_message()

        # Draw "AI thinking…" banner
        if self.game.ai_thinking and (not self.game.ai_vs_ai_mode or self.game.show_thinking):
            self.draw_thinking_message()

        # Draw AI picker, if open
        # … at the end of draw_board(), after all normal drawing …
        if self.show_promotion_menu:
            self.draw_promotion_menu()

        if self.show_ai_menu:
            self.draw_ai_selection_menu(board_x, board_y)



    def draw_turn_indicator(self, board_x, y):
        """
        A slim banner centered above the board telling the user
        whose move it is (human ↔ engine).
        """
        side_to_move = self.game.board.turn
        engine_playes = self.game._ai_for_turn() is not None

        text = "AI's Turn" if engine_playes else "Your Turn"
        colour = (128, 0, 0) if engine_playes else (0, 128, 0)

        # simple framed rectangle
        w, h = 200, 25
        x = board_x + (self.board_size - w) // 2
        pygame.draw.rect(self.screen, (240, 240, 240), (x, y, w, h))
        pygame.draw.rect(self.screen, colour, (x, y, w, h), 2)

        rendered = self.bold_font.render(text, True, colour)
        self.screen.blit(rendered, (x + (w - rendered.get_width()) // 2,
                                    y + (h - rendered.get_height()) // 2))

    def draw_ui(self, board_x, board_y):
        """Draw side tabs + panel under the board."""
        # ── tabs on the right ──────────────────────────────────────────────
        tab_width, tab_height = 100, 30
        tab_x = board_x + self.board_size + 20
        tab_y = board_y

        for i, (name, label) in enumerate([("moves", "Moves"),
                                           ("analysis", "Analysis"),
                                           ("stats", "Stats")]):
            rect = pygame.Rect(tab_x + i * tab_width, tab_y, tab_width, tab_height)
            colour = (200, 200, 200) if self.current_tab == name else (170, 170, 170)
            pygame.draw.rect(self.screen, colour, rect)
            txt = self.font.render(label, True, (0, 0, 0))
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                                   rect.centery - txt.get_height() // 2))

        # tab content box
        content_x, content_y = tab_x, tab_y + tab_height
        content_w, content_h = tab_width * 3, self.board_size - tab_height
        pygame.draw.rect(self.screen, (240, 240, 240), (content_x, content_y, content_w, content_h))
        pygame.draw.rect(self.screen, (200, 200, 200), (content_x, content_y, content_w, content_h), 1)

        if self.current_tab == "moves":
            self.draw_moves_tab(content_x, content_y, content_w, content_h)
        elif self.current_tab == "analysis":
            self.draw_analysis_tab(content_x, content_y, content_w, content_h)
        else:
            self.draw_stats_tab(content_x, content_y, content_w, content_h)

        # ── bottom control panel ───────────────────────────────────────────
        self.draw_bottom_controls(board_x, board_y)

    # ────────────────────────────────────────────────────────────────────────
    #  BOTTOM CONTROL PANEL  (4 rows under the board)
    # ────────────────────────────────────────────────────────────────────────
    def draw_bottom_controls(self, board_x: int, board_y: int) -> None:
        """
        Four-row control panel below the board.
        • Row 1: general buttons (New Game, Undo Move, Hint)
        • Row 2: “White: … / Black: …” – click to open picker
        • Row 3: depth +/- (only if that colour uses a depth-aware engine)
        • Row 4: “Show Thinking” toggle
        """
        self.control_rects = {}
        BW, BH, GAP = 100, 30, 10
        font = self.font

        # Row 1: New Game | Undo Move | Hint
        row0_x = board_x
        row0_y = board_y + self.board_size + 30
        for i, (label, key) in enumerate([
            ("New Game", "new_game"),
            ("Undo Move", "undo"),
            ("Hint", "hint"),
        ]):
            r = pygame.Rect(row0_x + i * (BW + GAP), row0_y, BW, BH)
            pygame.draw.rect(self.screen, (200, 200, 200), r)
            txt = font.render(label, True, (0, 0, 0))
            self.screen.blit(txt,
                             (r.centerx - txt.get_width() // 2,
                              r.centery - txt.get_height() // 2))
            self.control_rects[key] = r

        # Row 2: engine labels (White: … / Black: …)
        row1_y = row0_y + BH + GAP
        col_w = BW * 2
        pygame.draw.rect(self.screen, (240, 240, 240),
                         (row0_x, row1_y, col_w * 2, BH))

        def draw_engine_label(colour, x_off, key_hitbox):
            eng = self.game.engines[colour]
            name = type(eng).__name__ if eng else "Human"
            label = f"{'White' if colour == chess.WHITE else 'Black'}: {name}"
            txt = font.render(label, True, (0, 0, 0))
            # shrink if too wide
            while txt.get_width() > col_w - 6:
                txt = pygame.transform.scale(txt, (int(txt.get_width() * 0.8), txt.get_height()))
            self.screen.blit(txt, (row0_x + x_off + 3,
                                   row1_y + BH // 2 - txt.get_height() // 2))
            self.control_rects[key_hitbox] = pygame.Rect(row0_x + x_off,
                                                         row1_y, col_w, BH)

        draw_engine_label(chess.WHITE, 0, "white_ai")
        draw_engine_label(chess.BLACK, col_w, "black_ai")

        # Row 3: depth +/- for depth-based engines
        row2_y = row1_y + BH + GAP

        def depth_widgets(colour, depth, prefix, x_off):
            eng = self.game.engines[colour]
            if eng and hasattr(eng, "max_depth"):
                lab = font.render(f"{prefix.capitalize()} Depth: {depth}", True, (0, 0, 0))
                self.screen.blit(lab, (row0_x + x_off,
                                       row2_y + BH // 2 - lab.get_height() // 2))
                for sym, dx, key in [("-", 10, f"{prefix}_minus"),
                                     ("+", 50, f"{prefix}_plus")]:
                    r = pygame.Rect(row0_x + x_off + BW + dx, row2_y, 30, BH)
                    pygame.draw.rect(self.screen, (200, 200, 200), r)
                    self.screen.blit(font.render(sym, True, (0, 0, 0)),
                                     (r.centerx - 4, r.centery - 8))
                    self.control_rects[key] = r

        depth_widgets(chess.WHITE, self.game.white_ai_depth, "white_depth", 0)
        depth_widgets(chess.BLACK, self.game.black_ai_depth, "black_depth", 2 * BW)

        # Row 4: “Show Thinking” toggle
        row3_y = row2_y + BH + GAP
        togg = pygame.Rect(row0_x, row3_y, BW, BH)
        color = (150, 200, 250) if self.game.show_thinking else (200, 200, 200)
        pygame.draw.rect(self.screen, color, togg)
        txt = font.render("Show Thinking", True, (0, 0, 0))
        self.screen.blit(txt,
                         (togg.centerx - txt.get_width() // 2,
                          togg.centery - txt.get_height() // 2))
        self.control_rects["toggle_thinking"] = togg

        # ── row 4 ───────────────────────────────────────────────────────────────
        row3_y = row2_y + BH + GAP
        toggle = pygame.Rect(row0_x, row3_y, BW, BH)
        pygame.draw.rect(self.screen,
                         (150, 200, 250) if self.game.show_thinking else (200, 200, 200),
                         toggle)
        self.screen.blit(font.render("Show Thinking", True, (0, 0, 0)),
                         (toggle.centerx - font.size("Show Thinking")[0] // 2,
                          toggle.centery - font.size("Show Thinking")[1] // 2))
        self.control_rects["toggle_thinking"] = toggle

        def depth_widgets(colour, depth, prefix, x_off):
            eng = self.game.engines[colour]
            if eng and hasattr(eng, "max_depth"):
                lab = font.render(f"{prefix.capitalize()} Depth: {depth}",
                                  True, (0, 0, 0))
                self.screen.blit(lab, (row0_x + x_off,
                                  row2_y + BH // 2 - lab.get_height() // 2))
                for sym, dx, key in [("-", 10, f"{prefix}_minus"),
                                     ("+", 50, f"{prefix}_plus")]:
                    r = pygame.Rect(row0_x + x_off + BW + dx, row2_y, 30, BH)
                    pygame.draw.rect(self.screen, (200, 200, 200), r)
                    self.screen.blit(font.render(sym, True, (0, 0, 0)),
                                (r.centerx - 4, r.centery - 8))
                    self.control_rects[key] = r

        depth_widgets(chess.WHITE, self.game.white_ai_depth, "white_depth", 0)
        depth_widgets(chess.BLACK, self.game.black_ai_depth, "black_depth", 2 * BW)

        # ─ row 4 : show-thinking toggle ──────────────────────────────────
        row3_y = row2_y + BH + GAP
        toggle = pygame.Rect(row0_x, row3_y, BW, BH)
        pygame.draw.rect(self.screen,
                         (150, 200, 250) if self.game.show_thinking else (200, 200, 200),
                         toggle)
        self.screen.blit(font.render("Show Thinking", True, (0, 0, 0)),
                    (toggle.centerx - font.size("Show Thinking")[0] // 2,
                     toggle.centery - font.size("Show Thinking")[1] // 2))
        self.control_rects["toggle_thinking"] = toggle

        def depth_widgets(colour, depth, prefix, x_off):
            eng = self.game.engines[colour]
            if eng and hasattr(eng, "max_depth"):
                lab = font.render(f"{prefix.capitalize()} Depth: {depth}", True, (0, 0, 0))
                self.screen.blit(lab, (row0_x + x_off,
                                       row2_y + BH // 2 - lab.get_height() // 2))
                for sym, dx, key in [("-", 10, f"{prefix}_minus"),
                                     ("+", 50, f"{prefix}_plus")]:
                    r = pygame.Rect(row0_x + x_off + BW + dx, row2_y, 30, BH)
                    pygame.draw.rect(self.screen, (200, 200, 200), r)
                    self.screen.blit(font.render(sym, True, (0, 0, 0)),
                                     (r.centerx - 4, r.centery - 8))
                    self.control_rects[key] = r

        depth_widgets(chess.WHITE, self.game.white_ai_depth, "white_depth", 0)
        depth_widgets(chess.BLACK, self.game.black_ai_depth, "black_depth", 2 * BW)

        # ── Row 4 : show-thinking toggle ─────────────────────────────────────
        row3_y = row2_y + BH + GAP
        toggle = pygame.Rect(row0_x, row3_y, BW, BH)
        pygame.draw.rect(self.screen,
                         (150, 200, 250) if self.game.show_thinking else (200, 200, 200),
                         toggle)
        self.screen.blit(font.render("Show Thinking", True, (0, 0, 0)),
                         (toggle.centerx - font.size("Show Thinking")[0] // 2,
                          toggle.centery - font.size("Show Thinking")[1] // 2))
        self.control_rects["toggle_thinking"] = toggle

        # helper


    def draw_moves_tab(self, x, y, width, height):
        """Draw the moves history tab"""
        # Draw move history
        move_y = y + 10
        move_x_white = x + 10
        move_x_black = x + width // 2
        
        # Title
        title_text = self.font.render("Move History", True, (0, 0, 0))
        self.screen.blit(title_text, (x + width//2 - title_text.get_width()//2, move_y))
        move_y += 30
        
        # Column headers
        white_header = self.font.render("White", True, (0, 0, 0))
        black_header = self.font.render("Black", True, (0, 0, 0))
        self.screen.blit(white_header, (move_x_white, move_y))
        self.screen.blit(black_header, (move_x_black, move_y))
        move_y += 25
        
        # Moves
        for i in range(0, len(self.game.move_history), 2):
            # Move number
            move_num = i // 2 + 1
            move_num_text = self.font.render(f"{move_num}.", True, (0, 0, 0))
            self.screen.blit(move_num_text, (move_x_white - 25, move_y))
            
            # White's move
            white_move, white_san = self.game.move_history[i]
            white_move_text = self.font.render(white_san, True, (0, 0, 0))
            self.screen.blit(white_move_text, (move_x_white, move_y))
            
            # Black's move (if exists)
            if i + 1 < len(self.game.move_history):
                black_move, black_san = self.game.move_history[i + 1]
                black_move_text = self.font.render(black_san, True, (0, 0, 0))
                self.screen.blit(black_move_text, (move_x_black, move_y))
            
            move_y += 20
            
            # Stop if we run out of space
            if move_y > y + height - 20:
                break
    
    def draw_analysis_tab(self, x, y, width, height):
        """Draw the position analysis tab"""
        # Title
        title_text = self.font.render("Position Analysis", True, (0, 0, 0))
        self.screen.blit(title_text, (x + width//2 - title_text.get_width()//2, y + 10))
        
        # Current evaluation
        eval_text = self.font.render(f"Evaluation: {self.game.evaluator.evaluate(self.game.board):.2f}", True, (0, 0, 0))
        self.screen.blit(eval_text, (x + 10, y + 40))
        
        # Material count
        material_text = self.font.render(f"Material: {self.game.material_evaluator.evaluate(self.game.board):.2f}", True, (0, 0, 0))
        self.screen.blit(material_text, (x + 10, y + 60))
        
        # Position quality
        position_text = self.font.render(f"Position: {self.game.positional_evaluator.evaluate(self.game.board):.2f}", True, (0, 0, 0))
        self.screen.blit(position_text, (x + 10, y + 80))
        
        # Mobility
        mobility_text = self.font.render(f"Mobility: {self.game.mobility_evaluator.evaluate(self.game.board):.2f}", True, (0, 0, 0))
        self.screen.blit(mobility_text, (x + 10, y + 100))
        
        # King safety
        king_safety_text = self.font.render(f"King Safety: {self.game.king_safety_evaluator.evaluate(self.game.board):.2f}", True, (0, 0, 0))
        self.screen.blit(king_safety_text, (x + 10, y + 120))
        
        # Draw evaluation graph if we have enough data
        if len(self.game.position_evaluations) > 1:
            graph_x = x + 10
            graph_y = y + 150
            graph_width = width - 20
            graph_height = 150
            
            # Draw graph background
            pygame.draw.rect(self.screen, (255, 255, 255), (graph_x, graph_y, graph_width, graph_height))
            pygame.draw.rect(self.screen, (0, 0, 0), (graph_x, graph_y, graph_width, graph_height), 1)
            
            # Draw center line (0.0 evaluation)
            center_y = graph_y + graph_height // 2
            pygame.draw.line(self.screen, (200, 200, 200), (graph_x, center_y), (graph_x + graph_width, center_y))
            
            # Draw evaluation line
            max_eval = max(abs(min(self.game.position_evaluations)), abs(max(self.game.position_evaluations)), 3.0)
            scale = (graph_height / 2) / max_eval
            
            for i in range(1, len(self.game.position_evaluations)):
                prev_eval = self.game.position_evaluations[i-1]
                curr_eval = self.game.position_evaluations[i]
                
                prev_x = graph_x + (i-1) * graph_width / (len(self.game.position_evaluations) - 1)
                curr_x = graph_x + i * graph_width / (len(self.game.position_evaluations) - 1)
                
                prev_y = center_y - prev_eval * scale
                curr_y = center_y - curr_eval * scale
                
                pygame.draw.line(self.screen, (0, 0, 255), (prev_x, prev_y), (curr_x, curr_y), 2)
    
    def draw_stats_tab(self, x, y, width, height):
        """Draw the game statistics tab"""
        # Title
        title_text = self.font.render("Game Statistics", True, (0, 0, 0))
        self.screen.blit(title_text, (x + width//2 - title_text.get_width()//2, y + 10))
        
        # Game info
        moves_text = self.font.render(f"Total Moves: {len(self.game.move_history)}", True, (0, 0, 0))
        self.screen.blit(moves_text, (x + 10, y + 40))
        
        # Calculate piece counts
        white_pieces = sum(1 for square in chess.SQUARES if self.game.board.piece_at(square) and self.game.board.piece_at(square).color == chess.WHITE)
        black_pieces = sum(1 for square in chess.SQUARES if self.game.board.piece_at(square) and self.game.board.piece_at(square).color == chess.BLACK)
        
        white_text = self.font.render(f"White Pieces: {white_pieces}", True, (0, 0, 0))
        self.screen.blit(white_text, (x + 10, y + 60))
        
        black_text = self.font.render(f"Black Pieces: {black_pieces}", True, (0, 0, 0))
        self.screen.blit(black_text, (x + 10, y + 80))
        
        # Game status
        status = self.game.check_game_state()
        if status:
            status_text = self.font.render(f"Game Status: {status.capitalize()}", True, (0, 0, 0))
        else:
            turn = "White" if self.game.board.turn == chess.WHITE else "Black"
            status_text = self.font.render(f"Game Status: {turn} to move", True, (0, 0, 0))
        self.screen.blit(status_text, (x + 10, y + 100))
        
        # Check status
        check_status = "In check" if self.game.board.is_check() else "Not in check"
        check_text = self.font.render(f"Check Status: {check_status}", True, (0, 0, 0))
        self.screen.blit(check_text, (x + 10, y + 120))
        
        # Castling rights
        castling = []
        if self.game.board.has_kingside_castling_rights(chess.WHITE):
            castling.append("White O-O")
        if self.game.board.has_queenside_castling_rights(chess.WHITE):
            castling.append("White O-O-O")
        if self.game.board.has_kingside_castling_rights(chess.BLACK):
            castling.append("Black O-O")
        if self.game.board.has_queenside_castling_rights(chess.BLACK):
            castling.append("Black O-O-O")
        
        castling_text = self.font.render(f"Castling Rights: {', '.join(castling) if castling else 'None'}", True, (0, 0, 0))
        self.screen.blit(castling_text, (x + 10, y + 140))
        
        # Legal moves count
        legal_moves_count = len(list(self.game.board.legal_moves))
        legal_moves_text = self.font.render(f"Legal Moves: {legal_moves_count}", True, (0, 0, 0))
        self.screen.blit(legal_moves_text, (x + 10, y + 160))
        
        # AI info if in AI vs AI mode
        if self.game.ai_vs_ai_mode:
            ai_text = self.font.render("AI vs AI Mode:", True, (0, 0, 128))
            self.screen.blit(ai_text, (x + 10, y + 180))
            
            white_ai = next((k for k, v in self.game.ai_algorithms.items() if v == self.game.current_ai), "Custom")
            black_ai = next((k for k, v in self.game.ai_algorithms.items() if v == self.game.second_ai), "Custom")
            
            white_ai_text = self.font.render(f"White AI: {white_ai}", True, (0, 0, 0))
            self.screen.blit(white_ai_text, (x + 20, y + 200))
            
            black_ai_text = self.font.render(f"Black AI: {black_ai}", True, (0, 0, 0))
            self.screen.blit(black_ai_text, (x + 20, y + 220))

    def draw_game_over_message(self):
        """Draw game over message"""
        status = self.game.check_game_state()
        if status:
            # Semi-transparent full-screen overlay
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            # Message box
            box_width, box_height = 300, 150
            box_x = (self.width - box_width) // 2
            box_y = (self.height - box_height) // 2

            pygame.draw.rect(self.screen, (240, 240, 240), (box_x, box_y, box_width, box_height))
            pygame.draw.rect(self.screen, (0, 0, 0), (box_x, box_y, box_width, box_height), 2)

            # Title
            title_text = self.large_font.render("Game Over", True, (0, 0, 0))
            self.screen.blit(title_text,
                             (box_x + box_width // 2 - title_text.get_width() // 2,
                              box_y + 20))

            # Result line
            if status == "checkmate":
                winner = "Black" if self.game.board.turn == chess.WHITE else "White"
                result_line = f"{winner} wins by checkmate!"
            else:
                result_line = f"Draw by {status}!"
            result_text = self.font.render(result_line, True, (0, 0, 0))
            self.screen.blit(result_text,
                             (box_x + box_width // 2 - result_text.get_width() // 2,
                              box_y + 60))

            # Buttons: New Game and Close
            button_width, button_height = 120, 30
            gap = 10
            total_width = button_width * 2 + gap
            start_x = box_x + (box_width - total_width) // 2
            button_y = box_y + 100

            # New Game button
            self.game_over_button_rect = pygame.Rect(start_x, button_y, button_width, button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), self.game_over_button_rect)
            btn_txt = self.font.render("New Game", True, (0, 0, 0))
            self.screen.blit(btn_txt,
                             (start_x + button_width // 2 - btn_txt.get_width() // 2,
                              button_y + button_height // 2 - btn_txt.get_height() // 2))

            # Close button
            close_x = start_x + button_width + gap
            self.game_over_close_button_rect = pygame.Rect(close_x, button_y, button_width, button_height)
            pygame.draw.rect(self.screen, (200, 200, 200), self.game_over_close_button_rect)
            close_txt = self.font.render("Close", True, (0, 0, 0))
            self.screen.blit(close_txt,
                             (close_x + button_width // 2 - close_txt.get_width() // 2,
                              button_y + button_height // 2 - close_txt.get_height() // 2))

    def draw_thinking_message(self):
        """Black banner at the bottom while an engine is searching."""
        overlay_h = 30
        surf = pygame.Surface((self.width, overlay_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 200))
        self.screen.blit(surf, (0, self.height - overlay_h))

        # Which engine is *actually* on move?
        engine = self.game._ai_for_turn()
        name = type(engine).__name__ if engine else "Engine"

        txt = self.font.render(f"{name} is thinking…", True, (255, 255, 255))
        self.screen.blit(txt,
                         (self.width // 2 - txt.get_width() // 2,
                          self.height - overlay_h // 2 - txt.get_height() // 2))

    def draw_ai_selection_menu(self, board_x, board_y):
        """Draw the AI selection menu"""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Draw menu box
        menu_width, menu_height = 300, 400
        menu_x = (self.width - menu_width) // 2
        menu_y = (self.height - menu_height) // 2
        
        pygame.draw.rect(self.screen, (240, 240, 240), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height), 2)
        
        # Title
        title = "Select White AI" if self.ai_target_colour == chess.WHITE else "Select Black AI"
        title_text = self.large_font.render(title, True, (0, 0, 0))
        self.screen.blit(title_text, (menu_x + menu_width//2 - title_text.get_width()//2, menu_y + 20))
        
        # AI options
        button_height = 30
        button_width = menu_width - 40
        button_x = menu_x + 20
        button_y = menu_y + 60

        ai_names = list(self.game.ai_algorithms.keys()) + ["Human"]  # ← NEW
        for i, ai_name in enumerate(ai_names):
            pygame.draw.rect(self.screen, (200, 200, 200),
                             (button_x, button_y + i * (button_height + 5),
                              button_width, button_height))
            txt = self.font.render(ai_name, True, (0, 0, 0))
            self.screen.blit(txt, (button_x + button_width // 2 - txt.get_width() // 2,
                                   button_y + i * (button_height + 5) + button_height // 2 - txt.get_height() // 2))

        # Cancel button
        cancel_y = menu_y + menu_height - 50
        pygame.draw.rect(self.screen, (200, 200, 200), (button_x, cancel_y, button_width, button_height))
        cancel_text = self.font.render("Cancel", True, (0, 0, 0))
        self.screen.blit(cancel_text, (button_x + button_width//2 - cancel_text.get_width()//2, 
                                      cancel_y + button_height//2 - cancel_text.get_height()//2))


    # ────────────────────────────────────────────────────────────────────────────
    #  CLICK-HANDLER for the control panel
    # ────────────────────────────────────────────────────────────────────────────
    # ────────────────────────────────────────────────────────────────────────────
    #  CLICK-HANDLER for the control panel   (row-1 buttons, depth +/- …)
    # ────────────────────────────────────────────────────────────────────────────
    def handle_bottom_controls_click(self, pos) -> None:
        """Route a click to the correct bottom‐panel button."""
        for key, rect in self.control_rects.items():
            if not rect.collidepoint(pos):
                continue

            # Row 1 buttons
            if key == "new_game":
                self.game.new_game(player_color=self.game.player_color)
            elif key == "undo":
                self.game.undo_move()
            elif key == "hint":
                self.toggle_hint()

            # Row 3 depth widgets
            elif key == "white_depth_minus":
                self.game.set_ai_depth(max(1, self.game.white_ai_depth - 1),
                                       for_white=True)
            elif key == "white_depth_plus":
                self.game.set_ai_depth(self.game.white_ai_depth + 1,
                                       for_white=True)
            elif key == "black_depth_minus":
                self.game.set_ai_depth(max(1, self.game.black_ai_depth - 1),
                                       for_white=False)
            elif key == "black_depth_plus":
                self.game.set_ai_depth(self.game.black_ai_depth + 1,
                                       for_white=False)

            # Row 4 toggle
            elif key == "toggle_thinking":
                self.game.show_thinking = not self.game.show_thinking

            # Row 2 engine‐label pop-ups
            elif key == "white_ai":
                self.ai_target_colour = chess.WHITE
                self.show_ai_menu = True
            elif key == "black_ai":
                self.ai_target_colour = chess.BLACK
                self.show_ai_menu = True

            return  # stop after handling

    # ─────────────────────────────────────────────────────────────────────────────
    #  Mouse-down: board interaction, bottom panel, tabs
    # ─────────────────────────────────────────────────────────────────────────────
    def handle_mouse_down(self, event):
        if event.button != 1:
            return

        # 1) Game-Over popup?
        if self.game.game_over and hasattr(self, 'game_over_button_rect'):
            if self.game_over_button_rect.collidepoint(event.pos):
                self.game.new_game(player_color=self.game.player_color)
                self.show_hint = False
                return
            if (hasattr(self, 'game_over_close_button_rect') and
                    self.game_over_close_button_rect.collidepoint(event.pos)):
                self.show_game_over_popup = False
                return

        # 2) **Promotion popup?** ← MUST be here, not indented under the game-over block
        if self.show_promotion_menu:
            for piece_type, rect in self.promotion_rects.items():
                if rect.collidepoint(event.pos):
                    from_sq, to_sq = self.pending_promotion_move
                    move = chess.Move(from_sq, to_sq, promotion=piece_type)

                    # clear the popup _before_ we redraw
                    self.show_promotion_menu = False
                    self.pending_promotion_move = None
                    self.promotion_rects.clear()
                    self.selected_square = None
                    self.legal_moves = []
                    self.show_hint = False

                    if move in self.game.board.legal_moves:
                        self.game.make_move(move)
                    return
            # If they clicked anywhere else while popup is up, just eat the click
            return

        # 3) AI-picker popup?
        if self.show_ai_menu:
            self.handle_ai_menu_click(event)
            return

        # … rest of handle_mouse_down remains unchanged …

        # ——— AI-picker menu open? ——————————————————————————————
        if self.show_ai_menu:
            self.handle_ai_menu_click(event)
            return

        # ——— Click on the board? ——————————————————————————————
        board_x = (self.width - self.board_size) // 2
        board_y = 50
        if (board_x <= event.pos[0] <= board_x + self.board_size and
                board_y <= event.pos[1] <= board_y + self.board_size):

            # disabled in AI-vs-AI mode
            if self.game.ai_vs_ai_mode:
                return

            # if game over or AI to move, ignore board clicks
            if self.game.game_over or self.game._ai_for_turn() is not None:
                return

            # … existing logic to pick up / drop pieces …
            col = (event.pos[0] - board_x) // self.square_size
            row = (event.pos[1] - board_y) // self.square_size
            if self.game.player_color == chess.BLACK:
                square = row * 8 + col
            else:
                square = (7 - row) * 8 + col

            piece = self.game.board.piece_at(square)
            if piece and piece.color == self.game.board.turn:
                self.selected_square = square
                self.legal_moves = [
                    m for m in self.game.board.legal_moves
                    if m.from_square == square
                ]
                self.dragging = False
                self.drag_piece = None
                return

            if self.selected_square is not None:
                pawn = self.game.board.piece_at(self.selected_square)
                promo = None
                # detect promotion
                if pawn and pawn.piece_type == chess.PAWN:
                    tgt_rank = square // 8
                    if pawn.color == chess.WHITE and tgt_rank == 7:
                        promo = chess.QUEEN
                    elif pawn.color == chess.BLACK and tgt_rank == 0:
                        promo = chess.QUEEN

                move = chess.Move(self.selected_square, square, promotion=promo)
                if move in self.game.board.legal_moves:
                    if promo and promo == chess.QUEEN:
                        self.pending_promotion_move = (self.selected_square, square)
                        self.show_promotion_menu = True
                    else:
                        self.game.make_move(move)

                self.selected_square = None
                self.legal_moves = []
                self.show_hint = False
                return

        # ——— Click on bottom controls? ——————————————————————————
        self.handle_bottom_controls_click(event.pos)

        # ——— Click on side-tabs? ——————————————————————————————
        tab_w, tab_h = 100, 30
        tab_x = board_x + self.board_size + 20
        tab_y = board_y
        if tab_y <= event.pos[1] <= tab_y + tab_h:
            idx = (event.pos[0] - tab_x) // tab_w
            self.current_tab = ["moves", "analysis", "stats"][max(0, min(idx, 2))]

    # ────────────────────────────────────────────────────────────────────────────
    #  CLICK-HANDLER for the control panel
    # ────────────────────────────────────────────────────────────────────────────

    # ────────────────────────────────────────────────────────────────────────────
    #  Pop-up: handle clicks in the AI-selection menu
    # ────────────────────────────────────────────────────────────────────────────
    def handle_ai_menu_click(self, event):
        """
        Process a mouse-click while the AI-picker pop-up is open.
        • Assign the chosen engine (or None for human) to the colour that was
          active when the menu opened.
        • Close the pop-up immediately.
        • If it's that colour's turn right now and we just assigned an engine,
          ChessGame.set_engine_for_colour will schedule the move on a background thread.
        """
        if event.button != 1:  # left mouse button only
            return

        # Menu geometry
        menu_w, menu_h = 300, 400
        menu_x = (self.width - menu_w) // 2
        menu_y = (self.height - menu_h) // 2

        btn_h = 30
        btn_w = menu_w - 40
        btn_x = menu_x + 20
        btn_y0 = menu_y + 60

        # List of names in the exact same order you draw them
        names = list(self.game.ai_algorithms.keys()) + ["Human"]

        # 1) Click on one of the engine choices?
        for i, name in enumerate(names):
            y1 = btn_y0 + i * (btn_h + 5)
            if btn_x <= event.pos[0] <= btn_x + btn_w and \
                    y1 <= event.pos[1] <= y1 + btn_h:
                # pick the engine (None for Human)
                engine = None if name == "Human" else self.game.ai_algorithms[name]

                # update the game’s engine assignment
                self.game.set_engine_for_colour(self.ai_target_colour, engine)

                # close the menu at once
                self.show_ai_menu = False
                return

        # 2) Click on “Cancel”?
        cancel_y = menu_y + menu_h - 50
        if btn_x <= event.pos[0] <= btn_x + btn_w and \
                cancel_y <= event.pos[1] <= cancel_y + btn_h:
            self.show_ai_menu = False
            return

        # 3) Click outside the menu → close it
        if not (menu_x <= event.pos[0] <= menu_x + menu_w and
                menu_y <= event.pos[1] <= menu_y + menu_h):
            self.show_ai_menu = False

    def handle_mouse_up(self, event):
        """Handle mouse button up events (finish drag-and-drop or promotion)"""
        if event.button != 1:  # left button only
            return

        # 0) If promotion menu is open, ignore releases
        if self.show_promotion_menu:
            return

        # 1) finish a drag-and-drop
        if self.dragging and self.selected_square is not None:
            board_x = (self.width - self.board_size) // 2
            board_y = 50

            # did we release on the board?
            if (board_x <= event.pos[0] <= board_x + self.board_size and
                board_y <= event.pos[1] <= board_y + self.board_size):

                # pixel → square index
                col = (event.pos[0] - board_x) // self.square_size
                row = (event.pos[1] - board_y) // self.square_size
                if self.game.player_color == chess.BLACK:
                    square = row * 8 + col
                else:
                    square = (7 - row) * 8 + col

                pawn = self.game.board.piece_at(self.selected_square)
                promo = None
                # detect promotion
                if pawn and pawn.piece_type == chess.PAWN:
                    target_rank = square // 8
                    if pawn.color == chess.WHITE and target_rank == 7:
                        promo = chess.QUEEN
                    elif pawn.color == chess.BLACK and target_rank == 0:
                        promo = chess.QUEEN

                # if promotion, open menu
                if promo:
                    self.pending_promotion_move = (self.selected_square, square)
                    self.show_promotion_menu = True
                    # skip executing move until choice made
                    self.dragging = False
                    return

                # otherwise normal move
                move = chess.Move(self.selected_square, square)
                if move in self.game.board.legal_moves:
                    # play sounds
                    if self.game.board.is_capture(move):
                        self.play_sound('capture')
                    elif self.game.board.is_castling(move):
                        self.play_sound('castle')
                    elif move.promotion:
                        self.play_sound('promote')
                    else:
                        self.play_sound('move')

                    self.game.make_move(move)

                    if self.game.board.is_check():
                        self.play_sound('check')
                    if self.game.game_over:
                        self.play_sound('game_end')

                    self.show_hint = False

            # reset drag state
            self.dragging = False
            self.drag_piece = None
            self.selected_square = None
            self.legal_moves = []
    
    def handle_mouse_motion(self, event):
        """Handle mouse motion events"""
        # If a square is selected and left button is held, start or continue drag
        if self.selected_square is not None and event.buttons[0]:
            if not self.dragging:
                self.dragging = True
                self.drag_piece = self.game.board.piece_at(self.selected_square)
            self.drag_pos = event.pos
    
    def handle_key_press(self, event):
        """Handle key press events"""
        if event.key == pygame.K_ESCAPE:
            # Deselect piece or close AI menu
            if self.show_ai_menu:
                self.show_ai_menu = False
            else:
                self.selected_square = None
                self.legal_moves = []
                self.dragging = False
                self.drag_piece = None
        elif event.key == pygame.K_u:
            # Undo move
            self.game.undo_move()
            self.selected_square = None
            self.legal_moves = []
            self.show_hint = False
        elif event.key == pygame.K_n:
            # New game
            self.game.new_game()
            self.show_hint = False
        elif event.key == pygame.K_h:
            # Toggle hint
            self.toggle_hint()
        elif event.key == pygame.K_a:
            # Toggle AI vs AI mode
            if self.game.ai_vs_ai_mode:
                self.game.stop_ai_vs_ai()
            else:
                self.game.new_game(ai_vs_ai=True)
        elif event.key == pygame.K_t:
            # Toggle show thinking
            self.game.show_thinking = not self.game.show_thinking

    def toggle_hint(self):
        """Toggle hint on/off and generate a hint move using InsaneModeAI."""
        # Only allow hints when it's the human's turn and the game is in progress
        if (self.game.board.turn == self.game.player_color
                and not self.game.game_over):
            # flip the hint overlay
            self.show_hint = not self.show_hint

            if self.show_hint:
                # pull the InsaneModeAI instance from the game's registry
                insane_ai = self.game.ai_algorithms["Advanced Mode AI (4)"]
                # compute and store the hint move
                self.hint_move = insane_ai.get_best_move(self.game.board)

    def play_sound(self, sound_type):
        """Play a sound effect if available"""
        if sound_type in self.sounds and self.sounds[sound_type]:
            try:
                self.sounds[sound_type].play()
            except:
                pass  # Silently fail if sound can't be played
