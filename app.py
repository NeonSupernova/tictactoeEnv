import subprocess
import os
import tomllib
from enum import Enum

class Tokens(Enum):
    X = "X"
    O = "O"
    EMPTY = "E"


def ls_exec(directory):
    """ List bot folders in a given directory. """
    bot_folders = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            bot_folders.append(entry)
    return bot_folders


class Bot:
    def __init__(self, bot_folder: str):
        """ Initialize the bot with its folder path and configuration. """
        self.bot_folder = bot_folder
        self.bot_config = self.load_config()
        self.bot_path = os.path.join(bot_folder, self.bot_config['bot']['run'].split()[0])  # Assuming first word in 'run' is the command
        self.process = None
        self.symbol = None
        self.__doc__ = self.load_readme()

    def load_config(self):
        """ Load the bot's configuration from its toml file. """
        config_path = os.path.join(self.bot_folder, "config.toml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found for bot: {self.bot_folder}")
        with open(config_path, 'rb') as fp:
            return tomllib.load(fp)

    def load_readme(self):
        """ Load the bot's README into a docstring if it exists. """
        readme_path = os.path.join(self.bot_folder, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, 'r') as f:
                return f.read()
        return ""

    def start(self, bot_symbol: Tokens):
        """ Start the bot's subprocess using the 'run' command from its config. """
        self.symbol = bot_symbol
        run_command = self.bot_config['bot']['run'].split()
        self.process = subprocess.Popen(
            run_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            cwd=self.bot_folder  # Ensure subprocess runs in the correct directory
        )

    def make_move(self, board: "Board") -> int:
        """ Send the board state to the bot and retrieve its move. """
        if not self.process:
            raise Exception(f"Bot {self.bot_folder} is not started.")

        # Send board state to bot
        self.process.stdin.write(f"{board.board_state}\n")
        self.process.stdin.flush()

        # Get the move from bot
        move = self.process.stdout.readline().strip()
        return int(move)

    def stop(self):
        """ Terminate the bot's subprocess. """
        if self.process:
            self.process.terminate()
            self.process = None


class Board:
    def __init__(self):
        """ Initialize the tic-tac-toe board. """
        self.board = [Tokens.EMPTY for _ in range(9)]  # Empty board with 9 cells

    def display(self):
        """ Display the current board state. """
        print(f"{self.board[0].value} | {self.board[1].value} | {self.board[2].value}")
        print("-" * 9)
        print(f"{self.board[3].value} | {self.board[4].value} | {self.board[5].value}")
        print("-" * 9)
        print(f"{self.board[6].value} | {self.board[7].value} | {self.board[8].value}")

    def is_valid_move(self, move: int) -> bool:
        """ Check if the move is valid (within bounds and on an empty space). """
        return 0 <= move < 9 and self.board[move] == Tokens.EMPTY

    def place_move(self, move: int, symbol: Tokens):
        """ Place the player's move on the board. """
        if self.is_valid_move(move):
            self.board[move] = symbol
        else:
            raise ValueError("Invalid move!")

    def is_winner(self, bot: Bot) -> bool:
        """ Check if the given symbol has won. """
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]
        return any(all(self.board[i] == bot.symbol for i in combo) for combo in winning_combinations)

    @property
    def is_full(self) -> bool:
        """ Check if the board is full (draw condition). """
        return all(space != Tokens.EMPTY for space in self.board)

    @property
    def board_state(self):
        """ Return the board state as a string for the bot to read. """
        return ''.join([i.value for i in self.board])


class GameManager:
    def __init__(self):
        """ Initialize the GameManager with registered bots. """
        self.bots = []

    def register(self, bot_folder: str):
        """ Register a bot for the competition. """
        bot = Bot(bot_folder)
        self.bots.append(bot)

    def play_match(self, bot1: int, bot2: int):
        """ Play a match between two bots. """
        board = Board()
        bot1 = self.bots[bot1]
        bot2 = self.bots[bot2]

        players = [bot1, bot2]

        # Start both bots
        bot1.start(Tokens.X)
        bot2.start(Tokens.O)

        turn = 0
        while not board.is_full:
            current_bot = players[turn % 2]

            board.display()
            print(f"Player {current_bot.symbol.value}'s turn")

            try:
                move = current_bot.make_move(board)
                if board.is_valid_move(move):
                    board.place_move(move, current_bot.symbol)
                else:
                    print(f"Invalid move by {current_bot.bot_folder}. {current_bot.symbol.value} loses!")
                    return
            except Exception as e:
                print(f"Error during {current_bot.symbol.value}'s turn: {e}")
                return

            if board.is_winner(current_bot):
                board.display()
                print(f"{current_bot.symbol.value} wins!")
                return

            turn += 1

        board.display()
        print("It's a draw!")

        # Stop both bots
        bot1.stop()
        bot2.stop()


if __name__ == '__main__':
    gm = GameManager()
    bot_directory = "./bots"

    # Register bots from the bot directory
    for bot_folder in ls_exec(bot_directory):
        gm.register(bot_folder.path)

    print(f"Registered {len(gm.bots)} bots from {bot_directory}.")

    # Run a match between the first two bots (if any are registered)
    if len(gm.bots) >= 2:
        print("Playing a match with {} and {}.".format(gm.bots[0].bot_folder, gm.bots[1].bot_folder))
        gm.play_match(0, 1)
    else:
        print("Not enough bots to play a match.")