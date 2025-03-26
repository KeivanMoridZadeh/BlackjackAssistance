"""
GUI module for the Blackjack Assistant.
Contains classes and functions for graphical user interface with drag-and-drop functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re

class DraggableCard(ttk.Label):
    """A draggable card widget."""
    
    def __init__(self, parent, rank, gui):
        """
        Initialize the draggable card.
        
        Args:
            parent: The parent widget
            rank: The rank of the card (e.g., "A" for Ace)
            gui: Reference to the main GUI
        """
        super().__init__(parent, text=rank, relief="raised", borderwidth=1)
        self.rank = rank
        self.gui = gui
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.original_parent = parent
        self.original_geometry = None

    def start_drag(self, event):
        """Start dragging the card."""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.original_parent = self.winfo_parent()
        self.original_geometry = self.winfo_geometry()
        self.lift()  # Bring to front while dragging

    def drag(self, event):
        """Handle card dragging."""
        x = self.winfo_x() - self.drag_data["x"] + event.x
        y = self.winfo_y() - self.drag_data["y"] + event.y
        self.place(x=x, y=y)

    def stop_drag(self, event):
        """Stop dragging and handle card placement."""
        # Get the widget under the cursor
        widget_under = event.widget.winfo_containing(event.x_root, event.y_root)
        
        # If we're over a drop target, handle the drop
        if isinstance(widget_under, DropTarget):
            self.handle_drop(widget_under)
        else:
            # Return to original position
            self.return_to_original_position()

    def handle_drop(self, drop_target):
        """Handle dropping the card on a target."""
        try:
            # Check if we can add the card to the target
            if drop_target.can_add_card(self.rank):
                # Add the card to the target
                drop_target.add_card(self.rank)
                
                # Update the card counts
                self.gui.update_card_counts()
                
                # Update the counts display
                self.gui.update_counts()
                
                # Remove the card from available cards
                self.gui.remove_card_from_available(self.rank)
                
                # Update the game state
                self.gui.update_game_state()
                
                # Return to original position
                self.return_to_original_position()
            else:
                # Return to original position if we can't add the card
                self.return_to_original_position()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.return_to_original_position()

    def return_to_original_position(self):
        """Return the card to its original position."""
        if self.original_geometry:
            # Parse the geometry string
            match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', self.original_geometry)
            if match:
                width, height, x, y = map(int, match.groups())
                self.place(x=x, y=y)
            else:
                self.place_forget()
        else:
            self.place_forget()

class DropTarget(ttk.Frame):
    """A drop target for cards."""
    
    def __init__(self, parent, target_type, text, width=200, height=100):
        """
        Initialize the drop target.
        
        Args:
            parent: The parent widget
            target_type: The type of target ("dealer", "player", or "dealt")
            text: The text to display
            width: The width of the target
            height: The height of the target
        """
        super().__init__(parent)
        self.target_type = target_type
        self.cards = []
        self.card_labels = []
        
        # Create a label for the text
        self.label = ttk.Label(self, text=text)
        self.label.pack(side="top", pady=5)
        
        # Create a frame for the cards
        self.cards_frame = ttk.Frame(self, width=width, height=height, relief="sunken", borderwidth=1)
        self.cards_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.cards_frame.pack_propagate(False)  # Maintain specified size

    def can_add_card(self, rank):
        """Check if a card can be added to this target."""
        if self.target_type == "dealer":
            return len(self.cards) == 0  # Only one card allowed
        elif self.target_type == "player":
            return len(self.cards) < 5  # Maximum 5 cards
        else:  # dealt
            return True  # No limit on dealt cards

    def add_card(self, rank):
        """Add a card to this target."""
        if self.can_add_card(rank):
            self.cards.append(rank)
            self.update_display()
        else:
            raise ValueError(f"Cannot add more cards to {self.target_type} target")

    def remove_card(self, rank):
        """Remove a card from this target."""
        if rank in self.cards:
            self.cards.remove(rank)
            self.update_display()
        else:
            raise ValueError(f"Card not found in {self.target_type} target")

    def update_display(self):
        """Update the display of cards in this target."""
        # Clear existing card labels
        for label in self.card_labels:
            label.destroy()
        self.card_labels.clear()
        
        # Create new card labels
        x_offset = 0
        for rank in self.cards:
            label = ttk.Label(self.cards_frame, text=rank, relief="raised", borderwidth=1)
            label.place(x=x_offset, y=5)
            self.card_labels.append(label)
            x_offset += 30  # Space between cards

    def clear(self):
        """Clear all cards from this target."""
        self.cards.clear()
        self.update_display()

class CardCountDisplay(ttk.Frame):
    """Display for card counting information."""
    
    def __init__(self, parent):
        """Initialize the card count display."""
        super().__init__(parent)
        
        # Create labels for counts
        ttk.Label(self, text="Running Count:").pack(side="left", padx=5)
        self.running_count_label = ttk.Label(self, text="0", relief="sunken")
        self.running_count_label.pack(side="left", padx=5)
        
        ttk.Label(self, text="True Count:").pack(side="left", padx=5)
        self.true_count_label = ttk.Label(self, text="0.0", relief="sunken")
        self.true_count_label.pack(side="left", padx=5)
        
        ttk.Label(self, text="Bust Probability:").pack(side="left", padx=5)
        self.bust_prob_label = ttk.Label(self, text="0%", relief="sunken")
        self.bust_prob_label.pack(side="left", padx=5)
    
    def update_counts(self, running_count, true_count, bust_probability):
        """Update the count displays."""
        self.running_count_label.config(text=str(running_count))
        self.true_count_label.config(text=f"{true_count:.1f}")
        self.bust_prob_label.config(text=f"{int(bust_probability * 100)}%")

class BlackjackGUI:
    """Graphical user interface for the Blackjack Assistant with drag-and-drop functionality."""
    
    def __init__(self, root):
        """
        Initialize the GUI.
        
        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("Blackjack Assistant - Strategy Mode")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Store reference to GUI in root for access from DraggableCard
        self.root.gui = self
        
        # Set theme and style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat")
        self.style.configure("TLabel", padding=6)
        self.style.configure("TFrame", padding=6)
        
        # Define card ranks (J, Q, K are treated as 10)
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]
        
        # Variables
        self.num_decks = tk.IntVar(value=1)
        
        # Card counts dictionary to track remaining cards
        self.card_counts = {}
        
        # Create main layout frames
        self.create_layout()
        
        # Create drop targets list in root for DraggableCard to access
        self.root.drop_targets = [
            self.dealer_drop_target,
            self.player_drop_target,
            self.dealt_drop_target
        ]
        
        # Initialize game
        self.game = None
        self.basic_strategy = None
        self.counting_strategy = None
    
    def create_layout(self):
        """Create the main layout for the application."""
        # Create top panel for settings
        self.create_settings_panel()
        
        # Create main workspace with drop targets and card source
        self.create_workspace()
        
        # Create card tracking panel
        self.create_card_tracking_panel()
    
    def create_settings_panel(self):
        """Create the panel for game settings."""
        panel = ttk.Frame(self.root)
        panel.pack(fill="x", padx=10, pady=5)
        
        # Deck configuration
        ttk.Label(panel, text="Number of decks:").pack(side="left", padx=5)
        deck_spinner = ttk.Spinbox(panel, from_=1, to=8, width=5, textvariable=self.num_decks)
        deck_spinner.pack(side="left", padx=5)
        
        ttk.Button(panel, text="Set Decks", command=self.set_decks).pack(side="left", padx=5)
        ttk.Button(panel, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)
        ttk.Button(panel, text="Get Recommendation", command=self.get_recommendation).pack(side="left", padx=20)
        ttk.Button(panel, text="Next Hand", command=self.next_hand).pack(side="left", padx=5)
    
    def create_workspace(self):
        """Create the main workspace with drop targets and card source."""
        workspace = ttk.Frame(self.root)
        workspace.pack(fill="both", padx=10, pady=5, expand=True)
        
        # Create split panes
        paned_window = ttk.PanedWindow(workspace, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create left panel for card source and recommendation
        left_panel = ttk.Frame(paned_window)
        paned_window.add(left_panel, weight=1)
        
        # Create right panel for targets
        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=1)
        
        # Create a card source area
        self.create_card_source_panel(left_panel)
        
        # Create recommendation panel in left panel
        recommendation_frame = ttk.LabelFrame(left_panel, text="Recommendation")
        recommendation_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text area for recommendation display with normal size
        self.recommendation_text = scrolledtext.ScrolledText(recommendation_frame, height=6, width=80, wrap=tk.WORD, 
                                                          font=("Arial", 10))
        self.recommendation_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.recommendation_text.insert(tk.END, "Recommendation will appear here when you add cards to your hand and the dealer's hand, then click 'Get Recommendation'.")
        self.recommendation_text.config(state="disabled")
        
        # Create card count display
        self.count_display = CardCountDisplay(left_panel)
        self.count_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create drop targets in right panel
        self.dealer_drop_target = DropTarget(right_panel, "dealer", "Dealer's Hand (Drop Cards Here)", 
                                           width=400, height=150)
        self.dealer_drop_target.pack(side="top", fill="x", padx=5, pady=5)
        
        # Create a frame for player and dealt cards side by side
        card_areas = ttk.Frame(right_panel)
        card_areas.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.player_drop_target = DropTarget(card_areas, "player", "Your Hand (Drop Cards Here)", 
                                           width=200, height=150)
        self.player_drop_target.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.dealt_drop_target = DropTarget(card_areas, "dealt", "Dealt/Wasted Cards (Drop Cards Here)", 
                                          width=200, height=150)
        self.dealt_drop_target.pack(side="right", fill="both", expand=True, padx=5, pady=5)
    
    def create_card_source_panel(self, parent):
        """
        Create a panel with all available cards in three columns.
        
        Args:
            parent: The parent widget
        """
        card_source = ttk.LabelFrame(parent, text="Available Cards (Click to Add)")
        card_source.pack(fill="x", padx=5, pady=5)
        
        # Create a frame for the three columns
        columns_frame = ttk.Frame(card_source)
        columns_frame.pack(fill="both", padx=5, pady=5)
        
        # Create three columns
        dealer_column = ttk.LabelFrame(columns_frame, text="Dealer Cards")
        dealer_column.pack(side="left", fill="both", expand=True, padx=5)
        
        player_column = ttk.LabelFrame(columns_frame, text="Player Cards")
        player_column.pack(side="left", fill="both", expand=True, padx=5)
        
        wasted_column = ttk.LabelFrame(columns_frame, text="Wasted Cards")
        wasted_column.pack(side="left", fill="both", expand=True, padx=5)
        
        # Create cards in each column
        for rank_idx, rank in enumerate(self.ranks):
            # Dealer column
            dealer_card = ttk.Label(dealer_column, text=rank, relief="raised", borderwidth=1)
            dealer_card.grid(row=rank_idx, column=0, padx=2, pady=2)
            dealer_card.bind("<Button-1>", lambda e, r=rank: self.set_dealer_card(r))
            
            # Player column
            player_card = ttk.Label(player_column, text=rank, relief="raised", borderwidth=1)
            player_card.grid(row=rank_idx, column=0, padx=2, pady=2)
            player_card.bind("<Button-1>", lambda e, r=rank: self.add_to_player_hand(r))
            
            # Wasted column
            wasted_card = ttk.Label(wasted_column, text=rank, relief="raised", borderwidth=1)
            wasted_card.grid(row=rank_idx, column=0, padx=2, pady=2)
            wasted_card.bind("<Button-1>", lambda e, r=rank: self.add_to_dealt_cards(r))
    
    def create_recommendation_panel(self):
        """Create the panel for displaying recommendations."""
        # This method is no longer needed as the recommendation panel is now created in create_workspace
        pass
    
    def create_card_tracking_panel(self):
        """Create the panel for tracking cards and counts."""
        panel = ttk.Frame(self.root)
        panel.pack(fill="x", padx=10, pady=5)
        
        # Create a frame for running count and true count
        counts_frame = ttk.LabelFrame(panel, text="Card Counting")
        counts_frame.pack(fill="x", padx=5, pady=5)
        
        count_info = ttk.Frame(counts_frame)
        count_info.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(count_info, text="Running Count:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.running_count_label = ttk.Label(count_info, text="0", width=5, 
                                           background="white", relief="sunken")
        self.running_count_label.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(count_info, text="True Count:").grid(row=0, column=2, padx=20, pady=2, sticky="w")
        self.true_count_label = ttk.Label(count_info, text="0.0", width=5, 
                                        background="white", relief="sunken")
        self.true_count_label.grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(count_info, text="Bust Probability:").grid(row=0, column=4, padx=20, pady=2, sticky="w")
        self.bust_prob_label = ttk.Label(count_info, text="0%", width=5, 
                                        background="white", relief="sunken")
        self.bust_prob_label.grid(row=0, column=5, padx=5, pady=2)
    
    def set_game_and_strategies(self, game, basic_strategy, counting_strategy):
        """
        Set the game and strategy objects.
        
        Args:
            game: The game object
            basic_strategy: The basic strategy object
            counting_strategy: The counting strategy object
        """
        self.game = game
        self.basic_strategy = basic_strategy
        self.counting_strategy = counting_strategy
        
        # Update the deck count display
        self.num_decks.set(game.num_decks)
        
        # Initialize card counts
        self.initialize_card_counts()
        
        # Reset UI elements
        self.clear_displays()
        self.update_counts()
    
    def initialize_card_counts(self):
        """Initialize the card counts based on the number of decks."""
        self.card_counts = {}
        
        # Initialize all ranks with deck count * 4 (since each rank appears in all 4 suits)
        deck_count = self.num_decks.get()
        for rank in self.ranks:
            if rank == "10":
                # For 10, count includes J, Q, K (4 cards per suit)
                self.card_counts[rank] = deck_count * 16  # 4 cards × 4 suits
            else:
                self.card_counts[rank] = deck_count * 4  # 1 card × 4 suits
        
        # Initialize display
        self.update_card_count_display()
    
    def set_decks(self):
        """Set the number of decks and reinitialize the game."""
        if self.game:
            deck_count = self.num_decks.get()
            if 1 <= deck_count <= 8:
                self.game.num_decks = deck_count
                self.game.reset_deck()
                self.initialize_card_counts()
                self.clear_displays()
                self.update_counts()
                messagebox.showinfo("Deck Count", f"Game reset with {deck_count} deck(s).")
            else:
                messagebox.showerror("Invalid Input", "Please enter a number between 1 and 8.")
    
    def reset_game(self):
        """Reset the game."""
        if self.game:
            deck_count = self.num_decks.get()
            self.game.num_decks = deck_count
            self.game.reset_deck()
            self.initialize_card_counts()
            self.clear_displays()
            self.update_counts()
            messagebox.showinfo("Game Reset", f"Game reset with {deck_count} deck(s).")
    
    def clear_displays(self):
        """Clear all displays."""
        # Clear dealer display
        for widget in self.dealer_drop_target.cards_frame.winfo_children():
            widget.destroy()
        
        # Clear player display
        for widget in self.player_drop_target.cards_frame.winfo_children():
            widget.destroy()
        
        # Clear dealt display
        for widget in self.dealt_drop_target.cards_frame.winfo_children():
            widget.destroy()
        
        # Reset recommendation
        self.recommendation_text.config(state="normal")
        self.recommendation_text.delete(1.0, tk.END)
        self.recommendation_text.insert(tk.END, "Recommendation will appear here when you add cards to your hand and the dealer's hand, then click 'Get Recommendation'.")
        self.recommendation_text.config(state="disabled")
        
        # Reset count displays
        self.update_counts()
    
    def update_card_count_display(self):
        """Update the card count display."""
        if not self.game:
            return
            
        # Get the running count and true count
        running_count = self.game.get_running_count()
        true_count = self.game.get_true_count()
        
        # Calculate bust probability
        bust_probability = 0.0
        if self.game.player_hand:
            bust_probability = self.game.calculate_probability_of_bust()
        
        # Update the display
        self.count_display.update_counts(running_count, true_count, bust_probability)
    
    def decrement_card_count(self, rank):
        """
        Decrement the count for a specific rank.
        
        Returns:
            bool: True if the card is available, False otherwise
        """
        if rank in self.card_counts:
            if self.card_counts[rank] > 0:
                self.card_counts[rank] -= 1
                self.update_card_count_display()
                return True
            else:
                return False
        return False
    
    def set_dealer_card(self, rank):
        """
        Set the dealer's up card.
        
        Args:
            rank (str): Rank of the card
        """
        if self.game:
            try:
                # Check card count
                if not self.decrement_card_count(rank):
                    messagebox.showerror("No Cards Left", f"No more {rank}s available in the deck.")
                    return
                
                # Remove any existing dealer cards from display
                for widget in self.dealer_drop_target.cards_frame.winfo_children():
                    widget.destroy()
                
                # Add new card to game and update display
                self.game.set_dealer_upcard(rank + "S")  # Add dummy suit since game logic requires it
                
                # Create visual card
                card = DraggableCard(self.dealer_drop_target.cards_frame, rank, self)
                card.pack(side="left", padx=5, pady=5)
                
                # Update counts
                self.update_counts()
            except ValueError as e:
                messagebox.showerror("Invalid Card", str(e))
    
    def add_to_player_hand(self, rank):
        """
        Add a card to the player's hand.
        
        Args:
            rank (str): Rank of the card
        """
        if self.game:
            try:
                # Check card count
                if not self.decrement_card_count(rank):
                    messagebox.showerror("No Cards Left", f"No more {rank}s available in the deck.")
                    return
                
                # Add card to game
                self.game.add_to_player_hand(rank + "S")  # Add dummy suit since game logic requires it
                
                # Create visual card
                card = DraggableCard(self.player_drop_target.cards_frame, rank, self)
                card.pack(side="left", padx=5, pady=5)
                
                # Update counts
                self.update_counts()
            except ValueError as e:
                messagebox.showerror("Invalid Card", str(e))
    
    def add_to_dealt_cards(self, rank):
        """
        Add a card to the dealt cards.
        
        Args:
            rank (str): Rank of the card
        """
        if self.game:
            try:
                # Check card count
                if not self.decrement_card_count(rank):
                    messagebox.showerror("No Cards Left", f"No more {rank}s available in the deck.")
                    return
                
                # Add card to game
                self.game.add_dealt_card(rank + "S")  # Add dummy suit since game logic requires it
                
                # Create visual card
                card = DraggableCard(self.dealt_drop_target.cards_frame, rank, self)
                card.pack(side="left", padx=2, pady=2)
                
                # Update counts
                self.update_counts()
            except ValueError as e:
                messagebox.showerror("Invalid Card", str(e))
    
    def update_counts(self):
        """Update the count displays."""
        if not self.game:
            return
        
        # Update running count
        running_count = self.game.get_running_count()
        self.running_count_label.config(text=str(running_count))
        
        # Update true count
        true_count = self.game.get_true_count()
        self.true_count_label.config(text=f"{true_count:.1f}")
        
        # Update bust probability
        if self.game.player_hand:
            bust_prob = self.game.calculate_probability_of_bust() * 100
            self.bust_prob_label.config(text=f"{int(bust_prob)}%")
        else:
            self.bust_prob_label.config(text="0%")
    
    def get_recommendation(self):
        """Get and display a recommendation."""
        if not self.game:
            messagebox.showerror("Input Error", "Game not initialized. Please restart the application.")
            return
        
        # Check if player hand and dealer upcard are set
        if not self.game.player_hand:
            messagebox.showerror("Input Error", "Please add cards to your hand first by dragging cards to 'Your Hand' area.")
            return
        
        if not self.game.dealer_upcard:
            messagebox.showerror("Input Error", "Please set the dealer's up card first by dragging a card to 'Dealer's Hand' area.")
            return
        
        try:
            # Show user that we're processing
            self.recommendation_text.config(state="normal")
            self.recommendation_text.delete(1.0, tk.END)
            self.recommendation_text.insert(tk.END, "Calculating recommendation...")
            self.recommendation_text.config(state="disabled")
            self.root.update_idletasks()  # Force UI update
            
            # Get recommendations from both strategies
            basic_recommendation = self.basic_strategy.get_recommendation(self.game)
            counting_recommendation = self.counting_strategy.get_recommendation(self.game)
            
            # For debugging
            print(f"Player hand: {[f'{c.rank}{c.suit}' for c in self.game.player_hand]}")
            print(f"Dealer upcard: {self.game.dealer_upcard.rank}{self.game.dealer_upcard.suit}")
            print(f"Basic recommendation: {basic_recommendation}")
            print(f"Counting recommendation: {counting_recommendation}")
            
            # Display final recommendation (prefer counting strategy)
            self.display_final_recommendation(counting_recommendation)
        except Exception as e:
            error_msg = f"Failed to get recommendation: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
            import traceback
            traceback.print_exc()
    
    def display_final_recommendation(self, recommendation):
        """
        Display the final recommendation.
        
        Args:
            recommendation (dict): The recommendation from the strategy
        """
        if not recommendation:
            messagebox.showerror("Error", "No recommendation available")
            return
            
        actions = {
            "H": "Hit",
            "S": "Stand",
            "D": "Double Down",
            "P": "Split"
        }
        
        # Get the action in full text
        action = actions.get(recommendation["action"], recommendation["action"])
        
        # Update text area with complete recommendation
        self.recommendation_text.config(state="normal")
        self.recommendation_text.delete(1.0, tk.END)
        
        # Format the complete recommendation text with bold action
        recommendation_text = f"RECOMMENDED ACTION: {action}\n\n"
        explanation = recommendation.get('explanation', 'No explanation available')
        recommendation_text += f"{explanation}\n"
        
        # Add additional information
        if "subsequent_advice" in recommendation and recommendation["subsequent_advice"]:
            recommendation_text += f"\n{recommendation['subsequent_advice']}\n"
        
        if "bust_probability" in recommendation:
            bust_prob = int(recommendation["bust_probability"] * 100)
            recommendation_text += f"\nBust Probability: {bust_prob}%\n"
        
        if "running_count" in recommendation and "true_count" in recommendation:
            recommendation_text += f"\nRunning Count: {recommendation['running_count']}, True Count: {recommendation['true_count']:.1f}\n"
        
        self.recommendation_text.insert(tk.END, recommendation_text)
        
        try:
            # Add tags for formatting
            self.recommendation_text.tag_add("header", "1.0", "1.end")
            self.recommendation_text.tag_configure("header", font=("Arial", 12, "bold"))
            
            # Highlight text if it's a deviation
            if "deviation" in explanation.lower():
                self.recommendation_text.tag_add("deviation", "2.0", "3.end")
                self.recommendation_text.tag_configure("deviation", foreground="red")
        except Exception as e:
            print(f"Error applying text formatting: {e}")
        
        self.recommendation_text.config(state="disabled")
        
        # Update the UI immediately
        self.root.update_idletasks()
    
    def next_hand(self):
        """Move all cards from dealer and player hands to wasted cards and prepare for next hand."""
        if not self.game:
            return
        
        # Move dealer's card to dealt cards if present
        if self.game.dealer_upcard:
            # Get card rank
            dealer_rank = self.game.dealer_upcard.rank
            
            # Add card to dealt cards
            self.game.add_dealt_card(dealer_rank + "S")  # Add dummy suit since game logic requires it
            
            # Create visual card in dealt area
            card = DraggableCard(self.dealt_drop_target.cards_frame, dealer_rank, self)
            card.pack(side="left", padx=2, pady=2)
        
        # Move player's cards to dealt cards
        for player_card in self.game.player_hand:
            # Get card rank
            rank = player_card.rank
            
            # Add card to dealt cards
            self.game.add_dealt_card(rank + "S")  # Add dummy suit since game logic requires it
            
            # Create visual card in dealt area
            card = DraggableCard(self.dealt_drop_target.cards_frame, rank, self)
            card.pack(side="left", padx=2, pady=2)
        
        # Reset player and dealer cards in game
        self.game.player_hand = []
        self.game.dealer_upcard = None
        
        # Clear dealer display
        for widget in self.dealer_drop_target.cards_frame.winfo_children():
            widget.destroy()
        
        # Clear player display
        for widget in self.player_drop_target.cards_frame.winfo_children():
            widget.destroy()
        
        # Reset recommendation
        self.recommendation_text.config(state="normal")
        self.recommendation_text.delete(1.0, tk.END)
        self.recommendation_text.insert(tk.END, "Recommendation will appear here when you add cards to your hand and the dealer's hand, then click 'Get Recommendation'.")
        self.recommendation_text.config(state="disabled")
        
        # Update card counts
        self.update_counts() 