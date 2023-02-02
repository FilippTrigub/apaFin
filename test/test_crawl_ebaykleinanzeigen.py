import pytest

from apaFin.crawl_ebaykleinanzeigen import CrawlEbayKleinanzeigen
from utils.config import StringConfig

DUMMY_CONFIG = """
urls:
  - https://www.ebay-kleinanzeigen.de/s-wohnung-mieten/muenchen/anbieter:privat/anzeige:angebote/preis:600:1000
    """

TEST_URL = 'https://www.ebay-kleinanzeigen.de/s-wohnung-mieten/berlin/preis:1000:1500/c203l3331+wohnung_mieten.qm_d:70,+wohnung_mieten.zimmer_d:2'

@pytest.fixture
def crawler():
    return CrawlEbayKleinanzeigen(StringConfig(string=DUMMY_CONFIG))

def test_crawler(crawler):
    soup = crawler.get_page(TEST_URL)
    assert soup is not None
    entries = crawler.extract_data(soup)
    assert entries is not None
    assert len(entries) > 0
    assert entries[0]['id'] > 0
    assert entries[0]['url'].startswith("https://www.ebay-kleinanzeigen.de/s-anzeige")
    for attr in [ 'title', 'price', 'size', 'rooms', 'address' ]:
        assert entries[0][attr] is not None

def test_process_expose_fetches_details(crawler):
    soup = crawler.get_page(TEST_URL)
    assert soup is not None
    entries = crawler.extract_data(soup)
    assert entries is not None
    assert len(entries) > 0
    updated_entries = [ crawler.get_expose_details(expose) for expose in entries ]
    for expose in updated_entries:
        print(expose)
        for attr in [ 'title', 'price', 'size', 'rooms', 'address', 'from' ]:
            assert expose[attr] is not None
