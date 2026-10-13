import unittest

from src.research import find_related_candidates, normalize_date, parse_feed


class ResearchTests(unittest.TestCase):
    def test_rss_parser_rejects_unapproved_hosts(self):
        xml = """<rss><channel>
        <item><title>Safe title</title><link>https://www.nasa.gov/a</link><description>Official science</description><pubDate>Tue, 13 Oct 2026 10:00:00 GMT</pubDate></item>
        <item><title>Unsafe title</title><link>https://example.com/b</link><description>Not approved</description></item>
        </channel></rss>"""
        items = parse_feed(xml, "NASA", ["www.nasa.gov"])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Safe title")

    def test_related_candidates_are_discovery_only(self):
        items = [
            {"host": "www.nasa.gov", "url": "https://www.nasa.gov/a", "title": "Ocean climate research", "summary": "Ocean climate research measures changing temperatures"},
            {"host": "oceanservice.noaa.gov", "url": "https://oceanservice.noaa.gov/b", "title": "Ocean climate research", "summary": "Ocean climate research observes coastal temperatures"},
        ]
        pairs = find_related_candidates(items)
        self.assertTrue(pairs)
        self.assertEqual(pairs[0]["status"], "candidate_only_not_fact_checked")

    def test_same_host_is_not_independent(self):
        items = [
            {"host": "www.nasa.gov", "url": "https://www.nasa.gov/a", "title": "Ocean climate research", "summary": "Ocean climate research temperatures"},
            {"host": "www.nasa.gov", "url": "https://www.nasa.gov/b", "title": "Ocean climate research", "summary": "Ocean climate research temperatures"},
        ]
        self.assertEqual(find_related_candidates(items), [])

    def test_rfc822_date_is_normalized(self):
        value = normalize_date("Tue, 13 Oct 2026 10:00:00 GMT")
        self.assertTrue(value.startswith("2026-10-13T10:00:00"))

    def test_missing_date_is_not_fabricated(self):
        self.assertEqual(normalize_date("not-a-date"), "")


if __name__ == "__main__":
    unittest.main()
