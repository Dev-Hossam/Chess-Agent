#!/usr/bin/env python3

import pygame
import sys
import os
from chess_game import ChessGame

def main():


    pygame.init()

    os.makedirs('assets/sounds', exist_ok=True)
    
    game = ChessGame()
    
    try:
        game.gui.load_background_music('assets/music/bgm.mp3', volume=1.2)
        game.start_game()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
