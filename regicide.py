#coding a game of regicide: thanks ai for a lot of the code
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import random
from typing import Iterable

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
NUMBER_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
FACE_RANKS = ["J", "Q", "K"]
BOSS_HEALTH = {"J": 20, "Q": 30, "K": 40}
BOSS_ATTACK = {"J": 10, "Q": 15, "K": 20}
HAND_LIMIT = 8
LOW_DECK_WARNING = 6


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def attack_value(self) -> int:
        if self.rank == "A":
            return 1
        if self.rank in FACE_RANKS:
            return BOSS_ATTACK[self.rank]
        return int(self.rank)

    @property
    def tank_value(self) -> int:
        if self.rank == "A":
            return 1
        if self.rank in FACE_RANKS:
            return BOSS_HEALTH[self.rank]
        return int(self.rank)

    def short(self) -> str:
        return f"{self.rank}o{self.suit[0]}"

    def __str__(self) -> str:
        names = {"A": "Ace", "J": "Jack", "Q": "Queen", "K": "King"}
        return f"{names.get(self.rank, self.rank)} of {self.suit}"


def sort_hand(hand: list[Card]) -> None:
    hand.sort(key=lambda c: (c.attack_value, SUITS.index(c.suit)))


def balanced_shuffle(cards: list[Card], max_same_suit_run: int = 2) -> list[Card]:
    """Shuffle, then reduce long suit streaks for a more balanced feel."""
    shuffled = cards.copy()
    random.shuffle(shuffled)

    run_length = 1
    for i in range(1, len(shuffled)):
        if shuffled[i].suit == shuffled[i - 1].suit:
            run_length += 1
        else:
            run_length = 1

        if run_length <= max_same_suit_run:
            continue

        swap_idx = None
        for j in range(i + 1, len(shuffled)):
            if shuffled[j].suit != shuffled[i].suit:
                swap_idx = j
                break

        if swap_idx is not None:
            shuffled[i], shuffled[swap_idx] = shuffled[swap_idx], shuffled[i]
            run_length = 1

    return shuffled


def make_tavern_deck() -> list[Card]:
    deck = [Card(rank, suit) for suit in SUITS for rank in NUMBER_RANKS]
    return balanced_shuffle(deck)


def make_boss_deck() -> deque[Card]:
    """Build bosses as Jacks->Queens->Kings, with balanced/random suit order each tier."""
    bosses: list[Card] = []
    for rank in FACE_RANKS:
        rank_cards = [Card(rank, suit) for suit in SUITS]
        bosses.extend(balanced_shuffle(rank_cards, max_same_suit_run=1))
    return deque(bosses)


def draw_cards(deck: list[Card], hand: list[Card], amount: int) -> int:
    draws = 0
    while deck and len(hand) < HAND_LIMIT and draws < amount:
        hand.append(deck.pop())
        draws += 1
    sort_hand(hand)
    return draws


def print_rules() -> None:
    print("\n=== SINGLE-PLAYER REGICIDE RULES (TERMINAL VERSION) ===")
    print("- Defeat all 12 bosses (Jacks, Queens, Kings).")
    print("- First 4 bosses are always Jacks, then Queens, then Kings.")
    print("- You start with 8 cards. Play 1+ cards of the same value.")
    print("- Attack damage is the sum of played card attack values.")
    print("- Clubs: doubles your total damage (unless the boss is Clubs).")
    print("- Spades: blocks that much boss damage this turn (unless boss is Spades).")
    print("- Hearts: recycle that many cards from discard back into tavern deck")
    print("  (unless boss is Hearts).")
    print("- Diamonds: draw that many cards (unless boss is Diamonds).")
    print("- Mixed suits combine, but do not multiply each other (e.g., 7oC+7oD => 28 dmg + 14 draws).")
    print("- Collected J/Q/K cards are playable (attack 10/15/20; tank 20/30/40 when discarded to defend).")
    print("- If boss survives, it attacks. Discard hand cards to pay damage total.")
    print("- If you cannot pay damage, you lose.")
    print("- Exact kill (20/30/40): defeated boss goes to top of tavern deck.\n")


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
    cols = 4
    chunks = [hand[i : i + cols] for i in range(0, len(hand), cols)]
    for row_idx, row in enumerate(chunks):
        cells = []
        for col_idx, card in enumerate(row):
            idx = row_idx * cols + col_idx + 1
            cells.append(f"{idx:>2}:{card.short():<4}({card.attack_value}/{card.tank_value})")
        print("  " + " | ".join(cells))

    suit_counts = Counter(card.suit[0] for card in hand)
    print(
        "  Summary: "
        f"H={suit_counts.get('H', 0)} D={suit_counts.get('D', 0)} "
        f"C={suit_counts.get('C', 0)} S={suit_counts.get('S', 0)} | "
        f"Attack/Tank totals={sum(card.attack_value for card in hand)}/{sum(card.tank_value for card in hand)}"
    )


