"""
Strategy module for the Blackjack Assistant.
Contains classes and functions related to blackjack gameplay strategies.
"""

class Strategy:
    """Base class for blackjack strategies."""
    
    def get_recommendation(self, game):
        """
        Get a recommendation for the current game state.
        
        Args:
            game (Game): The current game state
            
        Returns:
            dict: A recommendation containing action and explanation
        """
        raise NotImplementedError("Subclasses must implement get_recommendation")

class BasicStrategy(Strategy):
    """
    Basic blackjack strategy that follows the standard rules
    based on the player's hand and the dealer's up card.
    """
    
    def __init__(self):
        """Initialize the basic strategy tables."""
        # Hard hand strategies (no aces or aces counted as 1)
        self.hard_hands = {
            # player total: {dealer upcard: action}
            21: {i: "S" for i in range(2, 12)},  # Always stand on 21
            20: {i: "S" for i in range(2, 12)},  # Always stand on 20
            19: {i: "S" for i in range(2, 12)},  # Always stand on 19
            18: {i: "S" for i in range(2, 12)},  # Always stand on 18
            17: {i: "S" for i in range(2, 12)},  # Always stand on 17
            16: {i: "H" if i == 11 else "S" for i in range(2, 12)},  # Hit vs Ace, stand vs 2-10
            15: {i: "S" if i < 7 else "H" for i in range(2, 12)},    # Stand against 2-6, hit against 7-A
            14: {i: "S" if i < 7 else "H" for i in range(2, 12)},    # Stand against 2-6, hit against 7-A
            13: {i: "S" if i < 7 else "H" for i in range(2, 12)},    # Stand against 2-6, hit against 7-A
            12: {i: "S" if 4 <= i < 7 else "H" for i in range(2, 12)},    # Stand against 4-6, hit against 2-3,7-A
            11: {i: "D" for i in range(2, 12)},   # Always double on 11
            10: {i: "D" if i < 10 else "H" for i in range(2, 12)},   # Double against 2-9, hit against 10,A
            9: {i: "D" if 3 <= i < 7 else "H" for i in range(2, 12)},     # Double against 3-6, hit against 2,7-A
            8: {i: "H" for i in range(2, 12)},    # Always hit on 8 or less
            7: {i: "H" for i in range(2, 12)},
            6: {i: "H" for i in range(2, 12)},
            5: {i: "H" for i in range(2, 12)},
            4: {i: "H" for i in range(2, 12)},
            3: {i: "H" for i in range(2, 12)},
            2: {i: "H" for i in range(2, 12)},
        }
        
        # Soft hand strategies (hand with an ace counted as 11)
        self.soft_hands = {
            # player total: {dealer upcard: action}
            20: {i: "S" for i in range(2, 12)},     # Always stand on soft 20 (A,9)
            19: {i: "S" for i in range(2, 12)},     # Always stand on soft 19 (A,8)
            18: {i: "S" if i < 9 else "H" for i in range(2, 12)},      # Stand against 2-8, hit against 9-A
            17: {i: "D" if 3 <= i < 7 else "H" for i in range(2, 12)},      # Double against 3-6, hit against 2,7-A
            16: {i: "D" if 4 <= i < 7 else "H" for i in range(2, 12)},      # Double against 4-6, hit against 2-3,7-A
            15: {i: "D" if 4 <= i < 7 else "H" for i in range(2, 12)},      # Double against 4-6, hit against 2-3,7-A
            14: {i: "D" if 5 <= i < 7 else "H" for i in range(2, 12)},      # Double against 5-6, hit against 2-4,7-A
            13: {i: "D" if 5 <= i < 7 else "H" for i in range(2, 12)}       # Double against 5-6, hit against 2-4,7-A
        }
        
        # Pair splitting strategies
        self.pair_hands = {
            # pair card: {dealer upcard: action}
            "A": {i: "P" for i in range(2, 12)},    # Always split Aces
            "10": {i: "S" for i in range(2, 12)},   # Never split 10s (or face cards)
            "9": {i: "P" if i in [2, 3, 4, 5, 6, 8, 9] else "S" for i in range(2, 12)},  # Split 9s against 2-6,8,9, stand against 7,10,A
            "8": {i: "P" for i in range(2, 12)},    # Always split 8s
            "7": {i: "P" if i < 8 else "H" for i in range(2, 12)},     # Split 7s against 2-7, hit against 8-A
            "6": {i: "P" if i < 7 else "H" for i in range(2, 12)},     # Split 6s against 2-6, hit against 7-A
            "5": {i: "D" if i < 10 else "H" for i in range(2, 12)},    # Double on 5s against 2-9, hit against 10,A
            "4": {i: "P" if i in [5, 6] else "H" for i in range(2, 12)},          # Split 4s against 5,6, hit against 2-4,7-A
            "3": {i: "P" if i < 8 else "H" for i in range(2, 12)},     # Split 3s against 2-7, hit against 8-A
            "2": {i: "P" if i < 8 else "H" for i in range(2, 12)}      # Split 2s against 2-7, hit against 8-A
        }
    
    def get_recommendation(self, game):
        """
        Get a recommendation based on basic strategy.
        
        Args:
            game (Game): The current game state
            
        Returns:
            dict: A recommendation containing action and explanation
        """
        # Get player's hand value and determine if it's a soft hand
        total, aces, is_soft = game.get_player_hand_value()
        
        # Get dealer's upcard value
        dealer_value = game.dealer_upcard.value
        
        # Check if the hand can be split
        can_split = game.can_split()
        
        # Check if the hand can be doubled down
        can_double = game.can_double_down()
        
        # Determine the recommended action
        action = "H"  # Default action is to hit
        explanation = ""
        
        # Check for pairs first
        if can_split and len(game.player_hand) == 2:
            pair_card = game.player_hand[0].rank
            if pair_card in self.pair_hands and dealer_value in self.pair_hands[pair_card]:
                action = self.pair_hands[pair_card][dealer_value]
        
        # Check for soft hands (if not splitting)
        elif is_soft and total in self.soft_hands and dealer_value in self.soft_hands[total]:
            action = self.soft_hands[total][dealer_value]
            
            # If the strategy says to double but we can't double, hit instead
            if action == "D" and not can_double:
                action = "H"
        
        # Check for hard hands (if not splitting or a soft hand)
        elif total in self.hard_hands and dealer_value in self.hard_hands[total]:
            action = self.hard_hands[total][dealer_value]
            
            # If the strategy says to double but we can't double, hit instead
            if action == "D" and not can_double:
                action = "H"
        
        # Generate explanation based on the action
        if action == "H":
            explanation = f"Hit with {total} against dealer's {dealer_value}."
        elif action == "S":
            explanation = f"Stand with {total} against dealer's {dealer_value}."
        elif action == "D":
            explanation = f"Double down with {total} against dealer's {dealer_value}."
        elif action == "P":
            explanation = f"Split {game.player_hand[0].rank}'s against dealer's {dealer_value}."
        
        # Calculate the probability of busting if hitting
        bust_probability = game.calculate_probability_of_bust()
        
        # Prepare the subsequent advice
        subsequent_advice = ""
        if action == "H":
            if bust_probability > 0.5:
                subsequent_advice = f"Warning: {int(bust_probability * 100)}% chance of busting if you hit."
            else:
                subsequent_advice = f"After hitting, re-evaluate based on your new total. {int(bust_probability * 100)}% chance of busting."
        elif action == "D":
            subsequent_advice = "After doubling, you will receive exactly one more card and then must stand."
        elif action == "P":
            subsequent_advice = "After splitting, play each hand according to basic strategy."
        
        return {
            "action": action,
            "explanation": explanation,
            "subsequent_advice": subsequent_advice,
            "bust_probability": bust_probability
        }

