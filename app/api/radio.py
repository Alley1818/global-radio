from pyradios import RadioBrowser

rb = RadioBrowser()

def radio_search(name: str = "BBC Radio 1", exact: bool = False):
    results = rb.search(name=name, name_exact=exact)
    return results
