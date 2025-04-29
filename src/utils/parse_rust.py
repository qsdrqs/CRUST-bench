from pathlib import Path
import json
from tqdm import tqdm
from tree_sitter import Language, Parser
import sys
import os
import re

# Build and include the Rust language library
Language.build_library(
    "rust_build/my-languages.so",
    ["./resources/tree-sitter-rust"],
)

RUST_LANGUAGE = Language("rust_build/my-languages.so", "rust")
EMPTY_MAIN_STRING = 'fn main() {\n    println!("Hello, world!");\n}'
# Initialize the parser
PARSER = Parser()
PARSER.set_language(RUST_LANGUAGE)


def function_signture_builder(rust_code):
    # Parse the Rust code and get the root node
    tree = PARSER.parse(bytes(rust_code, "utf-8"))
    root_node = tree.root_node
    return traverse(root_node, rust_code)


def traverse(node, code, level=0):
    content = ""
    for child in node.children:
        if child.type == "struct_item":  # Struct (class) definition
            content += child.text.decode("utf-8") + "\n"
        if child.type == "enum_item":  # Enum definition
            content += child.text.decode("utf-8") + "\n"
        if child.type == "impl_item":  # Impl block
            # Extract struct (class) name
            struct_name = child.child_by_field_name("type").text.decode("utf-8")
            content += f"impl {struct_name} {{\n"

            # Traverse to find functions within the impl
            for impl_child in child.children:
                if impl_child.type == "declaration_list":
                    for decl_child in impl_child.children:
                        if decl_child.type == "function_item":
                            content += print_function_signature(
                                get_function_parameters(decl_child, code)
                            )
                if impl_child.type == "function_item":
                    content += print_function_signature(
                        get_function_parameters(impl_child, code)
                    )

            content += f"}}\n"

        elif child.type == "function_item":  # Standalone function
            content += print_function_signature(get_function_parameters(child, code))

        # Recurse to explore nested structures if any
        # traverse(child, code, level + 1)

    return content


def print_function_signature(func_res):
    arguments = [f["name"] + ": " + f["type"] for f in func_res["arguments"]]
    if func_res["return_type"] != "":
        return f"  fn {func_res['function_name']}({', '.join(arguments)}) -> {func_res['return_type']}\n"
    else:
        return (
            f"  fn {func_res['function_name']}({', '.join(arguments)})\n"
        )


def get_function_parameters(fn_node, code):
    # Extract function name
    fn_name = fn_node.child_by_field_name("name").text.decode("utf-8")

    # Extract function parameters and return type
    params_text = fn_node.child_by_field_name("parameters").text.decode("utf-8")
    params_node = fn_node.child_by_field_name("parameters")
    params = [t for t in params_node.children if t.type == "parameter"]
    # reference types not accounted for
    param_dict = []
    for p in params:
        name = p.child_by_field_name("pattern").text.decode("utf-8")
        ret_type = p.child_by_field_name("type")
        if not ret_type:
            ret_type = p.child_by_field_name("reference_type").text.decode("utf-8")
        elif ret_type:
            ret_type = ret_type.text.decode("utf-8")
        else:
            raise Exception("Type not found")
        param_dict.append({"name": name, "type": ret_type})

    # param_dict = [{"name": p.child_by_field_name("identifier").text.decode("utf-8"), "type": p.child_by_field_name("type").text.decode("utf-8")} for p in params]
    # Extract return type if it exists
    return_type_node = fn_node.child_by_field_name("return_type")
    return_type = ""
    if return_type_node:
        if type(code) == bytes:
            return_type = code[
                return_type_node.start_byte : return_type_node.end_byte
            ].decode("utf-8")
        else:
            return_type = code[return_type_node.start_byte : return_type_node.end_byte]

    # Print function signature in the required format
    # parameters = params_text.strip('(').strip(')').split(", ")
    return {
        "function_name": fn_name,
        "arguments": param_dict,
        "return_type": return_type,
    }


def get_rust_functions(code):
    # Parse the Rust code and get the root node
    tree = PARSER.parse(code.encode())
    root_node = tree.root_node
    return get_rust_functions_util(root_node, code)


