#!/usr/bin/env python3
"""
Blackjack Assistant (GUI Version) - A Python application that helps players make optimal decisions in blackjack games.
Features drag-and-drop functionality for cards with deck-based limitations.
"""

import sys
import os
import tkinter as tk

from blackjack.game import Game
from blackjack.strategy import EnhancedStrategy
from blackjack.gui import BlackjackGUI

def main():
    """Main entry point for the Blackjack Assistant GUI application."""
    # Create the root window
    root = tk.Tk()
    root.title("Blackjack Assistant - Enhanced Strategy")
    
    # Initialize game components
    game = Game(num_decks=6)  # Default to 6 decks
    enhanced_strategy = EnhancedStrategy()
    
    # Create and start the GUI
    gui = BlackjackGUI(root)
    gui.set_game_and_strategies(game, enhanced_strategy, enhanced_strategy)  # Use enhanced strategy for both
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1) 