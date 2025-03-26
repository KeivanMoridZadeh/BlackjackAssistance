"""
Game module for the Blackjack Assistant.
Contains classes and functions related to blackjack game state and mechanics.
"""

import re
from collections import defaultdict

class Card:
    """Represents a playing card."""
    
    def __init__(self, card_str):
        """
        Initialize a card from a string representation.
        
        Args:
            card_str (str): String representation of a card, e.g., "AS" for Ace of Spades
        """
        # Validate card format
        if not re.match(r'^([2-9]|10|[JQKA])([CDHS])$', card_str):
            raise ValueError(f"Invalid card format: {card_str}")
        
        # Extract rank and suit
        if card_str[0:2] == "10":
            self.rank = "10"
            self.suit = card_str[2]
        else:
            self.rank = card_str[0]
            self.suit = card_str[1]
        
        # Map ranks to values
        rank_values = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
            "J": 10, "Q": 10, "K": 10, "A": 11
        }
        
        self.value = rank_values[self.rank]
        self.is_ace = (self.rank == "A")
    
    def __str__(self):
        """Return string representation of the card."""
        suit_symbols = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}
        return f"{self.rank}{suit_symbols[self.suit]}"
    
    def __repr__(self):
        """Return representation of the card."""
        return f"Card('{self.rank}{self.suit}')"

class Game:
    """Represents a blackjack game state."""
    
    def __init__(self, num_decks=1):
        """
        Initialize a blackjack game.
        
        Args:
            num_decks (int): Number of decks in the shoe
        """
        self.num_decks = num_decks
        self.dealt_cards = []
        self.player_hand = []
        self.dealer_upcard = None
        self.card_count = 0
        
        # Initialize deck
        self.reset_deck()
    
    def reset_deck(self):
        """Reset the deck with the specified number of decks."""
        self.deck = []
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        suits = ["C", "D", "H", "S"]
        
        for _ in range(self.num_decks):
            for rank in ranks:
                for suit in suits:
                    self.deck.append(f"{rank}{suit}")
        
        self.dealt_cards = []
        self.player_hand = []
        self.dealer_upcard = None
        self.card_count = 0
    
    def add_dealt_card(self, card_str):
        """
        Add a card to the list of dealt cards.
        
        Args:
            card_str (str): String representation of a card
        """
        card = Card(card_str)
        self.dealt_cards.append(card)
        self._update_card_count(card)
    
    def add_to_player_hand(self, card_str):
        """
        Add a card to the player's hand.
        
        Args:
            card_str (str): String representation of a card
        """
        card = Card(card_str)
        self.player_hand.append(card)
        self._update_card_count(card)
    
    def set_dealer_upcard(self, card_str):
        """
        Set the dealer's up card.
        
        Args:
            card_str (str): String representation of a card
        """
        self.dealer_upcard = Card(card_str)
        self._update_card_count(self.dealer_upcard)
    
    def _update_card_count(self, card):
        """
        Update the running count based on Hi-Lo card counting system.
        
        Args:
            card (Card): The card to count
        """
        if card.value >= 2 and card.value <= 6:
            self.card_count += 1
        elif card.value >= 10 or card.is_ace:
            self.card_count -= 1
    
    def get_player_hand_value(self):
        """
        Calculate the value of the player's hand.
        
        Returns:
            tuple: (total value, number of aces, is soft hand)
        """
        total = 0
        aces = 0
        
        for card in self.player_hand:
            total += card.value
            if card.is_ace:
                aces += 1
        
        # Adjust for aces
        is_soft = False
        while total > 21 and aces > 0:
            total -= 10  # Convert Ace from 11 to 1
            aces -= 1
        
        if aces > 0 and total <= 11:
            is_soft = True
        
        return (total, aces, is_soft)
    
    def can_split(self):
        """
        Check if the player can split their hand.
        
        Returns:
            bool: True if the player can split, False otherwise
        """
        if len(self.player_hand) != 2:
            return False
        
        return self.player_hand[0].rank == self.player_hand[1].rank
    
    def can_double_down(self):
        """
        Check if the player can double down.
        
        Returns:
            bool: True if the player can double down, False otherwise
        """
        # In most casinos, double down is only allowed on first two cards
        return len(self.player_hand) == 2
    
    def get_running_count(self):
        """
        Get the current running count.
        
        Returns:
            int: The running count
        """
        return self.card_count
    
    def get_true_count(self):
        """
        Calculate the true count based on the number of decks remaining.
        
        Returns:
            float: The true count
        """
        cards_per_deck = 52
        total_cards = self.num_decks * cards_per_deck
        cards_dealt = len(self.dealt_cards)
        
        # Include player hand and dealer upcard in cards_dealt
        cards_dealt += len(self.player_hand)
        if self.dealer_upcard:
            cards_dealt += 1
        
        decks_remaining = (total_cards - cards_dealt) / cards_per_deck
        if decks_remaining <= 0:
            return 0
        
        return self.card_count / decks_remaining
    
    def get_remaining_cards(self):
        """
        Calculate the remaining cards in the deck.
        
        Returns:
            dict: A dictionary mapping card ranks to their remaining counts
        """
        cards_per_rank = {
            "2": 4 * self.num_decks,
            "3": 4 * self.num_decks,
            "4": 4 * self.num_decks,
            "5": 4 * self.num_decks,
            "6": 4 * self.num_decks,
            "7": 4 * self.num_decks,
            "8": 4 * self.num_decks,
            "9": 4 * self.num_decks,
            "10": 16 * self.num_decks,  # 10, J, Q, K
            "A": 4 * self.num_decks
        }
        
        # Count cards that have been dealt
        all_cards = self.dealt_cards + self.player_hand
        if self.dealer_upcard:
            all_cards.append(self.dealer_upcard)
        
        for card in all_cards:
            if card.rank in ["J", "Q", "K"]:
                cards_per_rank["10"] -= 1
            else:
                cards_per_rank[card.rank] -= 1
        
        return cards_per_rank
    
    def calculate_probability_of_bust(self):
        """
        Calculate the probability of busting if the player hits.
        
        Returns:
            float: The probability of busting (0-1)
        """
        hand_value = self.get_player_hand_value()[0]
        
        if hand_value >= 21:
            return 1.0
        
        # Calculate the number of cards that would cause a bust
        bust_threshold = 21 - hand_value
        
        remaining_cards = self.get_remaining_cards()
        total_remaining = sum(remaining_cards.values())
        
        bust_cards = 0
        for rank, count in remaining_cards.items():
            if int(rank) if rank.isdigit() else 10 > bust_threshold:
                bust_cards += count
        
        if total_remaining == 0:
            return 0.0
        
        return bust_cards / total_remaining 