"""
GUI module for the Blackjack Assistant.
Contains classes and functions for graphical user interface with drag-and-drop functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import json
import queue
import sounddevice as sd
import numpy as np
import vosk
import threading
import os

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
    
    def __init__(self, parent, target_type, text, width=300, height=150):
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
        header_frame.pack(side="top", fill="x", pady=2)  # Reduced padding
        
        # Create a label for the text
        self.label = ttk.Label(header_frame, text=text)
        self.label.pack(side="left", padx=2)  # Reduced padding
        
        # Add a voice button
        self.voice_button = ttk.Button(header_frame, text="🎤", width=2,  # Narrower button
                                     command=lambda: parent.winfo_toplevel().gui.toggle_voice_recognition(target_type, self.voice_button))
        self.voice_button.pack(side="right", padx=2)  # Reduced padding
        
        # Create a frame for the cards with reduced height
        self.cards_frame = ttk.Frame(self, width=width, height=height, relief="sunken", borderwidth=1)
        self.cards_frame.pack(fill="both", expand=True, padx=2, pady=2)  # Reduced padding
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
        """Update the display of cards in this target with grid layout."""
        # Clear existing card labels
        for label in self.card_labels:
            label.destroy()
        self.card_labels.clear()
        
        # Special handling for dealer and player
        if self.target_type == "dealer" or self.target_type == "player":
            # Create new card labels (horizontally aligned)
            for i, rank in enumerate(self.cards):
                label = ttk.Label(self.cards_frame, text=rank, relief="raised", borderwidth=1, width=2)  # Narrower label
                label.place(x=5 + i*35, y=5)  # Reduced spacing between cards
                self.card_labels.append(label)
            return
        
        # For dealt/wasted cards only - use strict grid placement
        # Card dimensions and spacing
        card_width = 25  # Smaller card width
        card_height = 22  # Smaller card height
        h_spacing = 3  # Reduced spacing
        v_spacing = 3  # Reduced spacing
        left_margin = 3  # Reduced margin
        top_margin = 3  # Reduced margin
        
        # Force update to get correct dimensions
        self.cards_frame.update_idletasks()
        frame_width = self.cards_frame.winfo_width()
        
        # Calculate cards per row
        usable_width = frame_width - (2 * left_margin)
        cards_per_row = max(1, usable_width // (card_width + h_spacing))
        
        # Create new card labels in grid layout
        for i, rank in enumerate(self.cards):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = left_margin + col * (card_width + h_spacing)
            y = top_margin + row * (card_height + v_spacing)
            
            label = ttk.Label(self.cards_frame, text=rank, relief="raised", borderwidth=1, width=2)  # Narrower label
            # Place anchored at northwest (top-left)
            label.place(x=x, y=y, anchor="nw")
            self.card_labels.append(label)

    def clear(self):
        """Clear all cards from this target."""
        # First clear any cards in the internal list
        self.cards.clear()
        
        # Clear card labels list
        for label in self.card_labels:
            label.destroy()
        self.card_labels.clear()
        
        # Also destroy any direct children of the cards_frame (DraggableCards)
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
            
        # Update display to ensure all cards are removed
        self.update_display()

class CardCountDisplay(ttk.Frame):
    """Display for card counting information."""
    
    def __init__(self, parent):
        """Initialize the card count display."""
        super().__init__(parent)
        
        # Create labels for counts with reduced text and spacing
        ttk.Label(self, text="Run:").pack(side="left", padx=2)  # Shorter text
        self.running_count_label = ttk.Label(self, text="0", width=3, relief="sunken")  # Narrower
        self.running_count_label.pack(side="left", padx=2)  # Reduced padding
        
        ttk.Label(self, text="True:").pack(side="left", padx=2)  # Shorter text
        self.true_count_label = ttk.Label(self, text="0.0", width=4, relief="sunken")  # Narrower
        self.true_count_label.pack(side="left", padx=2)  # Reduced padding
        
        ttk.Label(self, text="Bust:").pack(side="left", padx=2)  # Shorter text
        self.bust_prob_label = ttk.Label(self, text="0%", width=3, relief="sunken")  # Narrower
        self.bust_prob_label.pack(side="left", padx=2)  # Reduced padding
    
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
        self.root.title("Blackjack Assistant - Enhanced Strategy")
        self.root.geometry("1000x700")  # Smaller default size
        self.root.resizable(True, True)
        
        # Store reference to GUI in root for access from DraggableCard
        self.root.gui = self
        
        # Set theme and style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=3)  # Reduced padding
        self.style.configure("TLabel", padding=3)   # Reduced padding
        self.style.configure("TFrame", padding=2)   # Reduced padding
        
        # Define card ranks (J, Q, K are value 10 but tracked separately)
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        
        # Variables
        self.num_decks = tk.IntVar(value=1)
        
        # Card counts dictionary to track remaining cards
        self.card_counts = {}
        
        # Initialize speech recognition
        self.is_listening = False
        self.active_target = None
        self.listen_thread = None
        self.audio_queue = queue.Queue()
        
        # Initialize Vosk model
        try:
            model_path = "vosk-model-small-en-us-0.15"
            if not os.path.exists(model_path):
                self.update_status("Downloading Vosk model...")
                import urllib.request
                import zipfile
                import io
                
                url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
                response = urllib.request.urlopen(url)
                with zipfile.ZipFile(io.BytesIO(response.read())) as zip_ref:
                    zip_ref.extractall(".")
                
            self.model = vosk.Model(model_path)
            self.update_status("Vosk model loaded successfully")
        except Exception as e:
            self.update_status(f"Error loading Vosk model: {str(e)}")
            self.model = None
        
        # Card number mapping with fuzzy matching
        self.card_numbers = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'ace': 'A', 'king': 'K', 'queen': 'Q', 'jack': 'J',
            'first': 'A'  # Add "first" as a clear alternative for "ace"
        }
        
        # Alternative pronunciations with similarity scores
        self.card_alternatives = {
            'for': ('4', 0.8), 'tree': ('3', 0.9), 'free': ('3', 0.8),
            'too': ('2', 0.9), 'to': ('2', 0.8), 'won': ('1', 0.9),
            'ate': ('8', 0.9), 'sicks': ('6', 0.8), 'sex': ('6', 0.7),
            'heaven': ('7', 0.7), 'tin': ('10', 0.8), 'tan': ('10', 0.8),
            'is': ('A', 0.8), 'hey': ('A', 0.7), 'aids': ('A', 0.7),
            'space': ('A', 0.9), 'base': ('A', 0.8), 'case': ('A', 0.8),
            'face': ('A', 0.9), 'place': ('A', 0.8), 'number one': ('A', 0.95),
            'as': ('A', 0.8), 'first card': ('A', 0.95), 'one card': ('A', 0.9),
            'check': ('J', 0.8), 'queen': ('Q', 0.9), 'king': ('K', 0.9)
        }
        
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
        panel.pack(fill="x", padx=5, pady=2)  # Reduced padding
        
        # Left frame for game controls
        left_frame = ttk.Frame(panel)
        left_frame.pack(side="left", fill="x", expand=True)
        
        # Deck configuration
        ttk.Label(left_frame, text="Decks:").pack(side="left", padx=2)  # Shorter label
        deck_spinner = ttk.Spinbox(left_frame, from_=1, to=8, width=3, textvariable=self.num_decks)  # Narrower
        deck_spinner.pack(side="left", padx=2)  # Reduced padding
        
        ttk.Button(left_frame, text="Set", command=self.set_decks, width=4).pack(side="left", padx=2)  # Shorter text
        ttk.Button(left_frame, text="Reset", command=self.reset_game, width=5).pack(side="left", padx=2)  # Shorter text
        ttk.Button(left_frame, text="Recommend", command=self.get_recommendation, width=10).pack(side="left", padx=2)  # Shorter text
        ttk.Button(left_frame, text="Next", command=self.next_hand, width=5).pack(side="left", padx=2)  # Shorter text
        
        # Right frame for voice recognition status
        right_frame = ttk.Frame(panel)
        right_frame.pack(side="right", fill="x", padx=5)
        
        # Voice recognition status
        self.voice_status_label = ttk.Label(right_frame, text="Voice: Click 🎤")  # Shorter text
        self.voice_status_label.pack(side="right", padx=2)
        
        # Create a tooltip for voice usage
        self.create_tooltip(self.voice_status_label, 
                          "To use voice recognition:\n"
                          "1. Click 🎤 next to dealer, player, or wasted cards\n"
                          "2. Say a card value (e.g., 'two', 'ace', etc.)\n"
                          "3. The card will be added to selected area")
    
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
        workspace.pack(fill="both", padx=5, pady=2, expand=True)  # Reduced padding
        
        # Create split panes
        paned_window = ttk.PanedWindow(workspace, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
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
        recommendation_frame.pack(fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
        # Text area for recommendation display with smaller size
        self.recommendation_text = scrolledtext.ScrolledText(recommendation_frame, height=4, width=70, wrap=tk.WORD, 
                                                          font=("Arial", 9))  # Smaller font and height
        self.recommendation_text.pack(fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        self.recommendation_text.insert(tk.END, "Recommendation will appear here when you add cards.")
        self.recommendation_text.config(state="disabled")
        
        # Create card count display
        self.count_display = CardCountDisplay(left_panel)
        self.count_display.pack(fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
        # Create drop targets in right panel with smaller dimensions
        self.dealer_drop_target = DropTarget(right_panel, "dealer", "Dealer's Hand", 
                                           width=380, height=100)  # Smaller dimensions, shorter text
        self.dealer_drop_target.pack(side="top", fill="x", padx=2, pady=2)  # Reduced padding
        
        # Create a frame for player and dealt cards side by side
        card_areas = ttk.Frame(right_panel)
        card_areas.pack(fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
        self.player_drop_target = DropTarget(card_areas, "player", "Your Hand", 
                                           width=180, height=130)  # Smaller dimensions, shorter text
        self.player_drop_target.pack(side="left", fill="both", expand=True, padx=2, pady=2)  # Reduced padding
        
        self.dealt_drop_target = DropTarget(card_areas, "dealt", "Wasted Cards", 
                                          width=180, height=130)  # Smaller dimensions, shorter text
        self.dealt_drop_target.pack(side="right", fill="both", expand=True, padx=2, pady=2)  # Reduced padding
    
    def create_card_source_panel(self, parent):
        """
        Create a panel with all available cards in three columns.
        
        Args:
            parent: The parent widget
        """
        card_source = ttk.LabelFrame(parent, text="Available Cards")  # Shorter text
        card_source.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        # Create a frame for the three columns
        columns_frame = ttk.Frame(card_source)
        columns_frame.pack(fill="both", padx=2, pady=2)  # Reduced padding
        
        # Create three columns
        dealer_column = ttk.LabelFrame(columns_frame, text="Dealer")  # Shorter text
        dealer_column.pack(side="left", fill="both", expand=True, padx=2)  # Reduced padding
        
        player_column = ttk.LabelFrame(columns_frame, text="Player")  # Shorter text
        player_column.pack(side="left", fill="both", expand=True, padx=2)  # Reduced padding
        
        wasted_column = ttk.LabelFrame(columns_frame, text="Wasted")  # Shorter text
        wasted_column.pack(side="left", fill="both", expand=True, padx=2)  # Reduced padding
        
        # Create cards in each column with reduced spacing
        for rank_idx, rank in enumerate(self.ranks):
            # Dealer column
            dealer_card = ttk.Label(dealer_column, text=rank, relief="raised", borderwidth=1)
            dealer_card.grid(row=rank_idx, column=0, padx=1, pady=1)  # Reduced padding
            dealer_card.bind("<Button-1>", lambda e, r=rank: self.set_dealer_card(r))
            
            # Player column
            player_card = ttk.Label(player_column, text=rank, relief="raised", borderwidth=1)
            player_card.grid(row=rank_idx, column=0, padx=1, pady=1)  # Reduced padding
            player_card.bind("<Button-1>", lambda e, r=rank: self.add_to_player_hand(r))
            
            # Wasted column
            wasted_card = ttk.Label(wasted_column, text=rank, relief="raised", borderwidth=1)
            wasted_card.grid(row=rank_idx, column=0, padx=1, pady=1)  # Reduced padding
            wasted_card.bind("<Button-1>", lambda e, r=rank: self.add_to_dealt_cards(r))
    
    def create_recommendation_panel(self):
        """Create the panel for displaying recommendations."""
        # This method is no longer needed as the recommendation panel is now created in create_workspace
        pass
    
    def create_card_tracking_panel(self):
        """Create the panel for tracking cards and counts."""
        panel = ttk.Frame(self.root)
        panel.pack(fill="x", padx=5, pady=2)  # Reduced padding
        
        # Create a frame for running count and true count
        counts_frame = ttk.LabelFrame(panel, text="Card Counting")
        counts_frame.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        count_info = ttk.Frame(counts_frame)
        count_info.pack(fill="x", padx=2, pady=2)  # Reduced padding
        
        ttk.Label(count_info, text="Run Count:").grid(row=0, column=0, padx=2, pady=1, sticky="w")  # Shorter text
        self.running_count_label = ttk.Label(count_info, text="0", width=4, 
                                           background="white", relief="sunken")
        self.running_count_label.grid(row=0, column=1, padx=2, pady=1)  # Reduced padding
        
        ttk.Label(count_info, text="True Count:").grid(row=0, column=2, padx=10, pady=1, sticky="w")  # Shorter text
        self.true_count_label = ttk.Label(count_info, text="0.0", width=4, 
                                        background="white", relief="sunken")
        self.true_count_label.grid(row=0, column=3, padx=2, pady=1)  # Reduced padding
        
        ttk.Label(count_info, text="Bust Prob:").grid(row=0, column=4, padx=10, pady=1, sticky="w")  # Shorter text
        self.bust_prob_label = ttk.Label(count_info, text="0%", width=4, 
                                        background="white", relief="sunken")
        self.bust_prob_label.grid(row=0, column=5, padx=2, pady=1)  # Reduced padding
    
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
                # For 10, we count just the numeric 10 cards (not face cards)
                self.card_counts[rank] = deck_count * 4  # 1 card × 4 suits
            else:
                self.card_counts[rank] = deck_count * 4  # 1 card × 4 suits
        
        # Add face cards (J, Q, K) - each has 4 cards per deck
        self.card_counts["J"] = deck_count * 4
        self.card_counts["Q"] = deck_count * 4
        self.card_counts["K"] = deck_count * 4
        
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
        self.recommendation_text.insert(tk.END, "Recommendation will appear here when you add cards.")
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
                
                # Add to the DropTarget's cards list and update display
                self.dealt_drop_target.add_card(rank)
                
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
            
            # Add to the wasted cards display
            self.dealt_drop_target.add_card(dealer_rank)
        
        # Move player's cards to dealt cards
        for player_card in self.game.player_hand:
            # Get card rank
            rank = player_card.rank
            
            # Add card to dealt cards
            self.game.add_dealt_card(rank + "S")  # Add dummy suit since game logic requires it
            
            # Add to the wasted cards display
            self.dealt_drop_target.add_card(rank)
        
        # Reset player and dealer cards in game
        self.game.player_hand = []
        self.game.dealer_upcard = None
        
        # Clear dealer display
        self.dealer_drop_target.clear()
        
        # Clear player display
        self.player_drop_target.clear()
        
        # Reset recommendation
        self.recommendation_text.config(state="normal")
        self.recommendation_text.delete(1.0, tk.END)
        self.recommendation_text.insert(tk.END, "Recommendation will appear here when you add cards.")
        self.recommendation_text.config(state="disabled")
        
        # Update card counts
        self.update_counts()
    
    def reset_target_labels(self):
        """Reset the labels of all drop targets after voice recognition is done."""
        self.dealer_drop_target.label.config(text="Dealer's Hand", foreground="black")
        self.player_drop_target.label.config(text="Your Hand", foreground="black")
        self.dealt_drop_target.label.config(text="Wasted Cards", foreground="black")
        self.voice_status_label.config(text="Voice: Click 🎤", foreground="black")
        
        # Reset button appearance
        if hasattr(self, 'current_voice_button') and self.current_voice_button:
            self.current_voice_button.config(text="🎤")
            self.current_voice_button = None
    
    def toggle_voice_recognition(self, target_type, button):
        """Toggle voice recognition on/off."""
        if not self.is_listening:
            self.start_listening(target_type, button)
        else:
            self.stop_listening(button)

    def start_listening(self, target_type, button):
        """Start continuous voice recognition using Vosk."""
        if not self.model:
            self.update_status("Error: Vosk model not loaded")
            return
            
        self.is_listening = True
        self.active_target = target_type
        button.configure(text="⏹️", style="Listening.TButton")
        
        # Create and start listening thread
        self.listen_thread = threading.Thread(target=self.continuous_listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        # Update status
        self.update_status("Listening for cards... (Say 'stop' to end)")

    def stop_listening(self, button):
        """Stop voice recognition."""
        self.is_listening = False
        self.active_target = None
        button.configure(text="🎤", style="TButton")
        self.voice_status_label.config(text="Voice recognition stopped")

    def continuous_listen(self):
        """Continuously listen for card commands using Vosk."""
        try:
            # Audio parameters
            sample_rate = 16000
            channels = 1
            dtype = np.int16
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Status: {status}")
                self.audio_queue.put(indata.copy())
            
            with sd.InputStream(samplerate=sample_rate, channels=channels, dtype=dtype, callback=audio_callback):
                rec = vosk.KaldiRecognizer(self.model, sample_rate)
                
                while self.is_listening:
                    try:
                        # Get audio data from queue
                        audio_data = self.audio_queue.get()
                        
                        # Process audio with Vosk
                        if rec.AcceptWaveform(audio_data.tobytes()):
                            result = json.loads(rec.Result())
                            text = result.get("text", "").lower()
                            
                            # Check for stop command
                            if 'stop' in text:
                                self.root.after(0, self.stop_listening, self.find_active_button())
                                break
                            
                            # Process multiple cards in one phrase
                            words = text.split()
                            for word in words:
                                card = self.process_card_word(word)
                                if card:
                                    self.root.after(0, self.add_card_from_voice, card)
                                    self.root.after(0, self.update_status, f"Added card: {card}")
                    
                    except Exception as e:
                        print(f"Error in audio processing: {e}")
                        continue
                        
        except Exception as e:
            self.root.after(0, self.update_status, f"Error: {str(e)}")
            self.root.after(0, self.stop_listening, self.find_active_button())

    def process_card_word(self, word):
        """Process a word to determine if it's a valid card value using fuzzy matching."""
        word = word.lower().strip()
        
        # Check direct matches
        if word in self.card_numbers:
            return self.card_numbers[word]
            
        # Check alternative pronunciations with similarity scores
        best_match = None
        best_score = 0
        
        for alt, (card, score) in self.card_alternatives.items():
            # Calculate Levenshtein distance
            distance = self.levenshtein_distance(word, alt)
            similarity = 1 - (distance / max(len(word), len(alt)))
            
            # Combine with predefined similarity score
            combined_score = (similarity + score) / 2
            
            if combined_score > best_score and combined_score > 0.6:  # Threshold for matching
                best_score = combined_score
                best_match = card
        
        if best_match:
            return best_match
            
        # Check if the word is already a valid card value
        if word in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'a', 'j', 'q', 'k']:
            return word.upper()
            
        return None

    def levenshtein_distance(self, s1, s2):
        """Calculate the Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def add_card_from_voice(self, card):
        """Add a card based on voice recognition."""
        try:
            if self.active_target == "dealer":
                self.set_dealer_card(card)
            elif self.active_target == "player":
                self.add_to_player_hand(card)
            elif self.active_target == "dealt":
                self.add_to_dealt_cards(card)
        except Exception as e:
            self.update_status(f"Error adding card: {str(e)}")

    def update_status(self, message):
        """Update the status label."""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
        else:
            print(f"Status: {message}")  # Fallback to console output

    def find_active_button(self):
        """Find the currently active voice button."""
        if self.active_target == "dealer":
            return self.dealer_drop_target.voice_button
        elif self.active_target == "player":
            return self.player_drop_target.voice_button
        elif self.active_target == "dealt":
            return self.dealt_drop_target.voice_button
        return None 