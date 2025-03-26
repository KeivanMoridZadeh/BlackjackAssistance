# Blackjack Assistant

A Python-based Blackjack Assistant that helps players make optimal decisions using basic strategy and card counting techniques.

## Features

- Basic strategy recommendations
- Card counting system (Hi-Lo)
- Real-time probability calculations
- Support for 1-8 decks
- Visual card tracking
- Bust probability warnings
- Running and true count display
- Voice control for hands-free operation

## Requirements

- Python 3.6 or higher
- tkinter (usually comes with Python)
- SpeechRecognition
- PyAudio

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/KeivanMoridZadeh/PokerAssistance.git
   ```

2. Navigate to the project directory:

   ```
   cd PokerAssistance
   ```

3. Install required dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Run the application:

   ```
   python blackjack_assistant_gui.py
   ```

## Usage

1. Set the number of decks (1-8)
2. Add cards to your hand and the dealer's hand
3. Click "Get Recommendation" for optimal play advice
4. Use "Next Hand" to start a new hand
5. Track dealt cards in the "Dealt/Wasted Cards" section

### Voice Control

The application supports voice control for adding cards to different areas:

1. Click the microphone button (🎤) next to the dealer, player, or wasted cards area
2. Speak the card value (e.g., "two", "three", "ace", etc.)
3. The card will be automatically added to the selected area
4. To cancel voice input, click the square button (⏹️) that appears while listening

Supported voice commands include:
- Number words: "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"
- Face cards: "jack", "queen", "king" (all count as 10)
- Ace: "ace" or "a"

## Strategy Components

- Basic Strategy: Mathematically optimal play without counting
- Card Counting: Hi-Lo system for enhanced decision making
- Probability Calculations: Real-time bust probability warnings

## License

This project is licensed under the MIT License - see the LICENSE file for details.
