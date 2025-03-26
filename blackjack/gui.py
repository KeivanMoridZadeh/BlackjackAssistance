"""
GUI module for the Blackjack Assistant.
Contains classes and functions for graphical user interface with drag-and-drop functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import speech_recognition as sr
import threading

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
        
        # Create a header frame for the text and voice button
        header_frame = ttk.Frame(self)
        header_frame.pack(side="top", fill="x", pady=5)
        
        # Create a label for the text
        self.label = ttk.Label(header_frame, text=text)
        self.label.pack(side="left", padx=5)
        
        # Add a voice button
        self.voice_button = ttk.Button(header_frame, text="🎤", width=3,
                                     command=lambda: parent.winfo_toplevel().gui.toggle_voice_recognition(target_type, self.voice_button))
        self.voice_button.pack(side="right", padx=5)
        
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
        
        # Voice recognition variables
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.current_voice_target = None
        self.current_voice_button = None
        
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
        
        # Left frame for game controls
        left_frame = ttk.Frame(panel)
        left_frame.pack(side="left", fill="x", expand=True)
        
        # Deck configuration
        ttk.Label(left_frame, text="Number of decks:").pack(side="left", padx=5)
        deck_spinner = ttk.Spinbox(left_frame, from_=1, to=8, width=5, textvariable=self.num_decks)
        deck_spinner.pack(side="left", padx=5)
        
        ttk.Button(left_frame, text="Set Decks", command=self.set_decks).pack(side="left", padx=5)
        ttk.Button(left_frame, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)
        ttk.Button(left_frame, text="Get Recommendation", command=self.get_recommendation).pack(side="left", padx=20)
        ttk.Button(left_frame, text="Next Hand", command=self.next_hand).pack(side="left", padx=5)
        
        # Right frame for voice recognition status
        right_frame = ttk.Frame(panel)
        right_frame.pack(side="right", fill="x", padx=10)
        
        # Voice recognition status
        self.voice_status_label = ttk.Label(right_frame, text="Voice Recognition: Click 🎤 buttons to use")
        self.voice_status_label.pack(side="right", padx=5)
        
        # Create a tooltip for voice usage
        self.create_tooltip(self.voice_status_label, 
                          "To use voice recognition:\n"
                          "1. Click the 🎤 button next to dealer, player, or wasted cards\n"
                          "2. Say a card value (e.g., 'two', 'ace', etc.)\n"
                          "3. The card will be added to the selected area")
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a given widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, justify="left",
                            background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
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
    
    def reset_target_labels(self):
        """Reset the labels of all drop targets after voice recognition is done."""
        self.dealer_drop_target.label.config(text="Dealer's Hand (Drop Cards Here)", foreground="black")
        self.player_drop_target.label.config(text="Your Hand (Drop Cards Here)", foreground="black")
        self.dealt_drop_target.label.config(text="Dealt/Wasted Cards (Drop Cards Here)", foreground="black")
        self.voice_status_label.config(text="Voice Recognition: Click 🎤 buttons to use", foreground="black")
        
        # Reset button appearance
        if hasattr(self, 'current_voice_button') and self.current_voice_button:
            self.current_voice_button.config(text="🎤")
            self.current_voice_button = None
    
    def toggle_voice_recognition(self, target_type, button):
        """
        Toggle voice recognition for a specific target.
        
        Args:
            target_type: The type of target ('dealer', 'player', or 'dealt')
            button: The voice button associated with the target
        """
        if self.is_listening:
            # Already listening, stop current session
            self.is_listening = False
            if hasattr(self, 'current_voice_button') and self.current_voice_button:
                self.current_voice_button.config(text="🎤")
            self.reset_target_labels()
            return
            
        self.current_voice_target = target_type
        self.current_voice_button = button
        self.is_listening = True
        
        # Update status label
        target_name = "Dealer" if target_type == "dealer" else "Player" if target_type == "player" else "Wasted Cards"
        self.voice_status_label.config(text=f"Voice Recognition: Listening for {target_name}...", foreground="red")
        
        # Show visual indicator that voice recognition is active
        if target_type == "dealer":
            self.dealer_drop_target.label.config(text="Dealer's Hand (Listening...)", foreground="red")
        elif target_type == "player":
            self.player_drop_target.label.config(text="Your Hand (Listening...)", foreground="red")
        else:  # dealt
            self.dealt_drop_target.label.config(text="Dealt/Wasted Cards (Listening...)", foreground="red")
        
        # Change button appearance
        button.config(text="⏹️")
        
        # Start voice recognition in a separate thread
        threading.Thread(target=self.listen_for_voice_commands, daemon=True).start()
    
    def listen_for_voice_commands(self):
        """Listen for voice commands and process them."""
        try:
            with sr.Microphone() as source:
                # Update status and show indicator that we're adjusting for ambient noise
                self.root.after(0, lambda: self.voice_status_label.config(
                    text="Voice Recognition: Adjusting for ambient noise...", foreground="blue"))
                
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Update status to show we're ready to listen
                target_name = "Dealer" if self.current_voice_target == "dealer" else "Player" if self.current_voice_target == "player" else "Wasted Cards"
                self.root.after(0, lambda: self.voice_status_label.config(
                    text=f"Voice Recognition: Listening for {target_name}...", foreground="red"))
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                        
                        # Show that we're processing speech
                        self.root.after(0, lambda: self.voice_status_label.config(
                            text="Voice Recognition: Processing speech...", foreground="orange"))
                        
                        text = self.recognizer.recognize_google(audio).lower()
                        print(f"Recognized: '{text}'")  # Debug output
                        
                        # Process the recognized text
                        success = self.process_voice_command(text)
                        
                        # Only stop listening if we successfully processed a command
                        if success:
                            self.is_listening = False
                            self.root.after(1000, self.reset_target_labels)  # Reset after 1 second to show feedback
                        
                    except sr.WaitTimeoutError:
                        # No speech detected within timeout
                        continue
                    except sr.UnknownValueError:
                        # Speech was unintelligible
                        self.root.after(0, lambda: self.voice_status_label.config(
                            text="Voice Recognition: Didn't understand, try again...", foreground="orange"))
                        continue
                    except Exception as e:
                        print(f"Error in voice recognition: {e}")
                        self.is_listening = False
                        self.root.after(0, lambda: self.reset_target_labels())
                        
        except Exception as e:
            print(f"Error initializing microphone: {e}")
            self.is_listening = False
            # Show error in status
            self.root.after(0, lambda: self.voice_status_label.config(
                text=f"Voice Recognition Error: {str(e)[:30]}...", foreground="red"))
            self.root.after(2000, self.reset_target_labels)  # Reset after 2 seconds
    
    def process_voice_command(self, text):
        """
        Process a voice command.
        
        Args:
            text: The recognized text from the voice command
        """
        # Map spoken words to card ranks
        card_mappings = {
            "two": "2", "2": "2", "to": "2", "too": "2",
            "three": "3", "3": "3", "tree": "3",
            "four": "4", "4": "4", "for": "4",
            "five": "5", "5": "5",
            "six": "6", "6": "6",
            "seven": "7", "7": "7",
            "eight": "8", "8": "8", "ate": "8",
            "nine": "9", "9": "9",
            "ten": "10", "10": "10",
            "jack": "10", "queen": "10", "king": "10",  # Face cards count as 10
            "ace": "A", "a": "A", "as": "A", "aces": "A"
        }
        
        # Find the matching card rank
        card_rank = None
        for word, rank in card_mappings.items():
            if word in text:
                card_rank = rank
                break
        
        if card_rank:
            # Show feedback that we recognized a card
            target_name = "Dealer" if self.current_voice_target == "dealer" else "Player" if self.current_voice_target == "player" else "Wasted Cards"
            self.root.after(0, lambda: self.voice_status_label.config(
                text=f"Voice Recognition: Adding {card_rank} to {target_name}", foreground="green"))
            
            # Use the GUI thread to update the UI
            if self.current_voice_target == "dealer":
                self.root.after(0, lambda: self.set_dealer_card(card_rank))
            elif self.current_voice_target == "player":
                self.root.after(0, lambda: self.add_to_player_hand(card_rank))
            else:  # dealt
                self.root.after(0, lambda: self.add_to_dealt_cards(card_rank))
        else:
            # No card recognized
            self.root.after(0, lambda: self.voice_status_label.config(
                text="Voice Recognition: No valid card recognized, try again", foreground="orange"))
            # Keep listening
            return False
        
        # Successfully processed a command
        return True 