class CountingStrategy(Strategy):
    """
    Card counting blackjack strategy that adjusts the basic strategy
    based on the current count of the deck.
    """
    
    def __init__(self):
        """Initialize the counting strategy."""
        # Use the basic strategy as a foundation
        self.basic_strategy = BasicStrategy()
        
        # Deviation thresholds for when to deviate from basic strategy
        self.true_count_thresholds = {
            "insurance": 3.0,             # Take insurance when true count >= 3
            "16_vs_10": 0.0,              # Stand on 16 vs 10 when true count >= 0
            "15_vs_10": 4.0,              # Stand on 15 vs 10 when true count >= 4
            "10_vs_ace": 4.0,             # Double on 10 vs A when true count >= 4
            "12_vs_3": 2.0,               # Stand on 12 vs 3 when true count >= 2
            "12_vs_2": 3.0,               # Stand on 12 vs 2 when true count >= 3
            "11_vs_ace": 1.0,             # Double on 11 vs A when true count >= 1
            "9_vs_2": 1.0,                # Double on 9 vs 2 when true count >= 1
            "10_10_vs_5": -4.0,           # Split 10,10 vs 5 when true count <= -4
            "10_10_vs_6": -4.0,           # Split 10,10 vs 6 when true count <= -4
        }
    
    def get_recommendation(self, game):
        """
        Get a recommendation based on card counting strategy.
        
        Args:
            game (Game): The current game state
            
        Returns:
            dict: A recommendation containing action and explanation
        """
        # Get the basic strategy recommendation first
        basic_rec = self.basic_strategy.get_recommendation(game)
        
        # Get player's hand value and determine if it's a soft hand
        total, aces, is_soft = game.get_player_hand_value()
        
        # Get dealer's upcard value
        dealer_value = game.dealer_upcard.value
        dealer_rank = game.dealer_upcard.rank
        
        # Get the true count
        true_count = game.get_true_count()
        
        # Initialize counting strategy recommendation with basic strategy
        action = basic_rec["action"]
        explanation = basic_rec["explanation"]
        
        # Check for deviations from basic strategy based on the count
        deviation_made = False
        
        # Insurance deviation
        if dealer_rank == "A" and true_count >= self.true_count_thresholds["insurance"]:
            explanation = f"Consider taking insurance with true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 16 vs 10 deviation
        elif total == 16 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["16_vs_10"]:
            action = "S"  # Stand instead of hit
            explanation = f"Stand with 16 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 15 vs 10 deviation
        elif total == 15 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["15_vs_10"]:
            action = "S"  # Stand instead of hit
            explanation = f"Stand with 15 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 10 vs Ace deviation
        elif total == 10 and dealer_value == 11 and game.can_double_down() and true_count >= self.true_count_thresholds["10_vs_ace"]:
            action = "D"  # Double down instead of hit
            explanation = f"Double down with 10 vs A due to true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 12 vs 3 deviation
        elif total == 12 and dealer_value == 3 and not is_soft and true_count >= self.true_count_thresholds["12_vs_3"]:
            action = "S"  # Stand instead of hit
            explanation = f"Stand with 12 vs 3 due to true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 12 vs 2 deviation
        elif total == 12 and dealer_value == 2 and not is_soft and true_count >= self.true_count_thresholds["12_vs_2"]:
            action = "S"  # Stand instead of hit
            explanation = f"Stand with 12 vs 2 due to true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 11 vs Ace deviation
        elif total == 11 and dealer_value == 11 and game.can_double_down() and true_count >= self.true_count_thresholds["11_vs_ace"]:
            action = "D"  # Double down instead of hit
            explanation = f"Double down with 11 vs A due to true count {true_count:.1f}."
            deviation_made = True
        
        # Hard 9 vs 2 deviation
        elif total == 9 and dealer_value == 2 and game.can_double_down() and true_count >= self.true_count_thresholds["9_vs_2"]:
            action = "D"  # Double down instead of hit
            explanation = f"Double down with 9 vs 2 due to true count {true_count:.1f}."
            deviation_made = True
        
        # 10,10 vs 5 or 6 deviation (only for very negative counts)
        elif (game.can_split() and len(game.player_hand) == 2 and 
              game.player_hand[0].rank in ["10", "J", "Q", "K"] and game.player_hand[1].rank in ["10", "J", "Q", "K"]):
            if dealer_value == 5 and true_count <= self.true_count_thresholds["10_10_vs_5"]:
                action = "P"  # Split instead of stand
                explanation = f"Split 10s vs 5 due to very negative true count {true_count:.1f}."
                deviation_made = True
            elif dealer_value == 6 and true_count <= self.true_count_thresholds["10_10_vs_6"]:
                action = "P"  # Split instead of stand
                explanation = f"Split 10s vs 6 due to very negative true count {true_count:.1f}."
                deviation_made = True
        
        # If no deviation was made, use the basic strategy
        if not deviation_made:
            explanation = f"Follow basic strategy. Current true count: {true_count:.1f}."
        
        # Calculate the probability of busting if hitting
        bust_probability = game.calculate_probability_of_bust()
        
        # Prepare the subsequent advice
        subsequent_advice = basic_rec["subsequent_advice"]
        if deviation_made:
            subsequent_advice += " (This is a deviation from basic strategy based on the count.)"
        
        # Include counting information
        running_count = game.get_running_count()
        counting_info = (
            f"Running count: {running_count}, True count: {true_count:.1f}. "
            f"This affects optimal decisions as the count indicates "
            f"{'more high cards' if true_count > 0 else 'more low cards'} remaining."
        )
        
        return {
            "action": action,
            "explanation": explanation,
            "subsequent_advice": subsequent_advice,
            "bust_probability": bust_probability,
            "running_count": running_count,
            "true_count": true_count,
            "counting_info": counting_info
        }

