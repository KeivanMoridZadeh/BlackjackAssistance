"""
UI module for the Blackjack Assistant.
Contains classes and functions for user interaction.
"""

import os
import re
import sys

class BlackjackUI:
    """User interface for the Blackjack Assistant."""
    
    def __init__(self):
        """Initialize the UI."""
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.suits = ["C", "D", "H", "S"]
        self.suit_symbols = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_num_decks(self):
        """
        Get the number of decks from the user.
        
        Returns:
            int: The number of decks
        """
        while True:
            try:
                num_decks = int(input("Enter the number of decks in play (1-8): "))
                if 1 <= num_decks <= 8:
                    return num_decks
                else:
                    print("Please enter a number between 1 and 8.")
            except ValueError:
                print("Please enter a valid number.")
    
    def display_menu(self):
        """
        Display the main menu and get the user's choice.
        
        Returns:
            str: The user's choice
        """
        print("\n=== Blackjack Assistant ===")
        print("1. Input dealt card")
        print("2. Input player's hand")
        print("3. Input dealer's up card")
        print("4. Get recommendation")
        print("5. View game state")
        print("6. Reset game")
        print("7. Exit")
        
        return input("Enter your choice (1-7): ")
    
    def get_card_input(self, prompt):
        """
        Get a card input from the user.
        
        Args:
            prompt (str): The prompt to display
            
        Returns:
            str: The card string (e.g., "AS" for Ace of Spades)
        """
        while True:
            card_str = input(prompt).upper().strip()
            
            if not card_str:
                return None
            
            # Validate card format
            if re.match(r'^([2-9]|10|[JQKA])([CDHS])$', card_str):
                return card_str
            else:
                print("Invalid card format. Please use format like '10H' for 10 of Hearts or 'AS' for Ace of Spades.")
    
    def clear_player_hand(self, game):
        """
        Clear the player's hand.
        
        Args:
            game (Game): The current game state
        """
        game.player_hand = []
        print("Player's hand cleared.")
    
    def display_player_hand(self, game):
        """
        Display the player's hand.
        
        Args:
            game (Game): The current game state
        """
        if not game.player_hand:
            print("Player's hand is empty.")
            return
        
        hand_value, _, is_soft = game.get_player_hand_value()
        
        print("Player's hand:")
        hand_str = " ".join([str(card) for card in game.player_hand])
        print(f"{hand_str} = {hand_value}{' (soft)' if is_soft else ''}")
    
    def display_recommendations(self, basic_rec, counting_rec, game):
        """
        Display strategy recommendations.
        
        Args:
            basic_rec (dict): Basic strategy recommendation
            counting_rec (dict): Counting strategy recommendation
            game (Game): The current game state
        """
        actions = {
            "H": "Hit",
            "S": "Stand",
            "D": "Double Down",
            "P": "Split"
        }
        
        # Display hand information
        self.display_player_hand(game)
        print(f"Dealer's up card: {game.dealer_upcard}")
        
        # Display basic strategy recommendation
        print("\n=== Basic Strategy Recommendation ===")
        basic_action = actions.get(basic_rec["action"], basic_rec["action"])
        print(f"Action: {basic_action}")
        print(f"Explanation: {basic_rec['explanation']}")
        
        if basic_rec["subsequent_advice"]:
            print(f"Subsequent Advice: {basic_rec['subsequent_advice']}")
        
        # Display counting strategy recommendation
        print("\n=== Card Counting Strategy Recommendation ===")
        counting_action = actions.get(counting_rec["action"], counting_rec["action"])
        print(f"Action: {counting_action}")
        print(f"Explanation: {counting_rec['explanation']}")
        
        if counting_rec["subsequent_advice"]:
            print(f"Subsequent Advice: {counting_rec['subsequent_advice']}")
        
        print(f"\nCounting Information:")
        print(f"Running Count: {counting_rec['running_count']}")
        print(f"True Count: {counting_rec['true_count']:.1f}")
        print(f"Bust Probability: {int(counting_rec['bust_probability'] * 100)}%")
        
        # Display recommended action (use counting strategy)
        print("\n=== Final Recommendation ===")
        if counting_action != basic_action:
            print(f"Recommended action: {counting_action} (deviation from basic strategy)")
        else:
            print(f"Recommended action: {counting_action}")
    
    def display_game_state(self, game):
        """
        Display the current game state.
        
        Args:
            game (Game): The current game state
        """
        print("\n=== Game State ===")
        print(f"Number of decks: {game.num_decks}")
        
        # Display dealer's up card
        if game.dealer_upcard:
            print(f"Dealer's up card: {game.dealer_upcard}")
        else:
            print("Dealer's up card: Not set")
        
        # Display player's hand
        self.display_player_hand(game)
        
        # Display dealt cards
        print("\nDealt cards:")
        if game.dealt_cards:
            dealt_cards_str = " ".join([str(card) for card in game.dealt_cards])
            print(dealt_cards_str)
        else:
            print("No cards dealt yet.")
        
        # Display card counting information
        print("\nCard Counting:")
        print(f"Running count: {game.get_running_count()}")
        print(f"True count: {game.get_true_count():.1f}")
        
        # Display remaining cards
        print("\nRemaining cards:")
        remaining = game.get_remaining_cards()
        for rank, count in remaining.items():
            print(f"{rank}: {count}")
    
    def display_message(self, message):
        """
        Display a message to the user.
        
        Args:
            message (str): The message to display
        """
        print(message) 