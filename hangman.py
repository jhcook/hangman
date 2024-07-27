#!/usr/bin/env python3
"""
Hangman

Usage: hangman.py -w <dictionary>

References:
* Box Drawing - https://www.unicode.org/charts/PDF/U2500.pdf
* Dictionary -  https://wordnet.princeton.edu/download/current-version

Author: Justin Cook
"""

import argparse
import random
import curses
import logging

def gallows(stdscr):
    """Draw the gallows"""
    stdscr.addstr(0, 0, "\u250F" + "\u2501" * 7 + "\u2513")
    for i in range(11):
        stdscr.addstr(i+1, 0, "\u2503")
    stdscr.addstr(12, 0, "\u2588" * 16)

def head(stdscr):
    """Draw the head"""
    stdscr.addstr(1, 6, "\u256D\u2500\u2534\u2500\u256E")
    stdscr.addstr(2, 6, "\u2502\u25D5\u203F\u25D5\u2502")
    stdscr.addstr(3, 6, "\u2570\u2500\u2500\u2500\u256F")

def neck(stdscr):
    """Draw the neck"""
    stdscr.addstr(3, 7, "\u252C\u2500\u252C")

def torso(stdscr):
    """Draw the torso"""
    stdscr.addstr(4, 5, "\u2500" * 2 + "\u2518")
    stdscr.addstr(4, 9, "\u2514" + "\u2500" * 2)
    stdscr.addstr(5, 6, "\u2577   \u2577")
    stdscr.addstr(6, 6, "\u2502\u2500\u2500\u2500\u2502")

def right_arm(stdscr):
    """Draw the right arm"""
    stdscr.addstr(4, 4, "\u250C")
    stdscr.addstr(5, 4, "\u251C\u2500\u2510")
    stdscr.addstr(6, 4, "\u2502\u2574")
    stdscr.addstr(7, 5, "\u2509")

def left_arm(stdscr):
    """Draw the left arm"""
    stdscr.addstr(4, 12, "\u2510")
    stdscr.addstr(5, 10, "\u250C\u2500\u2524")
    stdscr.addstr(6, 11, "\u2576\u2502")
    stdscr.addstr(7, 11, "\u2509")

def right_leg(stdscr):
    """Draw the right leg"""
    stdscr.addstr(7, 6, "\u2502 \u257B")
    stdscr.addstr(8, 6, "\u2502 \u2502")
    stdscr.addstr(9, 6, "\u251C \u2524")

def left_leg(stdscr):
    """Draw the left leg"""
    stdscr.addstr(7, 10, "\u2502")
    stdscr.addstr(8, 10, "\u2502")
    stdscr.addstr(9, 10, "\u2524")

def right_shoe(stdscr):
    """Draw the right shoe"""
    stdscr.addstr(9, 7, "\u2500")
    stdscr.addstr(10, 6, "\u2502\u250A\u2502")
    stdscr.addstr(11, 6, "\u2515\u2501\u2519")

def left_shoe(stdscr):
    """Draw the left shoe"""
    stdscr.addstr(9, 8, "\u253C\u2500\u2524")
    stdscr.addstr(10, 9, "\u250A\u2502")
    stdscr.addstr(11, 8, "\u2537\u2501\u2519")

GAME = {
    0: lambda x: x,
    1: head,
    2: neck,
    3: torso,
    4: right_arm,
    5: left_arm,
    6: right_leg,
    7: left_leg,
    8: right_shoe,
    9: left_shoe
}

DICTIONARY = {}
THE_WORD = None
CURRENT = None
THE_DEFO = None

def read_dictionary(dictionary, selected):
    """Read the dictionary"""
    global DICTIONARY
    DICTIONARY[selected] = {}
    with open(f"{dictionary}/data.{selected}", 'r', encoding='utf-8') as d:
        logging.debug(f"Reading {dictionary}/data.{selected}")
        while True:
            line = d.readline()
            if not line:
                break
            try:
                if line[0].isdigit() and '|' in line:
                    rubbish, defo = line.split('|')
                    wrd  = rubbish.split()[4]
                    defo = line.split('|')[1]
                DICTIONARY[selected][wrd] = defo
            except (IndexError, UnboundLocalError):
                pass

def update_word(ltr):
    """Print out THE_WORD with chars that match `ltr`"""
    global CURRENT, THE_WORD
    indices = [i for i, ch in enumerate(THE_WORD) if ltr == ch]
    for i in indices:
        CURRENT[i] = ltr

def word_finished():
    """Return True if all letters guessed"""
    global CURRENT
    for char in CURRENT:
        if char != ' ' and char == '_':
            return False
    return True

def get_word(stdscr, dictionary):
    """Get a word and definition from the dictionary"""
    global DICTIONARY, CURRENT, THE_DEFO, THE_WORD
    menu = {"Noun": "noun", "Verb": "verb", "Adjective": "adj", "Adverb": "adv"}
    current_option = 0

    #stdscr.clear()
    while True:
        for i, option in enumerate(menu.keys()):
            x = 15
            y = 5 + i
            if i == current_option:
                stdscr.addstr(y, x, option, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)

        # Get user input
        key = stdscr.getch()

        # Handle arrow keys
        if key == curses.KEY_UP:
            current_option = (current_option - 1) % len(menu.keys())
        elif key == curses.KEY_DOWN:
            current_option = (current_option + 1) % len(menu.keys())
        elif key == 10:  # Enter key
            selected = menu[list(menu.keys())[current_option]]
            logging.debug(f"Selected: {selected}")
            stdscr.clear()
            break

    if selected not in DICTIONARY:
        read_dictionary(dictionary, selected)

    THE_WORD = random.choice(list(DICTIONARY[selected].keys()))
    logging.info(f"Word: {THE_WORD}")
    CURRENT = ['_' if c != '_' else ' ' for c in THE_WORD]
    THE_DEFO = DICTIONARY[selected][THE_WORD].split(';')[0].strip()

def play_word(stdscr):
    """Play the word"""
    global DICTIONARY, THE_WORD, CURRENT, THE_DEFO

    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    gallows(stdscr)
    stdscr.addstr(14, 0, THE_DEFO)
    stdscr.addstr(16, 5, "".join(CURRENT))

    break_out = False
    for i in range(len(GAME.keys())):
        GAME[i](stdscr)
        if i >= len(GAME.keys()) - 1:
            break
        while True:
            letter = stdscr.getch()
            if chr(letter) not in THE_WORD:
                break
            update_word(chr(letter))
            stdscr.addstr(16, 5, "".join(CURRENT))
            if word_finished():
                logging.info(f"Guessed word: {''.join(CURRENT)}")
                break_out = True
                break
        if break_out:
            break

    stdscr.addstr(16, 5, THE_WORD.replace("_", " "))
    stdscr.getch()

def main(stdscr, cargs):
    """Play the game"""
    while True:
        get_word(stdscr, cargs.dictionary)
        play_word(stdscr)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Play Hangman")
    parser.add_argument("-d", "--dictionary", required=True,
                        help="Path to the dictionary directory")
    parser.add_argument("-l", "--logfile", required=False, default="logfile.log",
                        help="Path to the logfile")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, filename=f"{args.logfile}")

    try:
        curses.wrapper(main, args)
    except KeyboardInterrupt:
        exit(0)
