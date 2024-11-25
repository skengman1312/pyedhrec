import json
import re
import requests

from .caching import commander_cache, card_detail_cache, combo_cache, average_deck_cache, deck_cache
from .utils import get_random_ua


class EDHRec:
    def __init__(self, cookies: str = None):
        self.cookies = cookies
        self.session = requests.Session()
        if self.cookies:
            self.session.cookies = self.get_cookie_jar(cookies)
        self.session.headers = {
            "Accept": "application/json",
            "User-Agent": get_random_ua()
        }
        self.base_url = "https://edhrec.com"
        self._json_base_url = "https://json.edhrec.com/cards"
        self._api_base_url = f"{self.base_url}/api"
        self.default_build_id = "mI7k8IZ23x74LocK_h-qe"
        self.current_build_id = None

        self._commander_data_cache = {}

    @staticmethod
    def get_cookie_jar(cookie_str: str):
        if cookie_str.startswith("userState="):
            cookie_str = cookie_str.split("userState=")[1]

        d = {
            "userState": cookie_str
        }
        cookie_jar = requests.cookies.cookiejar_from_dict(d)
        return cookie_jar

    @staticmethod
    def format_card_name(card_name: str) -> str:
        # card names are all lower case
        card_name = card_name.lower()
        # Spaces need to be converted to underscores
        card_name = card_name.replace(" ", "-")
        # remove apostrophes
        card_name = card_name.replace("'", "")
        # remove commas
        card_name = card_name.replace(",", "")
        return card_name

    def _get(self, uri: str, query_params: dict = None, return_type: str = "json") -> dict:
        res = self.session.get(uri, params=query_params)
        res.raise_for_status()
        if return_type == "json":
            res_json = res.json()
            return res_json
        else:
            return res.content

    def get_build_id(self) -> str or None:
        home_page = self._get(self.base_url, return_type="raw")
        home_page_content = home_page.decode("utf-8")
        script_block_regex = r"<script id=\"__NEXT_DATA__\" type=\"application/json\">(.*)</script>"
        if script_match := re.findall(script_block_regex, home_page_content):
            props_str = script_match[0]
        else:
            return None
        try:
            props_data = json.loads(props_str)
            return props_data.get("buildId")
        except json.JSONDecodeError:
            return None

    def check_build_id(self):
        if not self.current_build_id:
            self.current_build_id = self.get_build_id()
            # If we couldn't get the current buildId we'll try to fall back to a known static string
            if not self.current_build_id:
                self.current_build_id = self.default_build_id
        # We have a build ID set
        return True

    def _build_nextjs_uri(self, endpoint: str, card_name: str, slug: str = None, theme: str = None, budget: str = None):
        self.check_build_id()
        formatted_card_name = self.format_card_name(card_name)
        query_params = {
            "commanderName": formatted_card_name
        }
        uri = f"{self.base_url}/_next/data/{self.current_build_id}/{endpoint}/{formatted_card_name}"

        if theme:
            uri += f"/{theme}"
            if not budget:
                query_params["themeName"] = theme

        if budget == "budget":
            uri += f"/budget.json"
            query_params["themeName"] = budget
        elif budget == "expensive":
            uri += f"/expensive.json"
            query_params["themeName"] = budget
        else:
            uri += f".json"

        if slug:
            query_params["slug"] = slug

        if endpoint == "combos":
            query_params["colors"] = formatted_card_name

        return uri, query_params

    @staticmethod
    def _get_nextjs_data(response: dict) -> dict:
        if "pageProps" in response:
            return response.get("pageProps", {}).get("data")

    def _get_cardlist_from_container(self, card_name: str, tag: str = None) -> dict:
        card_data = self.get_commander_data(card_name)
        container = card_data.get("container", {})
        json_dict = container.get("json_dict", {})
        card_lists = json_dict.get("cardlists")
        result = {}
        for cl in card_lists:
            _card_list = cl.get("cardviews")
            _header = cl.get("header")
            _tag = cl.get("tag")
            if tag:
                if _tag == tag:
                    result[_header] = _card_list
                    return result
            else:
                result[_header] = _card_list
        return result

    def get_card_list(self, card_list: list) -> dict:
        uri = f"{self._api_base_url}/cards"
        req_body = {
            "format": "dict",
            "names": card_list
        }
        res = self.session.post(uri, json=req_body)
        res.raise_for_status()
        res_json = res.json()
        return res_json

    def get_card_link(self, card_name: str) -> str:
        formatted_card_name = self.format_card_name(card_name)
        uri = f"{self.base_url}/cards/{formatted_card_name}"
        return uri

    @card_detail_cache
    def get_card_details(self, card_name: str) -> dict:
        formatted_card_name = self.format_card_name(card_name)
        uri = f"{self._json_base_url}/{formatted_card_name}"
        res = self._get(uri)
        return res

    @combo_cache
    def get_card_combos(self, card_name: str) -> dict:
        combo_uri, params = self._build_nextjs_uri("combos", card_name)
        res = self._get(combo_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

    def get_combo_url(self, combo_url: str) -> str:
        uri = f"{self.base_url}"
        if combo_url.startswith("/"):
            uri += combo_url
        else:
            uri += f"/{combo_url}"
        return uri

    @commander_cache
    def get_commander_data(self, card_name: str) -> dict:
        commander_uri, params = self._build_nextjs_uri("commanders", card_name)
        res = self._get(commander_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

    @average_deck_cache
    def get_commanders_average_deck(self, card_name: str, budget: str = None) -> dict:
        average_deck_uri, params = self._build_nextjs_uri("average-decks", card_name, budget=budget)
        res = self._get(average_deck_uri, query_params=params)
        data = self._get_nextjs_data(res)
        deck_obj = {
            "commander": card_name,
            "decklist": data.get("deck")
        }
        return deck_obj

    @deck_cache
    def get_commander_decks(self, card_name: str, budget: str = None) -> dict:
        average_deck_uri, params = self._build_nextjs_uri("decks", card_name, budget=budget)
        res = self._get(average_deck_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

    def get_commander_cards(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name)
        return card_list

    def get_new_cards(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "newcards")
        return card_list

    def get_high_synergy_cards(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "highsynergycards")
        return card_list

    def get_top_cards(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "topcards")
        return card_list

    def get_top_creatures(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "creatures")
        return card_list

    def get_top_instants(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "instants")
        return card_list

    def get_top_sorceries(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "sorceries")
        return card_list

    def get_top_artifacts(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "utilityartifacts")
        return card_list

    def get_top_mana_artifacts(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "manaartifacts")
        return card_list

    def get_top_enchantments(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "enchantments")
        return card_list

    def get_top_battles(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "battles")
        return card_list

    def get_top_planeswalkers(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "planeswalkers")
        return card_list

    def get_top_lands(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "lands")
        return card_list

    def get_top_utility_lands(self, card_name: str) -> dict:
        card_list = self._get_cardlist_from_container(card_name, "utilitylands")
        return card_list

    def get_deck_by_id(self, id: str, simplified_output: bool = False) -> dict:
        """
        Fetch full deck list from EDHREC id/urlhash using the "deckpreview" endpoint
        :param id: id/urlhash of the deck of interest
        :param simplified_output: if true the response is parsed into an eye-readable dict
        :return:
        """
        deck_by_id_uri, params = self._build_nextjs_uri("deckpreview", id)
        deck_by_id_uri = deck_by_id_uri.replace(self.format_card_name(id), id)
        res = self._get(deck_by_id_uri, query_params=params)
        data = self._get_nextjs_data(res)
        if not simplified_output:
            return data
        else:
            return {**{"Commander": [cm for cm in data["commanders"] if cm is not None]},
                    **{cl["header"]: [card["name"] for card in cl["cardviews"]]
                       for cl in data["container"]["json_dict"]["cardlists"]}}

    def get_commander_decklists(self, card_name: str, budget: str = None) -> dict:
        """
        Generator of top deck lists for card_name commander, each iteration is a single request
        :param card_name:
        :param budget:
        """
        decklists_container = self.get_commander_decks(card_name, budget)["table"]
        for dl in decklists_container:
            hash = dl["urlhash"]
            yield self.get_deck_by_id(hash, simplified_output=True)

    def _get_top_commanders(self, query: str, n: int = 100):
        top_commanders_uri, params = self._build_nextjs_uri("commanders", query)
        if len(query) == 0:
            top_commanders_uri = top_commanders_uri.replace("commanders/.json", "commanders.json")

        res = self._get(top_commanders_uri, query_params=params)
        data = self._get_nextjs_data(res)
        cardlist = data["container"]["json_dict"]["cardlists"][0]
        for i in range(n):
            local_index, global_index = i % 100, i // 100
            if (local_index == 0) and (global_index != 0):
                replace_index = top_commanders_uri.find("commander")
                top_commanders_uri = top_commanders_uri[:replace_index] + cardlist["more"]
                res = self._get(top_commanders_uri)
                cardlist = self._get_nextjs_data(res)
            yield cardlist["cardviews"][local_index]["name"]

    def get_top_commanders_by_timeframe(self, time_frame: str = "", n: int = 100):
        """
        Get list of top commanders for the specified timeframe
        :param time_frame: available time frames are week and month, leave empty for all times
        :param n: number of items to be returned, each 100 items will constitute a new request
        """
        assert time_frame in (
            "week", "month", ""), "The available time frames are week and month, leave empty for all times"
        query = time_frame
        for i in self._get_top_commanders(query=query, n=n):
            yield i

    def get_top_commanders_by_color(self, colors: list = [], n: int = 100):
        """
        Get list of top commanders for the specified color combination
        :param colors: list of color identifiers as sirings  e.g. ["w","b"] for orzhov
        :param n: number of items to be returned, each 100 items will constitute a new request
        """
        color_archetypes = {'w': 'mono-white', 'u': 'mono-blue', 'b': 'mono-black', 'r': 'mono-red', 'g': 'mono-green',
                            'c': 'colorless', 'uw': 'azorius', 'bu': 'dimir', 'br': 'rakdos', 'gr': 'gruul',
                            'gw': 'selesnya', 'bw': 'orzhov', 'ru': 'izzet', 'bg': 'golgari', 'rw': 'boros',
                            'gu': 'simic', 'buw': 'esper', 'bru': 'grixis', 'bgr': 'jund', 'grw': 'naya', 'guw': 'bant',
                            'bgw': 'abzan', 'ruw': 'jeskai', 'bgu': 'sultai', 'brw': 'mardu', 'gru': 'temur',
                            'bruw': 'yore-tiller', 'bgru': 'glint-eye', 'bgrw': 'dune-brood', 'gruw': 'ink-treader',
                            'bguw': 'witch-maw', 'bgruw': 'five-color'}  # need to find a better way
        color_sting = "".join(sorted(colors))
        assert color_sting in color_archetypes.keys(), (f"Wrong color selection, available color combinations are: \n"
                                                        f"{color_archetypes}")
        archetype = color_archetypes[color_sting]
        query = archetype
        for i in self._get_top_commanders(query=query, n=n):
            yield i
