#!/usr/bin/env python3
"""
Hangman Game

A terminal-based hangman game using curses for display and WordNet dictionary data.

Usage: hangman.py -d <dictionary> [-l <logfile>]

References:
* Box Drawing - https://www.unicode.org/charts/PDF/U2500.pdf
* Dictionary -  https://wordnet.princeton.edu/download/current-version

Author: Justin Cook
"""

import argparse
import random
import curses
import logging
from typing import Dict, List, Callable, Optional, Tuple
from pathlib import Path

class HangmanDrawing:
    """Handles all hangman drawing operations using Unicode box drawing characters."""
    
    @staticmethod
    def gallows(stdscr) -> None:
        """Draw the gallows base structure.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(0, 0, "\u250F" + "\u2501" * 7 + "\u2513")
        for i in range(11):
            stdscr.addstr(i+1, 0, "\u2503")
        stdscr.addstr(12, 0, "\u2588" * 16)

    @staticmethod
    def head(stdscr) -> None:
        """Draw the hangman's head with a happy expression.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(1, 6, "\u256D\u2500\u2534\u2500\u256E")
        stdscr.addstr(2, 6, "\u2502\u25D5\u203F\u25D5\u2502")
        stdscr.addstr(3, 6, "\u2570\u2500\u2500\u2500\u256F")

    @staticmethod
    def neck(stdscr) -> None:
        """Draw the hangman's neck.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(3, 7, "\u252C\u2500\u252C")

    @staticmethod
    def torso(stdscr) -> None:
        """Draw the hangman's torso with sad expression.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(2, 6, "\u2502\u25D5\u005F\u25D5\u2502")
        stdscr.addstr(4, 5, "\u2500" * 2 + "\u2518")
        stdscr.addstr(4, 9, "\u2514" + "\u2500" * 2)
        stdscr.addstr(5, 6, "\u2577   \u2577")
        stdscr.addstr(6, 6, "\u2502\u2500\u2500\u2500\u2502")

    @staticmethod
    def right_arm(stdscr) -> None:
        """Draw the hangman's right arm.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(4, 4, "\u250C")
        stdscr.addstr(5, 4, "\u251C\u2500\u2510")
        stdscr.addstr(6, 4, "\u2502\u2574")
        stdscr.addstr(7, 5, "\u2509")

    @staticmethod
    def left_arm(stdscr) -> None:
        """Draw the hangman's left arm.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(4, 12, "\u2510")
        stdscr.addstr(5, 10, "\u250C\u2500\u2524")
        stdscr.addstr(6, 11, "\u2576\u2502")
        stdscr.addstr(7, 11, "\u2509")

    @staticmethod
    def right_leg(stdscr) -> None:
        """Draw the hangman's right leg.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(7, 6, "\u2502 \u257B")
        stdscr.addstr(8, 6, "\u2502 \u2502")
        stdscr.addstr(9, 6, "\u251C \u2524")

    @staticmethod
    def left_leg(stdscr) -> None:
        """Draw the hangman's left leg with worried expression.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(2, 6, "\u2502\u2576\u005F\u2574\u2502")
        stdscr.addstr(7, 10, "\u2502")
        stdscr.addstr(8, 10, "\u2502")
        stdscr.addstr(9, 10, "\u2524")

    @staticmethod
    def right_shoe(stdscr) -> None:
        """Draw the hangman's right shoe.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(9, 7, "\u2500")
        stdscr.addstr(10, 6, "\u2502\u250A\u2502")
        stdscr.addstr(11, 6, "\u2515\u2501\u2519")

    @staticmethod
    def left_shoe(stdscr) -> None:
        """Draw the hangman's left shoe with final expression.
        
        Args:
            stdscr: Curses screen object for drawing
        """
        stdscr.addstr(2, 6, "\u2502\u2A37\u2054\u2A37\u2502")
        stdscr.addstr(9, 8, "\u253C\u2500\u2524")
        stdscr.addstr(10, 9, "\u250A\u2502")
        stdscr.addstr(11, 8, "\u2537\u2501\u2519")


class GameError(Exception):
    """Custom exception for game-related errors."""
    pass


class DictionaryError(GameError):
    """Exception raised for dictionary-related errors."""
    pass

class HangmanGame:
    """Main game class that manages the hangman game state and logic."""
    
    # Game progression mapping incorrect guesses to drawing functions
    GAME_PROGRESSION: Dict[int, Callable] = {
        0: lambda stdscr: None,  # No drawing for 0 incorrect guesses
        1: HangmanDrawing.head,
        2: HangmanDrawing.neck,
        3: HangmanDrawing.torso,
        4: HangmanDrawing.right_arm,
        5: HangmanDrawing.left_arm,
        6: HangmanDrawing.right_leg,
        7: HangmanDrawing.left_leg,
        8: HangmanDrawing.right_shoe,
        9: HangmanDrawing.left_shoe
    }
    
    # Word type options for dictionary selection
    WORD_TYPES = {"Noun": "noun", "Verb": "verb", "Adjective": "adj", "Adverb": "adv"}
    
    def __init__(self, dictionary_path: str):
        """Initialize the hangman game.
        
        Args:
            dictionary_path: Path to the dictionary directory containing WordNet data files
        """
        self.dictionary_path = Path(dictionary_path)
        self.dictionaries: Dict[str, Dict[str, str]] = {}
        self.current_word: Optional[str] = None
        self.current_progress: List[str] = []
        self.current_definition: Optional[str] = None

    def read_dictionary(self, word_type: str) -> None:
        """Read and parse a WordNet dictionary file for the specified word type.
        
        Args:
            word_type: The type of words to load (noun, verb, adj, adv)
            
        Raises:
            FileNotFoundError: If the dictionary file doesn't exist
            IOError: If there's an error reading the file
        """
        if word_type in self.dictionaries:
            return  # Already loaded
            
        file_path = self.dictionary_path / f"data.{word_type}"
        if not file_path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {file_path}")
            
        self.dictionaries[word_type] = {}
        logging.debug(f"Reading {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line or not line[0].isdigit() or '|' not in line:
                        continue
                        
                    try:
                        parts = line.split('|', 1)
                        if len(parts) < 2:
                            continue
                            
                        word_data = parts[0].split()
                        if len(word_data) < 5:
                            continue
                            
                        word = word_data[4]
                        definition = parts[1].split(';')[0].strip()
                        
                        if word and definition:
                            self.dictionaries[word_type][word] = definition
                            
                    except (IndexError, ValueError) as e:
                        logging.debug(f"Skipping malformed line: {line} - {e}")
                        continue
                        
        except IOError as e:
            logging.error(f"Error reading dictionary file {file_path}: {e}")
            raise

    def update_word_progress(self, letter: str) -> bool:
        """Update the current word progress with correctly guessed letters.
        
        Args:
            letter: The letter that was guessed
            
        Returns:
            True if the letter was found in the word, False otherwise
        """
        if not self.current_word:
            return False
            
        found = False
        indices = [i for i, ch in enumerate(self.current_word) if letter.lower() == ch.lower()]
        
        for i in indices:
            self.current_progress[i] = letter.lower()
            found = True
            
        return found

    def is_word_complete(self) -> bool:
        """Check if the current word has been completely guessed.
        
        Returns:
            True if all letters have been guessed, False otherwise
        """
        return '_' not in self.current_progress

    def select_word_type(self, stdscr) -> str:
        """Display menu for selecting word type and return the selected type.
        
        Args:
            stdscr: Curses screen object
            
        Returns:
            Selected word type (noun, verb, adj, adv)
        """
        current_option = 0
        menu_items = list(self.WORD_TYPES.keys())
        
        while True:
            stdscr.clear()
            stdscr.addstr(2, 15, "Select word type:")
            
            for i, option in enumerate(menu_items):
                x, y = 15, 5 + i
                if i == current_option:
                    stdscr.addstr(y, x, f"> {option}", curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, f"  {option}")
            
            stdscr.addstr(12, 15, "Use arrow keys and Enter to select")
            stdscr.refresh()
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                current_option = (current_option - 1) % len(menu_items)
            elif key == curses.KEY_DOWN:
                current_option = (current_option + 1) % len(menu_items)
            elif key in (10, 13):  # Enter key
                selected_type = self.WORD_TYPES[menu_items[current_option]]
                logging.debug(f"Selected word type: {selected_type}")
                return selected_type
            elif key == 27:  # Escape key
                raise KeyboardInterrupt("User cancelled word selection")
    
    def get_random_word(self, stdscr) -> None:
        """Select a random word from the chosen dictionary category.
        
        Args:
            stdscr: Curses screen object for user interaction
        """
        try:
            selected_type = self.select_word_type(stdscr)
            
            if selected_type not in self.dictionaries:
                stdscr.clear()
                stdscr.addstr(10, 15, f"Loading {selected_type} dictionary...")
                stdscr.refresh()
                self.read_dictionary(selected_type)
            
            if not self.dictionaries[selected_type]:
                raise ValueError(f"No words found in {selected_type} dictionary")
            
            self.current_word = random.choice(list(self.dictionaries[selected_type].keys()))
            logging.info(f"Selected word: {self.current_word}")
            
            # Initialize progress with underscores, but preserve spaces
            self.current_progress = ['_' if c.isalpha() else c for c in self.current_word]
            # Pre-fill hyphens
            self.update_word_progress('-')
            # Pre-fill spaces
            self.update_word_progress(' ')
            
            self.current_definition = self.dictionaries[selected_type][self.current_word]
            
        except Exception as e:
            logging.error(f"Error selecting word: {e}")
            stdscr.clear()
            stdscr.addstr(10, 15, f"Error: {str(e)}")
            stdscr.addstr(12, 15, "Press any key to continue...")
            stdscr.refresh()
            stdscr.getch()
            raise

    def play_game(self, stdscr) -> bool:
        """Main game loop for playing a single word.
        
        Args:
            stdscr: Curses screen object
            
        Returns:
            True if the player won, False if they lost
        """
        if not self.current_word:
            raise ValueError("No word selected for gameplay")
            
        curses.curs_set(0)
        incorrect_guesses = 0
        guessed_letters = set()
        max_incorrect = len(self.GAME_PROGRESSION) - 1
        
        while incorrect_guesses < max_incorrect:
            stdscr.clear()
            
            # Draw gallows and current hangman state
            HangmanDrawing.gallows(stdscr)
            for i in range(1, incorrect_guesses + 1):
                if i in self.GAME_PROGRESSION:
                    self.GAME_PROGRESSION[i](stdscr)
            
            # Display game information
            stdscr.addstr(14, 0, f"Definition: {self.current_definition}")
            stdscr.addstr(16, 5, f"Word: {' '.join(self.current_progress)}")
            #stdscr.addstr(18, 0, f"Wrong guesses: {incorrect_guesses}/{max_incorrect}")
            
            if guessed_letters:
                sorted_guesses = sorted(list(guessed_letters))
                stdscr.addstr(19, 0, f"Guessed letters: {', '.join(sorted_guesses)}")
            
            stdscr.addstr(21, 0, "Enter a letter (or <esc> to quit): ")
            stdscr.refresh()
            
            # Check for win condition
            if self.is_word_complete():
                stdscr.addstr(23, 0, "Congratulations! You won!")
                logging.info(f"Player won with word: {self.current_word}")
                stdscr.getch()
                return True
            
            # Get player input
            try:
                key = stdscr.getch()
                if key == 27:  # ESC key
                    stdscr.addstr(24, 0, "Are you sure you want to quit? (y/n): ")
                    stdscr.refresh()
                    confirm = stdscr.getch()
                    if confirm in (ord('y'), ord('Y')):
                        return False
                    else:
                        continue
                if key == ord('q') or key == ord('Q'):
                    continue
                    
                if 32 <= key <= 126:  # Printable ASCII characters
                    letter = chr(key).lower()
                    
                    if not letter.isalpha():
                        continue
                        
                    if letter in guessed_letters:
                        stdscr.addstr(23, 0, f"You already guessed '{letter}'!")
                        stdscr.refresh()
                        curses.napms(1500)
                        continue
                    
                    guessed_letters.add(letter)
                    
                    if self.update_word_progress(letter):
                        stdscr.addstr(23, 0, f"Good guess! '{letter}' is in the word.")
                    else:
                        incorrect_guesses += 1
                        stdscr.addstr(23, 0, f"Sorry, '{letter}' is not in the word.")
                    
                    stdscr.refresh()
                    curses.napms(1500)
                    
            except KeyboardInterrupt:
                return False
        
        # Game over - player lost
        stdscr.clear()
        HangmanDrawing.gallows(stdscr)
        
        # Draw complete hangman
        for i in range(1, len(self.GAME_PROGRESSION)):
            self.GAME_PROGRESSION[i](stdscr)
        
        stdscr.addstr(14, 0, f"Game Over! The word was: {self.current_word}")
        stdscr.addstr(15, 0, f"Definition: {self.current_definition}")
        stdscr.addstr(17, 0, "Press any key to continue...")
        stdscr.refresh()
        logging.info(f"Player lost with word: {self.current_word}")
        stdscr.getch()
        return False

def main(stdscr, args: argparse.Namespace) -> None:
    """Main game loop that runs continuously until the user quits.
    
    Args:
        stdscr: Curses screen object
        args: Parsed command line arguments
    """
    try:
        game = HangmanGame(args.dictionary)
        
        while True:
            try:
                game.get_random_word(stdscr)
                won = game.play_game(stdscr)
                
                # Ask if player wants to play again
                stdscr.clear()
                if won:
                    stdscr.addstr(10, 15, "Congratulations! You won!")
                else:
                    stdscr.addstr(10, 15, "Better luck next time!")
                    
                stdscr.addstr(12, 15, "Play again? (y/n): ")
                stdscr.refresh()
                
                while True:
                    key = stdscr.getch()
                    if key in (ord('n'), ord('N'), ord('q'), ord('Q')):
                        return
                    elif key in (ord('y'), ord('Y'), 10, 13):  # y, Y, Enter
                        break
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Game error: {e}")
                stdscr.clear()
                stdscr.addstr(10, 15, f"An error occurred: {str(e)}")
                stdscr.addstr(12, 15, "Press any key to continue...")
                stdscr.refresh()
                stdscr.getch()
                
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        stdscr.clear()
        stdscr.addstr(10, 15, f"Fatal error: {str(e)}")
        stdscr.addstr(12, 15, "Press any key to exit...")
        stdscr.refresh()
        stdscr.getch()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Terminal-based Hangman game using WordNet dictionary data",
        epilog="Example: python hangman.py -d /path/to/wordnet/dict"
    )
    parser.add_argument(
        "-d", "--dictionary", 
        required=True,
        help="Path to the WordNet dictionary directory containing data files"
    )
    parser.add_argument(
        "-l", "--logfile", 
        default="logfile.log",
        help="Path to the log file (default: logfile.log)"
    )
    
    args = parser.parse_args()
    
    # Validate dictionary path
    dict_path = Path(args.dictionary)
    if not dict_path.exists() or not dict_path.is_dir():
        print(f"Error: Dictionary directory '{args.dictionary}' does not exist")
        exit(1)
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        filename=args.logfile,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'
    )
    
    logging.info("Starting Hangman game")
    
    try:
        curses.wrapper(main, args)
    except KeyboardInterrupt:
        logging.info("Game interrupted by user")
        print("\nGame interrupted. Goodbye!")
        exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"\nAn unexpected error occurred: {e}")
        exit(1)
    finally:
        logging.info("Hangman game ended")
