"""Terminal single-player Regicide.

A playable terminal adaptation of the cooperative card game, tuned for
single-player use.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
NUMBER_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
FACE_RANKS = ["J", "Q", "K"]
BOSS_HEALTH = {"J": 20, "Q": 30, "K": 40}
BOSS_ATTACK = {"J": 10, "Q": 15, "K": 20}
HAND_LIMIT = 8


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        if self.rank == "A":
            return 1
        if self.rank in FACE_RANKS:
            return 0
        return int(self.rank)

    @property
    def is_face(self) -> bool:
        return self.rank in FACE_RANKS

    def short(self) -> str:
        return f"{self.rank}{self.suit[0]}"

    def __str__(self) -> str:
        names = {
            "A": "Ace",
            "J": "Jack",
            "Q": "Queen",
            "K": "King",
        }
        rank_text = names.get(self.rank, self.rank)
        return f"{rank_text} of {self.suit}"


def make_tavern_deck() -> list[Card]:
    deck = [Card(rank, suit) for suit in SUITS for rank in NUMBER_RANKS]
    random.shuffle(deck)
    return deck


def make_boss_deck() -> list[Card]:
    deck = [Card(rank, suit) for suit in SUITS for rank in FACE_RANKS]
    random.shuffle(deck)
    return deck


def draw_cards(deck: list[Card], hand: list[Card], amount: int) -> int:
    draws = 0
    while deck and len(hand) < HAND_LIMIT and draws < amount:
        hand.append(deck.pop())
        draws += 1
    return draws


def print_rules() -> None:
    print("\n=== SINGLE-PLAYER REGICIDE RULES (TERMINAL VERSION) ===")
    print("- Defeat all 12 bosses (Jacks, Queens, Kings).")
    print("- You start with 8 cards. Play one turn at a time against the current boss.")
    print("- You may play 1+ cards, but they must all have the same value.")
    print("- Attack damage is the sum of played card values.")
    print("- Clubs: doubles your total damage (unless the boss is Clubs).")
    print("- Spades: blocks that much boss damage this turn (unless boss is Spades).")
    print("- Hearts: recycle that many cards from discard back into tavern deck")
    print("  (unless boss is Hearts).")
    print("- Diamonds: draw that many cards (unless boss is Diamonds).")
    print("- If boss survives, it attacks. You must discard cards from your hand")
    print("  whose total value is at least the incoming damage.")
    print("- If you cannot pay damage, you lose.\n")


def choose_indices(max_index: int, prompt: str) -> list[int]:
    while True:
        raw = input(prompt).strip().lower()
        if raw in {"q", "quit", "exit"}:
            raise SystemExit("Game exited.")
        if not raw:
            print("Please choose at least one card.")
            continue
        try:
            picks = [int(x) for x in raw.split()]
        except ValueError:
            print("Enter space-separated card numbers, like: 1 3 4")
            continue
        if len(set(picks)) != len(picks):
            print("Do not repeat card numbers.")
            continue
        if any(p < 1 or p > max_index for p in picks):
            print("One or more numbers are out of range.")
            continue
        return sorted(picks, reverse=True)


def remove_by_indices(cards: list[Card], descending_indices_1_based: Iterable[int]) -> list[Card]:
    removed: list[Card] = []
    for idx in descending_indices_1_based:
        removed.append(cards.pop(idx - 1))
    removed.reverse()
    return removed


def display_hand(hand: list[Card]) -> None:
    print("Your hand:")
    for i, card in enumerate(hand, start=1):
        print(f"  {i}. {str(card):20s} (value {card.value})")


def validate_play(played: list[Card]) -> bool:
    values = {c.value for c in played}
    return len(values) == 1 and next(iter(values)) > 0


def apply_hearts(heal_amount: int, tavern_discard: list[Card], tavern_deck: list[Card]) -> int:
    moved = 0
    while tavern_discard and moved < heal_amount:
        tavern_deck.insert(0, tavern_discard.pop())
        moved += 1
    return moved


def defend_damage(hand: list[Card], incoming: int, tavern_discard: list[Card]) -> bool:
    if incoming <= 0:
        print("You fully blocked the boss attack.")
        return True

    hand_total = sum(card.value for card in hand)
    print(f"Incoming damage: {incoming}. Hand value total: {hand_total}.")
    if hand_total < incoming:
        return False

    paid = 0
    while paid < incoming:
        display_hand(hand)
        picks = choose_indices(len(hand), f"Choose discard cards to pay damage ({paid}/{incoming} paid): ")
        discarded = remove_by_indices(hand, picks)
        if any(card.value == 0 for card in discarded):
            print("Face cards are never in hand in this version. Try again.")
            hand.extend(discarded)
            hand.sort(key=lambda c: (c.value, c.suit))
            continue
        value = sum(card.value for card in discarded)
        paid += value
        tavern_discard.extend(discarded)
        print(f"Discarded: {', '.join(card.short() for card in discarded)} (+{value})")

    return True


def game_loop() -> None:
    tavern_deck = make_tavern_deck()
    tavern_discard: list[Card] = []
    bosses = make_boss_deck()
    defeated: list[Card] = []
    hand: list[Card] = []

    draw_cards(tavern_deck, hand, HAND_LIMIT)

    boss = bosses.pop()
    boss_hp = BOSS_HEALTH[boss.rank]

    while True:
        print("\n" + "=" * 62)
        print(f"Boss: {boss} | HP: {boss_hp} | Attack: {BOSS_ATTACK[boss.rank]}")
        print(
            f"Bosses left (including current): {len(bosses) + 1} | "
            f"Defeated: {len(defeated)}"
        )
        print(f"Tavern deck: {len(tavern_deck)} | Tavern discard: {len(tavern_discard)}")

        if not hand:
            print("Your hand is empty. You lose.")
            return

        display_hand(hand)
        picks = choose_indices(len(hand), "Play card(s) by number (same value): ")
        played = remove_by_indices(hand, picks)

        if not validate_play(played):
            print("Invalid play: all played cards must share the same numeric value.")
            hand.extend(played)
            hand.sort(key=lambda c: (c.value, c.suit))
            continue

        suit_totals = {suit: 0 for suit in SUITS}
        for card in played:
            suit_totals[card.suit] += card.value

        base_damage = sum(card.value for card in played)
        damage = base_damage
        if suit_totals["Clubs"] > 0 and boss.suit != "Clubs":
            damage *= 2

        shield = 0
        if boss.suit != "Spades":
            shield = suit_totals["Spades"]

        print(f"Played: {', '.join(card.short() for card in played)}")
        print(f"Base damage: {base_damage}")
        if damage != base_damage:
            print(f"Clubs effect activated: damage doubled to {damage}")

        if suit_totals["Hearts"] > 0 and boss.suit != "Hearts":
            moved = apply_hearts(suit_totals["Hearts"], tavern_discard, tavern_deck)
            print(f"Hearts effect: recycled {moved} card(s) from discard to tavern deck")

        tavern_discard.extend(played)

        boss_hp -= damage
        if boss_hp <= 0:
            print(f"You defeated {boss}!")
            defeated.append(boss)

            if not bosses:
                print("\nAll bosses defeated. You win! 👑")
                return

            boss = bosses.pop()
            boss_hp = BOSS_HEALTH[boss.rank]
            print(f"Next boss appears: {boss} (HP {boss_hp})")
        else:
            incoming = max(0, BOSS_ATTACK[boss.rank] - shield)
            if shield > 0:
                print(f"Spades effect blocked {shield} damage.")
            if not defend_damage(hand, incoming, tavern_discard):
                print("You cannot pay the incoming damage. You lose.")
                return

        if suit_totals["Diamonds"] > 0 and boss.suit != "Diamonds":
            drew = draw_cards(tavern_deck, hand, suit_totals["Diamonds"])
            print(f"Diamonds effect: drew {drew} card(s).")


def main() -> None:
    print("Welcome to Single-Player Regicide (Terminal Edition)!\n")
    show = input("Show rules? (y/n): ").strip().lower()
    if show in {"y", "yes"}:
        print_rules()
    print("Tip: type q at any prompt to quit.\n")
    try:
        game_loop()
    except SystemExit as exc:
        print(exc)


if __name__ == "__main__":
    main()