def validate_play(played: list[Card]) -> bool:
    """Allow same-value groups, with Aces acting as wildcards."""
    if not played:
        return False

    non_aces = [card for card in played if card.rank != "A"]
    if not non_aces:
        return True

    target_value = non_aces[0].attack_value
    return all(card.attack_value == target_value for card in non_aces)


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

    hand_total = sum(card.tank_value for card in hand)
    print(f"Incoming damage: {incoming}. Hand value total: {hand_total}.")
    if hand_total < incoming:
        return False

    paid = 0
    while paid < incoming:
        display_hand(hand)
        picks = choose_indices(len(hand), f"Choose discard cards to pay damage ({paid}/{incoming} paid): ")
        discarded = remove_by_indices(hand, picks)
        value = sum(card.tank_value for card in discarded)
        paid += value
        tavern_discard.extend(discarded)
        print(f"Discarded: {', '.join(card.short() for card in discarded)} (+{value})")

    return True


def deck_warning(deck_size: int) -> str:
    if deck_size == 0:
        return "⚠️ Tavern deck empty!"
    if deck_size <= LOW_DECK_WARNING:
        return f"⚠️ Low tavern deck: {deck_size} card(s) left"
    return ""


def resolve_pending_draws(
    pending_draws: int, tavern_deck: list[Card], hand: list[Card]
) -> tuple[int, int]:
    """Auto-spend saved draws; player always draws up to hand limit when possible."""
    if pending_draws <= 0 or len(hand) >= HAND_LIMIT or not tavern_deck:
        return pending_draws, 0

    drew = draw_cards(tavern_deck, hand, pending_draws)
    return pending_draws - drew, drew


def ability_strength(played: list[Card]) -> int:
    """Suit abilities use raw played value and do not multiply each other."""
    return sum(card.attack_value for card in played)


def game_loop() -> None:
    tavern_deck = make_tavern_deck()
    tavern_discard: list[Card] = []
    bosses = make_boss_deck()
    defeated: list[Card] = []
    hand: list[Card] = []
    pending_draws = 0

    draw_cards(tavern_deck, hand, HAND_LIMIT)

    boss = bosses.popleft()
    boss_hp = BOSS_HEALTH[boss.rank]

    while True:
        pending_draws, auto_drew = resolve_pending_draws(pending_draws, tavern_deck, hand)
        if auto_drew:
            print(f"Auto-draw: drew {auto_drew} saved card(s). Pending draws: {pending_draws}.")

        print("\n" + "=" * 66)
        print(f"Boss: {boss} | HP: {boss_hp} | Attack: {BOSS_ATTACK[boss.rank]}")
        print(
            f"Bosses left (including current): {len(bosses) + 1} | "
            f"Defeated: {len(defeated)}"
        )
        print(f"Tavern deck: {len(tavern_deck)} | Tavern discard: {len(tavern_discard)}")
        warning = deck_warning(len(tavern_deck))
        if warning:
            print(warning)

        if not hand:
            print("Your hand is empty. You lose.")
            return

        display_hand(hand)
        picks = choose_indices(len(hand), "Play card(s) by number (same value): ")
        played = remove_by_indices(hand, picks)

        if not validate_play(played):
            print("Invalid play: non-Ace cards must share the same numeric value.")
            hand.extend(played)
            sort_hand(hand)
            continue

        played_suits = {card.suit for card in played}
        boss_suit = boss.suit

        base_damage = ability_strength(played)
        clubs_active = "Clubs" in played_suits and boss_suit != "Clubs"
        spades_active = "Spades" in played_suits and boss_suit != "Spades"
        hearts_active = "Hearts" in played_suits and boss_suit != "Hearts"
        diamonds_active = "Diamonds" in played_suits and boss_suit != "Diamonds"

        # Clubs doubles attack damage only; it never amplifies other suit abilities.
        damage = base_damage * 2 if clubs_active else base_damage
        shield = base_damage if spades_active else 0

        print(f"Played: {', '.join(card.short() for card in played)}")
        print(f"Base damage: {base_damage}")
        if clubs_active:
            print(f"Clubs effect activated: damage doubled to {damage}")

        if hearts_active:
            moved = apply_hearts(base_damage, tavern_discard, tavern_deck)
            print(f"Hearts effect: recycled {moved} card(s) from discard to tavern deck")

        if diamonds_active:
            pending_draws += base_damage
            print(
                f"Diamonds effect: gained {base_damage} draw(s) from raw card value "
                f"(not Club-doubled). Pending draws now {pending_draws}."
            )

        tavern_discard.extend(played)

        boss_hp -= damage
        if boss_hp <= 0:
            exact_kill = boss_hp == 0
            print(f"You defeated {boss}!")
            defeated.append(boss)
            if exact_kill:
                # draw_cards uses deck.pop(), so the top card is at the end of the list.
                tavern_deck.append(boss)
                print("Exact kill: defeated boss moved to the top of the tavern deck.")

            if not bosses:
                print("\nAll bosses defeated. You win! 👑")
                return

            boss = bosses.popleft()
            boss_hp = BOSS_HEALTH[boss.rank]
            print(f"Next boss appears: {boss} (HP {boss_hp})")
        else:
            incoming = max(0, BOSS_ATTACK[boss.rank] - shield)
            if shield > 0:
                print(f"Spades effect blocked {shield} damage.")
            if not defend_damage(hand, incoming, tavern_discard):
                print("You cannot pay the incoming damage. You lose.")
                return

        pending_draws, auto_drew = resolve_pending_draws(pending_draws, tavern_deck, hand)
        if auto_drew:
            print(f"Auto-draw: drew {auto_drew} saved card(s). Pending draws: {pending_draws}.")


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