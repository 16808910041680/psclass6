#coding a game of Regicide into the terminal
import random 
import numpy 
import math 
suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
startdraw= ["Ace","2", "3", "4", "5", "6", "7", "8", "9", "10"]
fightingdraw = ["Jack", "Queen", "King"]

def decktracker():
    deck = []
    for suit in suits:
        for card in startdraw:
            deck.append(f"{card} of {suit}")
    for suit in suits:
        for card in fightingdraw:
            deck.append(f"{card} of {suit}")
    
def drawcard():
    suit = random.choice(suits)
    card = random.choice (startdraw)
    return f"{card} of {suit}"

print("Welcome to the card game!")
cont = input ("For the rules, type 1. Otherwise, type 2 to continue.")

if cont == 1:
    print ("This is regicide. You will be drawing 7 cards to start the game. Firstly, the rules are you're fighting the Jacks, Queens, and Kings. Jacks have 20 health, dealing 10 damage, Queens have 30 health, dealing 15 damage, and Kings have 40 health, dealing 20 damage. Each card deals the damage of it's sheet: the 10's deal 10 damage, so on, so on.")
    print ("The goal of the game is to defeat all 12 Jacks, Queens, and Kings. You win if you defeat them all, and lose if you run out of cards in your deck.")
    print ("Damage is taken by discarding cards of the same value.")
    print ("Each card suit will have a specific power. Clubs doubles your damage, Spades give you a shield for damage, Hearts help you change your cards and diamonds help you draw.")
    print ("Each boss's suit is immune to the power of the same suit. For example, a Jack of Hearts is immune to the power of Hearts. To clarify, that means you cannot use the power of Hearts to change your cards when fighting a Jack of Hearts.")
    print ("Good luck, and have fun playing!")
elif cont == 2:
    for i in range (7):
        print(drawcard())
        
    firstboss = random.choice (suits)
    print (f"The first boss is a Jack of {firstboss}!")
    print ("Cards:")
else: 
    print ("Please type a valid input.")
