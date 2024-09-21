
import unittest
from utils import shorten_item_url

class TestShortenItemUrl(unittest.TestCase):
    """Test the function shorten_item_url"""

    def test_shorten_item_url(self):
        """Test the shorten_item_url function"""
        # test cases
        test_cases = [
            # should return the original url
            ("/marketplace/item/123456789/asdasdd", "/marketplace/item/123456789"),
            # should return the shortened url
            ("/marketplace/item/1234567890/asdasdas", "/marketplace/item/1234567890"),
            # should return the original url
            ("/marketplace/item/asdasd", "/marketplace/item/"),
        ]
        # loop through each test case
        for test_case in test_cases:
            # get the url and the expected shortened url
            url, expected = test_case
            # call the shorten_item_url function
            shortened = shorten_item_url(url)
            print(f"url {url} -> expecter {expected}")
            # check if the shortened url is equal to the expected one
            self.assertEqual(shortened, expected)


if __name__ == "__main__":
    unittest.main()
