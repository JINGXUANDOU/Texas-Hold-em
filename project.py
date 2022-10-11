import collections
import os, csv, math, random
from pathlib import Path
import argparse
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter


Card = collections.namedtuple('Card', 'suit value')
INITIAL_BET = 10    # Initial bet value
TEST_CASES_FILE = 'test_results.txt'

ACTION_FOLD = 'Fold'
ACTION_ALL_IN = 'All_In'
ACTION_BET = 'Bet'

NUMBER_OF_TRAIN = 3000

SUCC_RATIO_ACTION_TABLE = [
    (0.4, ACTION_FOLD, 0, 0),
    (0.6, ACTION_BET, 1, 2),
    (0.8, ACTION_BET, 2, 3),
    (1.0, ACTION_BET, 3, 10)
]

TEST_MODE = True

"""
The "round" input actually means the "game" in this program. Each game has two rounds.
Each player has 2 given cards and 3 community cards in the first round, and they bet. Then 2 community cards are given.
Then it comes to round 2, finally print the result of a game, which is 2 rounds.
Then it comes to a next game, which involves 2 rounds.
If only one player has rank below threshold, the player wins but receive no winning jetton.
"""

CARD_VALUES = ('', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K')
CARD_FONT = ('Ariel', 18, 'bold')
BUTTON_FONT = ('Ariel', 12, 'bold')
SPINBOX_FONT = ('Ariel', 16, 'bold')
BETS_FONT = ('Ariel', 20, 'bold')


class TestCase:
    '''This class contains key information of every testcase in given directory.

    Attributes:
        name: Name of file
        winner: The winner of the contents of the file given
        players: A list of players' cards given
    '''
    def __init__(self):
        self.name = ''
        self.winner = ''
        self.players: list[tuple[str, list[Card]]] = []

    def set_name(self, name: str):
        self.name = name

    def set_winner(self, winner: str):
        self.winner = winner

    def add_player(self, id: str, cards: list[Card] = [], cards_str: list[str] = []):
        if len(cards) > 0:
            if len(cards) < 5:
                raise ValueError
            self.players.append((id, cards))
        else:
            if len(cards_str) < 5:
                raise ValueError

            player_cards: list[Card] = []
            for card_str in cards_str:
                suit = card_str[0]
                value = int(card_str[1:])

                if not suit in 'SDCH' or value <= 0 or value > 13:
                    raise ValueError
        
                player_cards.append(Card(suit, value))

            if len(player_cards) > 0:
                self.players.append((id, player_cards))


class TestCases:
    '''This class reads all files given in test_results.txt.

    Attributes:
        cases: A list of testcase objects
    '''
    def __init__(self):
        self.cases: list[TestCase] = []

    def read_from_directory(self, dir_path: str) -> None:
        os.chdir(Path(dir_path))

        with open(TEST_CASES_FILE, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                test_case_file = row[0]

                if len(row) == 1:
                    winner = ''
                else:
                    winner = row[1]

                try:
                    self.read_from_file(test_case_file, winner)
                except:
                    print('There is an error while reading \'{}\'.'.format(test_case_file))

        if len(self.cases) == 0:
            raise


    def read_from_file(self, test_case_file: str, winner: str) -> None:
        with open(test_case_file, 'r') as f:
            case = TestCase()
            case.set_name(test_case_file)

            reader = csv.reader(f)
            for row in reader:
                if len(row) == 0:
                    continue

                case.add_player(id = row[0], cards_str = row[1:])
                if row[0] == winner:
                    case.set_winner(winner)

            if not case.winner or len(case.players) == 0:
                raise ValueError

            self.cases.append(case)


    def add(self, case: TestCase):
        if not case.winner or len(case.players) == 0:
            raise ValueError
        self.cases.append(case)


class  Deck():
    '''This class stimulates a deck in Texas Hold'em. It can shuffle a deck of cards and deal them to players.

    Attributes:
    cards: A list that contains total 52 cards (without 2 Jokers) in a list
    top: The top card among all cards'''

    def __init__(self, number_of_cards: int = 0) -> None:
        self.cards = []
        self.top = 0

        for suit in 'SDCH':
            for value in range(1, 14):
                self.cards.append(Card(suit, value))
        

    def shuffle(self) -> None:
        '''Game shuffles cards into random order.
        
        Returns:
            A pack of cards after shuffling.'''
        random.shuffle(self.cards)
        self.top = 0
        

    def deal(self, size: int) -> list[Card]:
        """Game deals cards to player

        Returns:
            cards: The card list on top of a deck of cards.
        """
        assert(0 < size < len(self.cards) - self.top)

        deal_cards: list[Card] = []
        for i in range(size):
            deal_cards.append(self.cards[self.top])
            self.top += 1

        return deal_cards


    def remove(self, remove_cards: list[Card]):
        for card in remove_cards:
            self.cards.remove(card)


class Player:
    """A simple class to store id and cards of Player.

    Attributes:
        initial_cards: The 2 cards player get at first
        community_cards: The community cards shared by all players
        bet_amount: The amount used to bet
        rank (int): Rank of result.
        rank_values(list): Statistics of rank suits and values
    """ 

    def __init__(self, id: str) -> None:
        self.id = id
        self.bet_amount = 0
        self.bets = 0
        self.state = ACTION_FOLD
        self.initial_cards: list[Card] = []
        self.community_cards: list[Card] = []
        self.rank = 9
        self.rank_values: list[int] = []
        self.number_of_train = 0
        self.number_of_train_win = 0
        self.reset_cards()


    def set_initial_bet(self, initial_bet: int) -> None:
        self.bet_amount = initial_bet
        self.bets = 0
        if self.bet_amount > 0:
            self.state = ACTION_BET


    def take_bets(self, bets: int) -> None:
        """ Decrease bets from bet_amount
        """
        if bets < self.bet_amount:
            self.bet_amount -= bets
        else:
            self.bet_amount = 0
            self.state = ACTION_ALL_IN
        self.bets = bets


    def give_bets(self, bets: int) -> None:
        """ Increase bets to bet_amount
        """
        self.bet_amount += bets
        self.bets = 0
        if self.bet_amount > 0:
            self.state = ACTION_BET


    def set_initial_cards(self, initial_cards: list[Card]) -> None:
        self.initial_cards = initial_cards


    def set_community_cards(self, community_cards: list[Card]) -> None:
        self.community_cards = community_cards
        self.number_of_train = 0
        self.number_of_train_win = 0


    def reset_cards(self):
        self.initial_cards.clear()
        self.community_cards.clear()
        self.rank = 9
        self.rank_values.clear()
        self.number_of_train = 0
        self.number_of_train_win = 0
        self.bets = 0

        if self.bet_amount == 0:
            self.state = ACTION_FOLD
        else:
            self.state = ACTION_BET


    def train(self, train_case):
        if self.is_fold() or self.is_all_in():
            return

        self.check_rank()

        self.number_of_train += 1
        if self.compare(train_case) >= 0:
            self.number_of_train_win += 1


    def is_all_in(self) -> bool:
        return self.state  == ACTION_ALL_IN


    def is_fold(self) -> bool:
        return self.state  == ACTION_FOLD


    def is_betting(self) -> bool:
        return self.state  == ACTION_BET


    # Judge player's action
    def make_action(self, limp_bets: int) -> tuple[str, int]:
        return ACTION_FOLD, 0


    # Check rank of list of cards
    def check_rank(self) -> None:
        if self.rank == 9 and len(self.rank_values) == 0:
            self.check_suit_rank()
            self.check_straight()
            self.check_value_rank()


    # Separate cards into value lists.
    def group_cards(self, four_kind_cards: list, three_kind_cards: list, pair_cards: list, single_cards: list) -> None:
        count_of_values = {}

        for card in self.initial_cards + self.community_cards:
            if card.value == 1:
                value = 14
            else:
                value = card.value
            count_of_values[value] = count_of_values.get(value, 0) + 1

        for value, count in count_of_values.items():
            while count >= 4:
                count -= 4
                four_kind_cards.append(value)

            while count >= 3:
                count -= 3
                three_kind_cards.append(value)

            while count >= 2:
                count -= 2
                pair_cards.append(value)

            while count >= 1:
                count -= 1
                single_cards.append(value)

        four_kind_cards.sort(reverse=True)
        three_kind_cards.sort(reverse=True)
        pair_cards.sort(reverse=True)
        single_cards.sort(reverse=True)


    # Check whether there are 4/3/2 cards with same rank in the list
    def check_value_rank(self) -> None:
        if self.rank < 2:
            return

        four_kind_cards = []
        three_kind_cards = []
        pair_cards = []
        single_cards = []
        self.group_cards(four_kind_cards, three_kind_cards, pair_cards, single_cards)

        if len(four_kind_cards) >= 1:
            self.rank = 2
            self.rank_values.append(four_kind_cards[0])
            value = 0

            if len(single_cards) > 0:
                value = single_cards[0]
            if len(pair_cards) > 0 and value < pair_cards[0]:
                value = pair_cards[0]
            if len(three_kind_cards) > 0 and value < three_kind_cards[0]:
                value = three_kind_cards[0]

            self.rank_values.append(value)
        elif len(three_kind_cards) >= 1 and len(pair_cards) >= 1:
            self.rank = 3
            self.rank_values.append(three_kind_cards[0])
            self.rank_values.append(pair_cards[0])
        elif self.rank < 6:
            return
        elif len(three_kind_cards) == 1:
            self.rank = 6
            self.rank_values.append(three_kind_cards[0])
            self.rank_values += single_cards[0:2]
        elif len(pair_cards) == 2:
            self.rank = 7
            self.rank_values += pair_cards[0:2]
            self.rank_values.append(single_cards[0])
        elif len(pair_cards) == 1:
            self.rank = 8
            self.rank_values.append(pair_cards[0])
            self.rank_values += single_cards[0:3]
        else:
            self.rank = 9
            self.rank_values = single_cards[0:5]


    # Check whether the suit of a list of cards are same
    def check_suit_rank(self) -> None:
        suits = { 'S': [], 'D': [], 'C': [], 'H': [] }
        
        for card in self.initial_cards + self.community_cards:
            if card.value == 1:
                suits[card.suit].append(14)
            else:
                suits[card.suit].append(card.value)

        for cards_suit, cards_value in suits.items():
            if len(cards_value) >= 5:
                cards_value.sort(reverse=True)
                self.check_suit_straight(cards_suit, cards_value)
                self.check_same_suit(cards_value)


    # Check whether the cards are suit straight, return straight's max value, If result is 0, it is not a straight.
    def check_suit_straight(self, cards_suit: str, cards_value: list[int]) -> bool:
        if len(cards_value) < 5:
            return False

        is_straight = True

        for i in range(len(cards_value) - 4):
            for j in range(i, i + 4):
                if cards_value[j] - 1 != cards_value[j + 1]:
                    is_straight = False
                    break

            if is_straight:
                if cards_suit == 'D':
                    self.rank = 0
                elif self.rank > 0:
                    self.rank = 1
                    self.rank_values.append(cards_value[i])
                return True

        return False

    # Check whether the cards are straight
    def check_straight(self) -> bool:
        cards_value: list[int] = []

        for card in self.initial_cards + self.community_cards:
            if card.value == 1:
                cards_value.append(14)
            else:
                cards_value.append(card.value)

        cards_value.sort(reverse=True)
        number_of_cards = len(cards_value)

        for i in range(number_of_cards - 4):
            count = 1
            for j in range(i, number_of_cards - 1):
                if cards_value[j] == cards_value[j + 1]:
                    continue
                elif cards_value[j] - 1 != cards_value[j + 1]:
                    break
                else:
                    count += 1
                    if count == 5:
                        if self.rank > 5:
                            self.rank = 5
                            self.rank_values.append(cards_value[i])
                        return True
        return False


    # Check whether the cards have same suit
    def check_same_suit(self, cards_value: list[int]) -> bool:
        if len(cards_value) < 5:
            return False

        if self.rank > 4:
            self.rank = 4
            self.rank_values = cards_value[0:5]

        return True


    # Compare self and other. Return 1 if self>other, return -1 if self<other, return 0 if self=other.
    def compare(self, other) -> int:
        if self.state == ACTION_FOLD:
            return -1

        if self.rank < other.rank:
            return 1
        elif self.rank > other.rank:
            return -1

        if self.rank == 0:
            return 0

        lens = min(len(self.rank_values), len(other.rank_values))

        for i in range(lens):
            if self.rank_values[i] < other.rank_values[i]:
                return -1
            elif self.rank_values[i] > other.rank_values[i]:
                return 1               
    
        if lens < len(other.rank_values):
            return -1
        elif lens < len(self.rank_values):
            return 1
        else:
            return 0

    def rank_str(self) -> str:
        RANK = ('Royal Flush', 'Straight Flush', 'Four of a kind', 'Full house', 'Flush', 'Strainght', 
        'Three of a kind', 'Two pairs', 'Pairs', 'Highcard')
        return RANK[self.rank]


class HumanPlayer(Player):
    '''This class represents human player in user mode. And it's a subclass of class Player.
    '''
    def make_action(self, limp_bets: int) -> tuple[str, int]:
        if not self.is_betting():    # Check whether the player is fold or all in
            return self.state, 0

        if len(self.initial_cards) + len(self.community_cards) >= 5:    # Check cards' number
            self.check_rank()

        bets = 0
        while True:
            input_str = input("Please enter amount to bet (Enter 'f' for fold):")
            if input_str == 'f' or input_str == 'F':    # Justify whether the user is going to fold
                self.state = ACTION_FOLD
                print("Human Player: fold.")
                return ACTION_FOLD, 0            
            elif input_str.isdigit():
                bets = int(input_str)
                if bets == self.bet_amount or limp_bets <= bets < self.bet_amount:
                    break
            print("Invalid input. You should enter a positive integer between {} and {}.".format(limp_bets, self.bet_amount))

        self.take_bets(bets)
        if self.is_all_in():
            print("Human Player: bet ${}. It\'s all in.".format(self.bets))
        else:
            print("Human Player: bet ${}.".format(bets))

        return ACTION_BET, bets


class BotPlayer(Player):
    '''This class represents bot players in user mode.  And it's a subclass of class Player.
    '''
    def make_action(self, limp_bets: int) -> tuple[str, int]:
        if not self.is_betting():
            return self.state, 0

        bets = limp_bets

        if len(self.initial_cards) + len(self.community_cards) >= 5:
            self.check_rank()

            succ_ratio = self.number_of_train_win / self.number_of_train
            print("Bot Player {}: train {}, win {}, ratio {}.".format(self.id, self.number_of_train, self.number_of_train_win, succ_ratio))

            for action_item in SUCC_RATIO_ACTION_TABLE:
                if succ_ratio < action_item[0]:
                    if action_item[1] == ACTION_FOLD:
                        self.state = ACTION_FOLD
                        print("Bot Player {}: fold.".format(self.id))
                        return ACTION_FOLD, 0

                    if limp_bets < action_item[2]:
                        bets = action_item[2]
                    elif limp_bets > action_item[3]:
                        self.state = ACTION_FOLD
                        print("Bot Player {}: fold.".format(self.id))
                        return ACTION_FOLD, 0
                
                    break

        self.take_bets(bets)
        if self.is_all_in():
            print("Bot Player {}: bet ${}. It\'s all in.".format(self.id, self.bets))
        else:
            print("Bot Player {}: bet ${}.".format(self.id, bets))

        return ACTION_BET, bets


class Trainer:
    '''This class trains bot players so they stimulate card process and estimate their winning probability.
    
    Attributes:
        number_of_player: The number of players in game.'''
    def __init__(self, number_of_player: int):
        self.players: list[Player] = []
        for i in range(number_of_player):
            self.players.append(Player(str(i)))


    def train(self, community_cards: list[Card]) -> Player:
        deck = Deck()
        deck.remove(community_cards)
        deck.shuffle()

        for player in self.players:
            player.reset_cards()
            player.set_initial_cards(deck.deal(2))

        train_community_cards: list[Card] = []
        train_community_cards += community_cards

        if len(train_community_cards) == 3:
            train_community_cards += deck.deal(2)

        for player in self.players:
            player.set_community_cards(train_community_cards)
            player.check_rank()

        winner = self.players[0]
        for player in self.players:
                if player.compare(winner) > 0:
                    winner = player

        return winner


class Game():
    '''The class represents gaming system for Texas Holdem.
    
    Attributes:
        deck: Stimulated deck for game
        bet_pool: Total amount bet in bet pool for this game
        number_of_round: Number of rounds passed
        community_cards: Community card ist for this round
        human_player: object for HumanPlayer class
        bot_player: List of objects for BotPlayer class.
        all_players:List of objects for all Players.
        '''
    def __init__(self):
        self.deck = Deck()
        self.bet_pool = 0
        self.number_of_round = 0
        self.community_cards: list[Card] = []
        self.human_player = HumanPlayer('0')
        self.bot_players: list[BotPlayer] = []
        self.all_players: list[Player] = []


    def init_players(self, number_of_players: int) -> None:
        self.human_player.set_initial_bet(INITIAL_BET)

        for i in range(1, number_of_players + 1):
            player = BotPlayer(str(i))
            player.set_initial_bet(INITIAL_BET)
            self.bot_players.append(player)

        self.all_players.append(self.human_player)
        self.all_players += self.bot_players


    def clear_players(self) -> None:
        self.bot_players.clear()
        self.all_players.clear()
        

    def reset_cards(self):
        self.bet_pool = 0
        self.number_of_round = 0
        self.community_cards.clear()

        for player in self.all_players:
            player.reset_cards()


    def deal_cards(self) -> None:
        if self.number_of_round == 0:
            self.deck.shuffle()
            self.community_cards.clear()

            print('------Initialization--------')
            for player in self.all_players:
                player.set_initial_cards(self.deck.deal(2))

            Game.print_cards('Human Player: ', self.human_player.initial_cards)
        elif self.number_of_round == 1:
            print('---------Round 1-----------')
            self.community_cards += self.deck.deal(3)
            for player in self.all_players:
                player.set_community_cards(self.community_cards)

            Game.print_cards('Community cards: ', self.community_cards)
        elif self.number_of_round == 2:
            print('---------Round 2-----------')
            self.community_cards += self.deck.deal(2)
            for player in self.all_players:
                player.set_community_cards(self.community_cards)

            Game.print_cards('Community cards: ', self.community_cards[3:])


    # Run user mode
    def run_user_mode(self, number_of_players: int) -> None:
        self.init_players(number_of_players)
        match_count = 0
        while True:
            match_count += 1
            print('\n------Match {}--------\n'.format(match_count))

            self.deal_cards()

            while self.play_a_round():
                self.deal_cards()

            result_msg = self.check_result()
            print('---------Results-----------')
            print(result_msg)
            self.print_detail()
        
            self.reset_cards()

            if self.human_player.is_fold():
                print('The game ends, since the human player is out of money.')
                break

            has_bot_player = False
            for player in self.bot_players:
                if not player.is_fold():
                    has_bot_player = True
                    break

            if not has_bot_player:
                print('The game ends, since the bot player is out of money.')
                break

            if Game.input_choice() == 'n':
                break

        print('------End of Game--------')


    # Run file mode
    def run_file_mode(self, dir_path: str) -> None:
        try:
            test_cases = TestCases()
            test_cases.read_from_directory(dir_path)
        except:
            print('There is an error while reading test cases directory \'{}\'.'.format(dir_path))
            return

        number_of_passed = 0

        for test_case in test_cases.cases:
            self.init_players(len(test_case.players)-1)

            for player, test_player in zip(self.all_players, test_case.players):
                player.set_initial_cards(test_player[1])
                player.check_rank()
            
            winner_list = self.get_winner()
            if len(winner_list) > 1:
                if not test_case.winner:       # Check whether the game is tied.
                    number_of_passed += 1
                else:
                    print('Test case {} is incorrect, the game is tied, while expected winner is {}'.format(test_case.name, test_case.winner))
            elif winner_list[0].id == test_case.winner:      # Check whether the winner is the same as expected.
                number_of_passed += 1
            else:
                print('Test case {} is incorrect, winner {} != except winner {}.'.format(test_case.name, winner_list[0].id, test_case.winner))
            
            self.clear_players()

        print('There are {} tests passed.'.format(number_of_passed))


    def train_players(self) -> None:
        trainer = Trainer(len(self.bot_players))

        for i in range(NUMBER_OF_TRAIN):
            train_case = trainer.train(self.community_cards)
            for player in self.bot_players:
                player.train(train_case)


    def play_a_round(self) -> bool:
        if self.number_of_round > 0:
            self.train_players()

        self.number_of_round += 1
        number_of_bet_players = 0
        limp_bets = 0

        for player in self.all_players:
            action, bets = player.make_action(limp_bets)
            if action == ACTION_BET:
                self.bet_pool += bets
                if limp_bets < bets:
                    limp_bets = bets
                elif not player.is_all_in():
                    number_of_bet_players += 1

        return self.number_of_round < 3 and number_of_bet_players > 1


    def distribute_bet_pool(self, winner_list: list[Player]) -> None:
        number_of_winner = len(winner_list)
        if number_of_winner > 1:
            for player in self.all_players:
                if player in winner_list:
                    bets = math.ceil(self.bet_pool / number_of_winner)
                    self.bet_pool -= bets
                    number_of_winner -= 1
                    player.give_bets(bets)
        elif number_of_winner == 0:
            number_of_winner = len(self.all_players)
            for player in self.all_players:
                bets = math.ceil(self.bet_pool / number_of_winner)
                self.bet_pool -= bets
                number_of_winner -= 1
                player.give_bets(bets)
        elif number_of_winner == 1:
            winner_list[0].give_bets(self.bet_pool)

        self.bet_pool = 0


    def check_result(self) -> str:
        winner_list = self.get_winner()
        self.distribute_bet_pool(winner_list)

        number_of_winner = len(winner_list)
        if number_of_winner > 1:
            result_msg = 'The match is tie. The winner are Player'
            for player in winner_list:
                result_msg += ' {}'.format(player.id)

            if self.human_player in winner_list:
                result_msg += '. You win.'
            else:
                result_msg += '. You lost.'
        elif number_of_winner == 0:
            result_msg = 'All players fold the game.'
        elif winner_list[0] == self.human_player:
            result_msg = 'You win the match.'
        else:
            result_msg = 'You lost the match. The winner is bot player {}.'.format(winner_list[0].id)

        return result_msg


    def print_detail(self):
        if TEST_MODE:
            self.human_player.check_rank()
            if self.human_player.is_fold():
                print('[X] ', end='')
            else:
                print('    ', end='')

            print('Human Player: ${}, rank {} = {}.'.format(self.human_player.bet_amount, self.human_player.rank, self.human_player.rank_str()), end='')
            Game.print_player_cards(' ', self.human_player)

            for player in self.bot_players:
                player.check_rank()
                if player.is_fold():
                    print('[X] ', end='')
                else:
                    print('    ', end='')

                print('Bot Player {}: ${}, rank {} = {}.'.format(player.id, player.bet_amount, player.rank, player.rank_str()), end='')
                Game.print_player_cards(' ', player)
        else:
            print('Human Player: ${}'.format(self.human_player.bet_amount))

            for player in self.bot_players:
                print('Bot Player {}: ${}'.format(player.id, player.bet_amount))
        print('')


    def get_winner(self) -> list[Player]:
        """This class judge the winner and return winner
        """
        winner_list: list[Player] = []

        for player in self.all_players:
            if player.is_fold():
                continue

            if len(winner_list) == 0:
                winner_list.append(player)
            else:
                result = player.compare(winner_list[0])
                if result > 0:
                    winner_list.clear()
                    winner_list.append(player)
                elif result == 0:
                    winner_list.append(player)

        #assert(len(winner_list) > 0)
        return winner_list


    @staticmethod
    def print_player_cards(prefix: str, player: Player) -> None:
        print(prefix, end='')

        for card in player.initial_cards:
            print(' {}{}'.format(card.suit, card.value), end='')

        for card in player.community_cards:
            print(' {}{}'.format(card.suit, card.value), end='')

        print('')


    @staticmethod
    def print_cards(prefix: str, cards1: list[Card]) -> None:
        print(prefix, end='')

        for card in cards1:
            print(' {}{}'.format(card.suit, card.value), end='')

        print('')


    @staticmethod
    def input_choice():
        while True:
            continue_choice = input("Do you want to continue gaming? Type 'y' for yes and 'n' for no:")
            if continue_choice == 'Y' or continue_choice == 'y':
                return 'y'
            elif continue_choice == 'N' or continue_choice == 'n':
                return 'n'
            print('Invalid input. Please re-enter your choice.')


# game window
class GameWindow(Game):
    """A class to do operations of gamewindow.
    """

    def destroy(self) -> None:      # destroy window
        """Destroy the window when finishing."""
        self.window.quit()


    def create_window(self, number_of_players:int) -> None:
        """create a widget"""
        self.window = tk.Tk()               # root window
        self.window.resizable(False, False)
        self.window.title("Texas")
        self.window.geometry('1000x440')

        self.card_img: dict[str, tk.PhotoImage] = {}
        self.initial_cards_item = []
        self.community_cards_item = []
        self.spinbox_value = tk.IntVar()

        self.desktop_img = tk.PhotoImage(file='bg.png')
        self.card_img['D'] = tk.PhotoImage(file='diamond.png')
        self.card_img['H'] = tk.PhotoImage(file='heart.png')
        self.card_img['C'] = tk.PhotoImage(file='club.png')
        self.card_img['S'] = tk.PhotoImage(file='spade.png')

        self.create_board()
        self.create_players_area(number_of_players)
        self.create_buttons()


    def create_board(self) -> None:
        '''create a board area for game'''
        self.canvas = tk.Canvas(self.window, width=660, height=426)
        self.canvas.pack(side=tk.LEFT)
        self.canvas.create_image(10, 10, anchor=tk.NW, image=self.desktop_img)
        self.bet_pool_text = self.canvas.create_text(320, 280, text="Bet pool: 0", fill ='#7CCDFF', font=BETS_FONT)


    def create_buttons(self) -> None:
        self.create_bet_spinbox()
        btn = tk.Button(self.window, text="Bet", width=10, command=self.on_bet, font=BUTTON_FONT)
        btn.place(x=540, y=360)
        btn = tk.Button(self.window, text="Fold", width=10, command=self.on_fold, font=BUTTON_FONT)
        btn.place(x=540, y=400)


    def create_players_area(self, number_of_players: int) -> None:
        """Create players board which shows player name, bets and action.
        
        Args:
            area: The area of showing.
        """
        columns = ['player', 'bets', 'action']
        self.players_table = ttk.Treeview(
                master=self.window,
                height=11,
                columns=columns,
                show='headings',
                )

        self.players_table.heading(column='player', text='player')
        self.players_table.heading(column='bets', text='bets')
        self.players_table.heading(column='action', text='action', anchor='w')

        self.players_table.column(column='player', width=140, minwidth=20, anchor='center')
        self.players_table.column(column='bets', width=80, minwidth=20, anchor='center')
        self.players_table.column(column='action', width=120, minwidth=20, anchor='w')

        self.players_table.pack(side=tk.LEFT, pady=10)

        self.players_table.insert('', index=0, text='', values=('Human player', '10', ''))
        for i in range(1, number_of_players):
            self.players_table.insert('', index=i, text='', values=('Bot player{}'.format(i), '10', ''))

        for i in range(number_of_players, 11):
            self.players_table.insert('', index=i, text='', values=('', '', ''))

        # Set the rowheight
        style=ttk.Style()
        style.configure("Treeview.Heading", font=(None, 14), rowheight=int(14*2.5))
        style.configure("Treeview", font=(None, 14), rowheight=int(14*2.5))


    def update_bet_pool(self) -> None:
        self.canvas.delete(self.bet_pool_text)
        self.bet_pool_text = self.canvas.create_text(320, 280, text="Bet pool: {}".format(self.bet_pool), fill ='#7CCDFF', font=BETS_FONT)


    def create_bet_spinbox(self) -> None:
        self.spinbox = tk.Spinbox(self.window, from_=1, to=self.human_player.bet_amount, increment=1, width=7, textvariable=self.spinbox_value, bg='#9BCD9B', font=SPINBOX_FONT)
        self.spinbox.place(x=540, y=325)


    def update_bet_spinbox(self) -> None:
        self.spinbox.destroy()

        if self.human_player.bet_amount == 0:
            self.spinbox_value.set(0)
            self.spinbox = tk.Spinbox(self.window, from_=0, to=0, increment=1, width=7, textvariable=self.spinbox_value, bg='#9BCD9B', font=SPINBOX_FONT)
        else:
            self.spinbox_value.set(1)
            self.spinbox = tk.Spinbox(self.window, from_=1, to=self.human_player.bet_amount, increment=1, width=7, textvariable=self.spinbox_value, bg='#9BCD9B', font=SPINBOX_FONT)
        self.spinbox.place(x=540, y=325)


    def update_cards(self) -> None:
        if self.number_of_round == 0:
            x_pos, y_pos = 305, 375
            cards = self.human_player.initial_cards
            cards_item = self.initial_cards_item
        elif self.number_of_round == 1:
            x_pos, y_pos = 220, 220
            cards = self.human_player.community_cards
            cards_item = self.community_cards_item
        elif self.number_of_round == 2:
            x_pos, y_pos = 400, 220
            cards = self.human_player.community_cards[3:]
            cards_item = self.community_cards_item
        else:
            return

        for card in cards:
            suit_cv = self.canvas.create_image(x_pos, y_pos, image=self.card_img[card.suit])
            value_cv = self.canvas.create_text(x_pos, y_pos-5, text=CARD_VALUES[card.value], fill='#000000', font=CARD_FONT)
            cards_item.append((suit_cv, value_cv))
            x_pos += 60


    def update_players_info(self) -> None:
        items = self.players_table.get_children()

        for i, player in enumerate(self.all_players):
            if player.is_fold():
                action = 'Fold'
            elif player.is_all_in():
                action = 'All In'
            elif player.bets == 0:
                action = ''
            else:
                action = 'Bet {}'.format(player.bets)

            if i == 0:
                self.players_table.item(items[i], values=('Human player', str(player.bet_amount), action))
            else:
                self.players_table.item(items[i], values=('Bot player{}'.format(i), str(player.bet_amount), action))


    def on_bet(self):
        if not self.human_player.is_betting():
            return

        bets = self.spinbox_value.get()
        self.bet_pool += bets
        self.human_player.take_bets(bets)

        self.update_bet_spinbox()
        self.update_bet_pool()

        self.window.after(0, self.play_a_round())


    def on_fold(self):
        if self.human_player.is_fold():
            return
            
        self.human_player.state = ACTION_FOLD
        self.window.after(0, self.play_a_round())


    def end_match(self):
        result_msg = self.check_result()
        self.print_detail()
        self.reset_cards()
        choice = False

        if self.human_player.is_fold():
            messagebox.showinfo('Confirm', result_msg + '\n\nThe game ends, since you are out of money.')
        else:
            has_bot_player = False
            for player in self.bot_players:
                if not player.is_fold():
                    has_bot_player = True
                    break

            if not has_bot_player:
                messagebox.showinfo('Confirm', result_msg + '\n\nThe game ends, since the bot players are out of money.')
            else:
                choice = messagebox.askyesno('Confirm', result_msg + '\n\nDo you want to continue gaming?')

        if choice:
            self.window.after(0, self.flop_cards)
        else:
            self.window.destroy()


    def flop_cards(self) -> None:
        Game.deal_cards(self)
        self.update_cards()


    def play_a_round(self) -> None:
        if self.number_of_round > 0:
            self.train_players()

        self.number_of_round += 1
        limp_bets = self.human_player.bets

        if self.human_player.is_betting():
            number_of_bet_players = 1
        else:
            number_of_bet_players = 0

        for player in self.bot_players:
            action, bets = player.make_action(limp_bets)
            if action == ACTION_BET:
                self.bet_pool += bets
                if limp_bets < bets:
                    limp_bets = bets
                if not player.is_all_in():
                    number_of_bet_players += 1

        self.update_bet_pool()
        self.update_players_info()

        if self.number_of_round > 2:
            self.window.after(0, self.end_match())
        elif number_of_bet_players <= 1:
            self.flop_cards()
            self.window.after(0, self.end_match())
        elif self.human_player.is_betting():
            self.window.after(200, self.flop_cards())
        else:
            self.flop_cards()
            self.window.after(0, self.play_a_round())


    def run_user_mode(self, number_of_players: int):
        self.init_players(number_of_players)
        self.create_window(number_of_players)

        self.window.after(500, self.flop_cards)
        self.window.mainloop()


    def reset_cards(self):
        Game.reset_cards(self)

        for item in self.initial_cards_item:
            self.canvas.delete(item[0])
            self.canvas.delete(item[1])

        for item in self.community_cards_item:
            self.canvas.delete(item[0])
            self.canvas.delete(item[1])

        self.initial_cards_item.clear()
        self.community_cards_item.clear()

        self.update_bet_pool()
        self.update_bet_spinbox()
        self.update_players_info()
        self.window.after(500, self.deal_cards)



if __name__=="__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u', action="store_true", help='run as user mode')
    group.add_argument('-f', action="store_true", help='run as ile mode')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', metavar='num', type=int, help='number of players you want to play with, 0 < num < 10')
    group.add_argument('-i', metavar='path', type=str, help='path_to_test_cases_directory')

    args = parser.parse_args()
    invalid_args = False

    if args.u and args.p: # Check whether the command line is under user mode form.
        if args.p < 1 or args.p > 9:
            invalid_args = True
        else:
            try:
                game = GameWindow()
                game.run_user_mode(args.p)
            except:
                invalid_args = True
    elif args.f and args.i:   # Check whether the command line is under file mode form.
        game = Game()
        game.run_file_mode(args.i)
    else:
        invalid_args = True         # Other forms that are not under required forms are rejected.

    if invalid_args:
        print("Something wrong happens. Please check your entering.\n")
        parser.print_help()
    
