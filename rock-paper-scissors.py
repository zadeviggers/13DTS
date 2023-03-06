# Copyright 2023 Zade Viggers.
# All rights reserved.

# Import the `random` module to chose a random item from a list.
import random

# List of options the user can choose from.
options = ["rock", "paper", "scissors"]

# Welcome message.
print("Let's play rock paper scissors!")

# Track whether the game is running.
playing = True
while playing:
    # Make a choice for the computer
    computer_choice = random.choice(options)

    # Get the user's choice
    user_choice = None

    # Loop forever, until the user quits or enters a correct value.
    while True:

        # Print this on a separate line for readability
        print(
            f"""Enter one of '{ "', '".join(options)}', or type 'quit' to stop playing.""")

        # Remove spaces, and convert to lower case to remove some potential errors
        res = input("> ").strip().lower()

        # Check if the result is in the options
        if res in options:
            # If it is, store the user's choice in a variable.
            user_choice = res
            # Stop the loop
            break
        # Allow the user to quit the game.
        elif res == "quit":
            # Feedback to user.
            print("Okay. It was fun playing with you!")
            # Built-in python function to quit the program.
            quit()
        # Handle empty response
        elif len(res) == 0:
            # Feedback to user.
            print("You didn't type anything! Could you try that again please?")
        # Generic error
        else:
            # Feedback to user.
            print(
                "That didn't look quite right. Can you try again? Make sure to type your response exactly the same as the in options I listed.")

    # Check for draws
    if computer_choice == user_choice:
        # Feedback to user.
        print(f"It's a draw! I also chose {computer_choice}.")
        # Exit this iteration of the loop, but keep looping.
        continue
    else:
        # Track whether the user won
        user_won = True

        # Figure out if the computer or the user won.
        # `match` is the python equivalent of a `switch` statement in other programming languages.
        match user_choice:
            # If the user chose 'rock'
            case "rock":
                # Check if the computer would win, otherwise, default to user winning.
                if computer_choice == "paper":
                    user_won = False
            # If the user chose 'paper'
            case "paper":
                # Check if the computer would win, otherwise, default to user winning.
                if computer_choice == "scissors":
                    user_won = False
            # If the user chose 'scissors'
            case "scissors":
                # Check if the computer would win, otherwise, default to user winning.
                if computer_choice == "rock":
                    user_won = False

        # Feedback to the user
        print(
            f"I chose {computer_choice}. That means {'you' if user_won else 'I'} win!")

    # Loop message
    print("Let's play again!")
