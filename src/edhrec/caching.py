from datetime import datetime, timedelta
from typing import Callable


def generate_wrapped_func(function: Callable, cache: dict) -> Callable:
    def wrapper(*args, func: Callable = function, wrapped_cache: dict = cache):
        now = datetime.utcnow()
        if args in wrapped_cache:
            if now >= wrapped_cache[args].get("expiry"):
                result = func(*args)
                expiry = now + timedelta(seconds=86400)
                wrapped_cache[args] = {
                    "result": result,
                    "expiry": expiry
                }

            return wrapped_cache[args].get("result")
        else:
            result = func(*args)
            expiry = now + timedelta(seconds=86400)
            wrapped_cache[args] = {
                "result": result,
                "expiry": expiry
            }
            return result
    return wrapper


def commander_cache(func):
    cmdr_cache = {}
    wrapper_func = generate_wrapped_func(func, cmdr_cache)
    return wrapper_func


def card_detail_cache(func):
    detail_cache = {}
    wrapper_func = generate_wrapped_func(func, detail_cache)
    return wrapper_func


def combo_cache(func):
    combo_cache = {}
    wrapper_func = generate_wrapped_func(func, combo_cache)
    return wrapper_func


def average_deck_cache(func):
    avg_deck_cache = {}
    wrapper_func = generate_wrapped_func(func, avg_deck_cache)
    return wrapper_func


def deck_cache(func):
    deck_cache = {}
    wrapper_func = generate_wrapped_func(func, deck_cache)
    return wrapper_func