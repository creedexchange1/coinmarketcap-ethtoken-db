from glob import glob
from itertools import groupby
import logging
import requests

from helpers import (DEFAULT_HEADERS, process_listing, read_entry,
                     write_token_entry)

CMC_LISTINGS_API_URL = "https://api.coinmarketcap.com/v2/listings/"


def get_listings():
    """
    Returns a list of CoinMarketCap-listed currencies via /v2/listings/ API endpoint.

    Returns: a list of dicts like so:
        [{'id': 1, 'name': 'Bitcoin', 'symbol': 'BTC', 'website_slug': 'bitcoin'}, ...]
    """
    r = requests.get(CMC_LISTINGS_API_URL, headers=DEFAULT_HEADERS)
    return r.json()["data"]


def map_existing_entries(files, exclude_deprecated=True):
    """
    Returns a hash keyed by CoinMarketCap asset ID with sets of Ethereum addresses
    known to be associated with that asset ID.
    """
    entries = ((entry["id"], entry["address"])
               for entry in (read_entry(fn) for fn in files)
               if not (exclude_deprecated and entry.get("_DEPRECATED", False)))

    return {
        e[0]: set(g[1] for g in e[1])
        for e in groupby(sorted(entries), key=lambda e: e[0])
    }


def main(listings):
    from time import sleep

    id_to_address = map_existing_entries(sorted(glob("tokens/0x*.yaml")))

    for listing in listings:
        sleep(12)

        result = process_listing(listing)
        if result is None:
            continue

        (updated_listing, current_addresses) = result

        existing_addresses = id_to_address[listing["id"]]
        for address in existing_addresses - current_addresses:
            logging.warning("'%s' has deprecated %s", listing["website_slug"],
                            address)
            old_listing = read_entry("tokens/{}.yaml".format(address))
            old_listing.update({"_DEPRECATED": True})
            del old_listing["address"]
            write_token_entry(address, old_listing)

        for address in current_addresses:
            write_token_entry(address, updated_listing)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    main(get_listings())
