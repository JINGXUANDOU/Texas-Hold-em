# Texas-Hold-em
A simple project for a Texas Hold'em project
## Explanation for homework options

There are two options for the project. Option 1 is to make a GUI window and option 2 is to design smarter bot players. I did both options to get extra points. 

My program will generate a GUI window under user mode, and bot players will bet different amount and fold sometimes during game. The program can also run under file mode which is the same as PA3.

Please grade both options, thank you for that.



## Brief Introduction

 1. This program is ran under Python 3.0 or newer version.

 2. The README file is written in markdown form, and can be read with jupyter notebook.

 3. After installing Python and extensions, type the following code in command line:

    ```
    $ jupyter notebook
    ```

    to enter jupyter notebook.



## Project Description

1. The project generates a Texas Hold'em  game which enables a player to play with several bot players in GUI, or a tester to test several groups of Texas Hold'em cards with expected winner. 
2. The game is ran with command line.
3. Under user mode, players play the game through GUI window. While results will be printed directly on screen under file mode.



## Guide for End-users (User mode)

1. Type "python script_name.py -u -p number_of_players_you_want_to_play_with" through command line to start a game. A GUI window will show your game-board.
2. You initially have 10 dollars to bet. 
3. During initialization process, you would be given 2 randomly generated cards which are only visible to you. Then the system will ask you to enter an amount to bet. You can choose an integer between 1 and 10 and press "bet" to bet, or press "fold" button to fold. Other players' actions will be displayed, after you bet, in statistic area which is located in right position of screen.
4. During round 1, 3 community cards are drawn which are visible to everyone in game. You are also visible to other players' bet amount in last process. Then the system will ask you to enter an amount to bet. You can choose an integer between 1 and you amount left and press "bet" button to bet, or press "fold" button to fold. Other players' actions will be displayed, after you bet, in statistic area which is located in right position of screen.
5. During round 2, 2 community cards are drawn which are visible to everyone in game. You are also visible to other players' bet amount in last process. Then the system will ask you to enter an amount to bet. You can choose an integer between 1 and you amount left and press "bet" button to bet, or press "fold" button to fold. Other players' actions will be displayed after you bet, in statistic area, which is located in right position of screen.
6. Once you fold, you will not be asked to enter an amount to bet later in that game. You will directory go to results.
7. You will be asked whether to continue gaming in a pop-up window. You can continue with pressing button "Y" or quit the game with pressing button "N".
8. If you press "Y", you will start from step 3, with money left from last game.



## Guide for End-users (File mode)

1. Type "python script_name.py -f -i path_to_test_cases_directory' for file mode" through command line to start a test. 
2. Your files should all be in ".txt" form.
3. There should be a file named "test_results.txt" in the same directory with expected winner of player files as content. 
4. All player files written in test_results.txt should all be in the same directory.
5. Once you type from command line, the program will show that how many tests are passed, and the tests that are not passed and reason.



## Guide for Other Programmers

This program contains 7 classes:

1. TestCase: This class contains key information of every testcase in given directory.
2. TestCases: This class reads all files given in test_results.txt.
3. Deck: This class stimulates a deck in Texas Hold'em. It can shuffle a deck of cards and deal them to players.
4. Player: A simple class to store id and cards of Player.
5. HumanPlayer: This class represents human player in user mode.
6. BotPlayer: This class represents bot players in user mode.
7. Trainer: Trainer class stimulates card process for bot players so bot players can estimate their winning probability. If the stimulated winning probability is lower than a level, bot player will fold.
8. Game: The class represents gaming system for Texas Holdem.
9. GameWindow: A class to do operations of gamewindow with thinker.



In main program, argparse controls input through command line and separate them into user mode and file mode. The program gets command line input through argparse, with add_mutually_exclusive_group to control different modes. For tk, tk creates photo images, canvas, buttons, spin box, etc for game window.

In user mode:

1. The program first sets the players
2. Then it sets up game window with tkinker and prepared for user.
3. The program sets initial bet.
4. In function "play_a_match", the program first shuffles cards.
5. Then program generates "initialization", "Round 1", and "Round 2", which would first generate cards, then ask for fold/bet, and print the answer.
6. After that, the program checks rank of each player and gets winner.
7. At last, it asks player whether to continue.



In file mode:

1. The program gets files from test_results.txt, and the directory given
2. The program reads those files.
3. The program checks rank of each player and gets winner of each file.
4. The program compares results, and add to test passed.



## Explanation for smarter bot players' logic

I designed a program so that bot players can estimate their winning probability, judge other players' bets and then make their own bet.

In class Trainer, bot players are trained to stimulate the game 3000 times. Each bot player stimulates the game without community cards for 3000 times, and calculate their winning probability. After that, they will use the winning probability to compare with several grades in SUCC_RATIO_ACTION_TABLE, which contains several probability ranks and bet amount level for these ranks. The first column is probability grade, second column is state, the third column is the bet amount floor, and the last column is the bet amount ceiling.

Each time the bot player first compare their stimulated winning probability and find the level. Then they will see previous players' bet amount. If the bet amount is lower than bet amount floor for that level, bot players will bet the floor amount. While previous players bets between floor and ceiling, bot players will bet ceiling amount. If previous player bets more than ceiling, then bot players will fold. For example:

If the winning probability is less than 0.4, bot players will fold. 

If the probability is between 0.4 and 0.6, they can bet from 1 to 2. They will first compare the previous player's bet amount to their bet amount floor, which is 1. If it's less than 1, they will just bet 1. If it's between 1 and 2, they will bet 2. If it's over 2, they will fold.
