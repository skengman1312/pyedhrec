# PyEDHRec

## Overview
This is a python wrapper around the excellent [EDHREC](https://edhrec.com/) website. Currently, EDHREC does not provide an API 
so the intent of this library is to enable people to build automated tooling around the useful information EDHREC provides.

## Installation
This package is available on PyPI and can be installed with pip
```bash
pip install pyedhrec
```

## Usage
Create an instance of the edhrec client
```python
from edhrec import EDHRec


edhrec = EDHRec()

# Reference cards by the exact card name, the library will format as needed
miirym = "Miirym, Sentinel Wyrm"

# Get basic card details
details = edhrec.get_card_details(miirym)

# Get details for a list of cards
card_list = edhrec.get_card_list(["Pongify", "Farseek"])

# Get an edhrec.com link for a given card
miirym_link = edhrec.get_card_link(miirym)

# Get combos for a card
miirym_combos = edhrec.get_card_combos(miirym)

# Get commander data 
miirym_commander_data = edhrec.get_commander_data(miirym)

# Get cards commonly associated with a commander
miirym_cards = edhrec.get_commander_cards(miirym)

# Get the average decklist for a commander
miirym_avg_deck = edhrec.get_commanders_average_deck(miirym)

# Get known deck lists for a commander
miirym_decks = edhrec.get_commander_decks(miirym)

# This library provides several methods to get specific types of recommended cards
new_cards = edhrec.get_new_cards(miirym)
high_synergy_cards = edhrec.get_high_synergy_cards(miirym)

# Get all top cards
top_cards = edhrec.get_top_cards(miirym)

# Get specific top cards by type
top_creatures = edhrec.get_top_creatures(miirym)
top_instants = edhrec.get_top_instants(miirym)
top_sorceries = edhrec.get_top_sorceries(miirym)
top_enchantments = edhrec.get_top_enchantments(miirym)
top_artifacts = edhrec.get_top_artifacts(miirym)
top_mana_artifacts = edhrec.get_top_mana_artifacts(miirym)
top_battles = edhrec.get_top_battles(miirym)
top_planeswalkers = edhrec.get_top_planeswalkers(miirym)
top_utility_lands = edhrec.get_top_utility_lands(miirym)
top_lands = edhrec.get_top_lands(miirym)

# Iterate over known decklists for a commander
for list in edhrec.get_commander_decklists(miirym):
    next_deck = list

# All known decklists for a commander 
all = list(edhrec.get_commander_decklists(miirym))

# Get top commanders by timeframe as generator (default number is 100)
week = edhrec.get_top_commanders_by_timeframe(time_frame="week")
all_times = edhrec.get_top_commanders_by_timeframe()

# Get top commanders by color identity as generator (default number is 100)
mono_white = edhrec.get_top_commanders_by_color(colors=["w"])
colorless = edhrec.get_top_commanders_by_color(colors=["c"])
simic = edhrec.get_top_commanders_by_color(colors=["u", "g"])
izzet = edhrec.get_top_commanders_by_color(colors=["u", "r"])
esper = edhrec.get_top_commanders_by_color(colors=["u", "w", "b"])
five_colors = edhrec.get_top_commanders_by_color(colors=["u", "w", "b", "g", "r"])

```

## Caching
To avoid excessive requests to edhrec.com this library uses in-memory caching for card retrieval methods. Each time you run 
a script using this library we'll cache the results for any given card. If you request the card again during the same execution we 
will use the cached value until the cache expires (defaults to 24 hours). If you use a long running script know that card data will only 
be updated once a day. Due to the nature of the game not changing often this should normally not cause issues and will help alleviate 
excessive traffic to EDHREC servers.