class EnhancedStrategy(Strategy):
    """
    Enhanced blackjack strategy that combines basic strategy with advanced counting
    techniques to maximize player edge.
    """
    
    def __init__(self):
        """Initialize the enhanced strategy tables."""
        # Use basic strategy as foundation
        self.basic_strategy = BasicStrategy()
        
        # Enhanced deviation thresholds for maximum edge
        self.true_count_thresholds = {
            # Insurance decisions
            "insurance": 2.5,            # Take insurance at true count >= 2.5
            
            # Standing deviations
            "16_vs_10": 0.0,            # Stand on 16 vs 10 at true count >= 0
            "15_vs_10": 3.0,            # Stand on 15 vs 10 at true count >= 3
            "14_vs_10": 4.0,            # Stand on 14 vs 10 at true count >= 4
            "13_vs_10": 5.0,            # Stand on 13 vs 10 at true count >= 5
            "12_vs_10": 5.0,            # Stand on 12 vs 10 at true count >= 5
            "12_vs_3": 1.0,             # Stand on 12 vs 3 at true count >= 1
            "12_vs_2": 2.0,             # Stand on 12 vs 2 at true count >= 2
            "12_vs_4": 1.0,             # Stand on 12 vs 4 at true count >= 1
            "12_vs_5": 1.5,             # Stand on 12 vs 5 at true count >= 1.5
            "12_vs_6": 2.0,             # Stand on 12 vs 6 at true count >= 2
            "13_vs_2": 1.0,             # Stand on 13 vs 2 at true count >= 1
            "13_vs_3": 1.5,             # Stand on 13 vs 3 at true count >= 1.5
            
            # Double down deviations
            "11_vs_ace": 0.5,           # Double on 11 vs A at true count >= 0.5
            "10_vs_ace": 1.0,           # Double on 10 vs A at true count >= 1
            "10_vs_10": 1.0,            # Double on 10 vs 10 at true count >= 1
            "9_vs_2": 0.5,              # Double on 9 vs 2 at true count >= 0.5
            "9_vs_3": 0.5,              # Double on 9 vs 3 at true count >= 0.5
            
            # Soft hand deviations
            "soft_18_vs_9": 0.5,        # Stand on soft 18 vs 9 at true count >= 0.5
            "soft_17_vs_2": 1.0,        # Stand on soft 17 vs 2 at true count >= 1
            "soft_16_vs_4": 0.5,        # Double on soft 16 vs 4 at true count >= 0.5
            "soft_15_vs_4": 0.5,        # Double on soft 15 vs 4 at true count >= 0.5
            "soft_14_vs_5": 0.5,        # Double on soft 14 vs 5 at true count >= 0.5
            "soft_13_vs_5": 0.5,        # Double on soft 13 vs 5 at true count >= 0.5
            
            # Pair splitting deviations
            "10_10_vs_5": -3.0,         # Split 10s vs 5 at true count <= -3
            "10_10_vs_6": -3.0,         # Split 10s vs 6 at true count <= -3
            "8_8_vs_10": 1.0,           # Split 8s vs 10 at true count >= 1
            "6_6_vs_7": 1.0,            # Split 6s vs 7 at true count >= 1
            "5_5_vs_10": 1.0,           # Split 5s vs 10 at true count >= 1
            "4_4_vs_4": 1.0,            # Split 4s vs 4 at true count >= 1
            "3_3_vs_8": 1.0,            # Split 3s vs 8 at true count >= 1
            "2_2_vs_8": 1.0,            # Split 2s vs 8 at true count >= 1
            
            # Surrender deviations (if allowed)
            "surrender_15_vs_10": -1.0,  # Surrender 15 vs 10 at true count <= -1
            "surrender_14_vs_10": -2.0,  # Surrender 14 vs 10 at true count <= -2
            "surrender_13_vs_10": -3.0,  # Surrender 13 vs 10 at true count <= -3
        }
        
        # Hand composition adjustments
        self.hand_composition = {
            "high_cards": ["10", "J", "Q", "K", "A"],
            "low_cards": ["2", "3", "4", "5", "6"],
            "mid_cards": ["7", "8", "9"]
        }
    
    def get_recommendation(self, game):
        """
        Get a recommendation based on enhanced strategy.
        
        Args:
            game (Game): The current game state
            
        Returns:
            dict: A recommendation containing action and explanation
        """
        # Get basic strategy recommendation as foundation
        basic_rec = self.basic_strategy.get_recommendation(game)
        
        # Get player's hand value and determine if it's a soft hand
        total, aces, is_soft = game.get_player_hand_value()
        
        # Get dealer's upcard value and rank
        dealer_value = game.dealer_upcard.value
        dealer_rank = game.dealer_upcard.rank
        
        # Get the true count
        true_count = game.get_true_count()
        
        # Initialize enhanced strategy recommendation
        action = basic_rec["action"]
        explanation = basic_rec["explanation"]
        
        # Check for deviations based on enhanced thresholds
        deviation_made = False
        
        # Insurance deviation
        if dealer_rank == "A" and true_count >= self.true_count_thresholds["insurance"]:
            explanation = f"Consider taking insurance with true count {true_count:.1f}."
            deviation_made = True
        
        # Standing deviations
        elif total == 16 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["16_vs_10"]:
            action = "S"
            explanation = f"Stand with 16 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        elif total == 15 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["15_vs_10"]:
            action = "S"
            explanation = f"Stand with 15 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        elif total == 14 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["14_vs_10"]:
            action = "S"
            explanation = f"Stand with 14 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        elif total == 13 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["13_vs_10"]:
            action = "S"
            explanation = f"Stand with 13 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        elif total == 12 and dealer_value == 10 and not is_soft and true_count >= self.true_count_thresholds["12_vs_10"]:
            action = "S"
            explanation = f"Stand with 12 vs 10 due to true count {true_count:.1f}."
            deviation_made = True
        
        # Soft hand deviations
        elif is_soft:
            if total == 18 and dealer_value == 9 and true_count >= self.true_count_thresholds["soft_18_vs_9"]:
                action = "S"
                explanation = f"Stand on soft 18 vs 9 due to true count {true_count:.1f}."
                deviation_made = True
            
            elif total == 17 and dealer_value == 2 and true_count >= self.true_count_thresholds["soft_17_vs_2"]:
                action = "S"
                explanation = f"Stand on soft 17 vs 2 due to true count {true_count:.1f}."
                deviation_made = True
            
            elif total == 16 and dealer_value == 4 and game.can_double_down() and true_count >= self.true_count_thresholds["soft_16_vs_4"]:
                action = "D"
                explanation = f"Double on soft 16 vs 4 due to true count {true_count:.1f}."
                deviation_made = True
        
        # Double down deviations
        elif game.can_double_down():
            if total == 11 and dealer_value == 11 and true_count >= self.true_count_thresholds["11_vs_ace"]:
                action = "D"
                explanation = f"Double on 11 vs A due to true count {true_count:.1f}."
                deviation_made = True
            
            elif total == 10 and dealer_value == 11 and true_count >= self.true_count_thresholds["10_vs_ace"]:
                action = "D"
                explanation = f"Double on 10 vs A due to true count {true_count:.1f}."
                deviation_made = True
            
            elif total == 10 and dealer_value == 10 and true_count >= self.true_count_thresholds["10_vs_10"]:
                action = "D"
                explanation = f"Double on 10 vs 10 due to true count {true_count:.1f}."
                deviation_made = True
        
        # Pair splitting deviations
        elif game.can_split() and len(game.player_hand) == 2:
            card1 = game.player_hand[0].rank
            card2 = game.player_hand[1].rank
            
            if card1 in ["10", "J", "Q", "K"] and card2 in ["10", "J", "Q", "K"]:
                if dealer_value == 5 and true_count <= self.true_count_thresholds["10_10_vs_5"]:
                    action = "P"
                    explanation = f"Split 10s vs 5 due to very negative true count {true_count:.1f}."
                    deviation_made = True
                elif dealer_value == 6 and true_count <= self.true_count_thresholds["10_10_vs_6"]:
                    action = "P"
                    explanation = f"Split 10s vs 6 due to very negative true count {true_count:.1f}."
                    deviation_made = True
            
            elif card1 == "8" and card2 == "8" and dealer_value == 10 and true_count >= self.true_count_thresholds["8_8_vs_10"]:
                action = "P"
                explanation = f"Split 8s vs 10 due to true count {true_count:.1f}."
                deviation_made = True
        
        # Calculate the probability of busting if hitting
        bust_probability = game.calculate_probability_of_bust()
        
        # Prepare the subsequent advice
        subsequent_advice = basic_rec["subsequent_advice"]
        if deviation_made:
            subsequent_advice += " (This is an enhanced strategy deviation based on the count.)"
        
        # Include counting information
        running_count = game.get_running_count()
        counting_info = (
            f"Running count: {running_count}, True count: {true_count:.1f}. "
            f"This affects optimal decisions as the count indicates "
            f"{'more high cards' if true_count > 0 else 'more low cards'} remaining."
        )
        
        return {
            "action": action,
            "explanation": explanation,
            "subsequent_advice": subsequent_advice,
            "bust_probability": bust_probability,
            "running_count": running_count,
            "true_count": true_count,
            "counting_info": counting_info
        } 