def get_rust_functions_util(node, code):
    content = []
    
    for child in node.children:
        if child.type=='mod_item':
            content.extend(get_rust_functions_util(child, code))
        if child.type == "declaration_list":
            content.extend(get_rust_functions_util(child, code))
        if child.type == "impl_item":  # Impl block
            # Extract struct (class) name
            struct_name = child.child_by_field_name("type").text.decode("utf-8")

            # Traverse to find functions within the impl
            for impl_child in child.children:
                if impl_child.type == "declaration_list":
                    for decl_child in impl_child.children:
                        if decl_child.type == "function_item":
                            content.append(get_function_parameters(decl_child, code))
                if impl_child.type == "function_item":
                    content.append(get_function_parameters(impl_child, code))

        elif child.type == "function_item":  # Standalone function
            content.append(get_function_parameters(child, code))
    return content


if __name__ == "__main__":
    rust_code = """
    use crate::card::card::{Card, CardDeck, CardHand, CardRank, CardSuitRank, ItrAction};

pub mod razz_simulation {
use super::*;

const RAZZ_CARD_IN_HAND_COUNT: usize = 7;

pub struct DecidedCards {
pub my_card_count: u8,
pub my_cards: [Option<Card>; 3],
pub opponent_card_count: u8,
pub opponent_cards: [Option<Card>; 7],
}

pub type RankListener<T> = fn(&mut T, CardRank);

pub fn simulate_razz_game<T>(decided_cards: &DecidedCards, game_count: u64, arg: &mut T, listener: RankListener<T>) -> i32 {
let mut my_hand = match CardHand::create_hand(RAZZ_CARD_IN_HAND_COUNT as u8, sort_card_by_rank) {
Some(hand) => hand,
None => {
eprintln!("Cannot create a hand");
return 1;
}
};

for _ in 0..game_count {
let mut deck = match CardDeck::create_shuffled_deck() {
Some(deck) => deck,
None => {
eprintln!("Cannot create a shuffled deck");
return 1;
}
};

strip_deck(&mut deck, decided_cards);
complete_hand(&mut my_hand, decided_cards, &mut deck);
listener(arg, get_razz_rank(&mut my_hand));
my_hand.reset_hand();
}

0
}

pub fn strip_deck(deck: &mut CardDeck, decided_cards: &DecidedCards) {
for i in 0..decided_cards.my_card_count as usize {
if let Some(card) = &decided_cards.my_cards[i] {
deck.strip_card_from_deck(card.get_card_suit_rank());
}
}

for i in 0..decided_cards.opponent_card_count as usize {
if let Some(card) = &decided_cards.opponent_cards[i] {
deck.strip_card_from_deck(card.get_card_suit_rank());
}
}
}

pub fn complete_hand(my_hand: &mut CardHand, decided_cards: &DecidedCards, deck: &mut CardDeck) {
for i in 0..decided_cards.my_card_count as usize {
my_hand.insert_into_hand(&decided_cards.my_cards[i]);
}

let remaining = RAZZ_CARD_IN_HAND_COUNT - decided_cards.my_card_count as usize;
for _ in 0..remaining {
if let Some(card) = deck.deal_from_deck() {
my_hand.insert_into_hand(&Some(card));
}
}
}

fn duplicated_rank_remover(_len: u64, pos: u64, c: &Option<Card>) -> ItrAction {
static mut PREV_RANK: CardRank = CardRank::InvalidRank;

if let Some(card) = c {
let curr_rank = card.get_card_rank();

if pos == 0 {
unsafe { PREV_RANK = curr_rank; }
return ItrAction::Continue;
}

if unsafe { PREV_RANK == curr_rank } {
return ItrAction::RemoveAndContinue;
}

unsafe { PREV_RANK = curr_rank; }
}

ItrAction::Continue
}

fn length_trimmer(_len: u64, pos: u64, _c: &Option<Card>) -> ItrAction {
if pos >= 5 {
return ItrAction::RemoveAndContinue;
}
ItrAction::Continue
}

fn get_razz_rank(hand: &mut CardHand) -> CardRank {
// First remove duplicated ranks
hand.iterate_hand(duplicated_rank_remover);

// Check if we have enough cards
if hand.count_cards_in_hand() < 5 {
return CardRank::InvalidRank;
}

// Trim to 5 cards
hand.iterate_hand(length_trimmer);

// Return the highest rank (worst card in Razz)
hand.get_max_rank_of_hand()
}

fn sort_card_by_rank(before: &Option<Card>, new: &Option<Card>, after: &Option<Card>) -> i32 {
if let Some(new_card) = new {
let new_rank = new_card.get_card_rank();

if after.is_none() ||
((before.is_none() || new_rank > before.unwrap().get_card_rank()) &&
new_rank <= after.unwrap().get_card_rank()) {
return 1;
}
}
0
}
}

    """
    print(get_rust_functions(rust_code))
    print(function_signture_builder(rust_code))
