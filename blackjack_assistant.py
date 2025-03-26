#!/usr/bin/env python3
"""
Blackjack Assistant - A Python application that helps players make optimal decisions in blackjack games.
"""

import sys
import os
from blackjack.game import Game
from blackjack.ui import BlackjackUI
from blackjack.strategy import BasicStrategy, CountingStrategy

def main():
    """Main entry point for the Blackjack Assistant application."""
    print("Welcome to Blackjack Assistant!")
    print("This application helps you make optimal decisions while playing blackjack.")
    
    # Initialize the UI
    ui = BlackjackUI()
    
    # Get the number of decks from the user
    num_decks = ui.get_num_decks()
    
    # Initialize the game with the specified number of decks
    game = Game(num_decks)
    
    # Load strategies
    basic_strategy = BasicStrategy()
    counting_strategy = CountingStrategy()
    
    while True:
        # Display menu and get user choice
        choice = ui.display_menu()
        
        if choice == '1':  # Input dealt card
            card = ui.get_card_input("Enter a card that has been dealt (e.g., 10H for 10 of Hearts): ")
            if card:
                game.add_dealt_card(card)
                ui.display_message(f"Added {card} to dealt cards.")
        
        elif choice == '2':  # Input player's hand
            ui.clear_player_hand(game)
            while True:
                card = ui.get_card_input("Enter a card in your hand (or press Enter to finish): ")
                if not card:
                    break
                game.add_to_player_hand(card)
            
            ui.display_player_hand(game)
        
        elif choice == '3':  # Input dealer's up card
            card = ui.get_card_input("Enter the dealer's up card: ")
            if card:
                game.set_dealer_upcard(card)
                ui.display_message(f"Dealer's up card set to {card}.")
        
        elif choice == '4':  # Get recommendation
            if not game.player_hand:
                ui.display_message("Please input your hand first.")
                continue
                
            if not game.dealer_upcard:
                ui.display_message("Please input dealer's up card first.")
                continue
            
            # Get recommendations from both strategies
            basic_recommendation = basic_strategy.get_recommendation(game)
            counting_recommendation = counting_strategy.get_recommendation(game)
            
            # Display recommendations
            ui.display_recommendations(basic_recommendation, counting_recommendation, game)
            
        elif choice == '5':  # View game state
            ui.display_game_state(game)
            
        elif choice == '6':  # Reset game
            num_decks = ui.get_num_decks()
            game = Game(num_decks)
            ui.display_message("Game reset with " + str(num_decks) + " deck(s).")
            
        elif choice == '7':  # Exit
            print("Thank you for using Blackjack Assistant!")
            sys.exit(0)
            
        else:
            ui.display_message("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting Blackjack Assistant...")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1) 