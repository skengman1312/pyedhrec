import json
import re
import requests


class EDHRec:
    def __init__(self, cookies=None):
        self.cookies = cookies
        self.session = requests.Session()
        if self.cookies:
            self.session.cookies = self.get_cookie_jar(cookies)
        self.session.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }
        self.base_url = "https://edhrec.com"
        self._json_base_url = "https://json.edhrec.com/cards/"
        self._api_base_url = f"{self.base_url}/api"
        self.default_build_id = "mI7k8IZ23x74LocK_h-qe"
        self.current_build_id = None

    @staticmethod
    def get_cookie_jar(cookie_str):
        if cookie_str.startswith("userState="):
            cookie_str = cookie_str.split("userState=")[1]

        d = {
            "userState": cookie_str
        }
        cookie_jar = requests.cookies.cookiejar_from_dict(d)
        return cookie_jar

    @staticmethod
    def format_card_name(card_name):
        # card names are all lower case
        card_name = card_name.lower()
        # Spaces need to be converted to underscores
        card_name = card_name.replace(" ", "-")
        # remove apostrophes
        card_name = card_name.replace("'", "")
        # remove commas
        card_name = card_name.replace(",", "")
        return card_name

    def _get(self, uri, query_params=None, return_type="json"):
        res = self.session.get(uri, params=query_params)
        res.raise_for_status()
        if return_type == "json":
            res_json = res.json()
            return res_json
        else:
            return res.content

    def get_build_id(self):
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

    def _build_nextjs_uri(self, endpoint, card_name, slug=None, theme=None, budget=None):
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
    def _get_nextjs_data(response):
        if "pageProps" in response:
            return response.get("pageProps", {}).get("data")

    def get_card_list(self, card_list):
        uri = f"{self._api_base_url}/cards"
        req_body = {
            "format": "dict",
            "names": card_list
        }
        res = self.session.post(uri, json=req_body)
        res.raise_for_status()
        res_json = res.json()
        return res_json

    def get_card_details(self, card_name):
        formatted_card_name = self.format_card_name(card_name)
        uri = f"{self._json_base_url}/{formatted_card_name}"
        res = self._get(uri)
        return res

    def get_card_combos(self, card_name):
        combo_uri, params = self._build_nextjs_uri("combos", card_name)
        res = self._get(combo_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

    def get_combo_url(self, combo_url):
        uri = f"{self.base_url}"
        if uri.startswith("/"):
            uri += combo_url
        else:
            uri += f"/{combo_url}"
        res = self._get(uri)
        return res

    def get_commander_data(self, card_name):
        commander_uri, params = self._build_nextjs_uri("commanders", card_name)
        res = self._get(commander_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

    def get_commanders_average_deck(self, card_name, budget=None):
        average_deck_uri, params = self._build_nextjs_uri("average-decks", card_name, budget=budget)
        res = self._get(average_deck_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

    def get_commander_decks(self, card_name, budget=None):
        average_deck_uri, params = self._build_nextjs_uri("decks", card_name, budget=budget)
        res = self._get(average_deck_uri, query_params=params)
        data = self._get_nextjs_data(res)
        return data

# edhrec = EDHRec()
# cl = edhrec.get_card_list(["pongify", "farseek"])
# coms = edhrec.get_card_combos("Miirym, Sentinel Wyrm")
# com_m = edhrec.get_combo_url('/combos/gur/380-703-2557')