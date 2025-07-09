import os
import tempfile
import unittest

from marketface.play_dynamic import download_image


class TestDownloadImage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_name = self.temp_dir.name
        os.makedirs(os.path.join(self.temp_dir_name, "data", "images"), exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_dont_download_if_exists(self):
        href_short = "/marketplace/item/1234567890"
        file_name = href_short[1:].replace("/", "_") + ".jpg"
        path_name = os.path.join("data", "images", file_name)
        img_src = ""
        self.assertEqual(download_image(href_short, img_src), path_name)
        self.assertTrue(os.path.isfile(path_name))

    def _test_download_if_doesnt_exist(self):
        # TODO test is wrong
        file_name = os.path.join(self.temp_dir_name, "data", "images", "test.jpg")
        img_src = (
            "https://www.gravatar.com/avatar/d50c83a958d1168ba6e71576e9c333e8?s=200"
        )
        href_short = "/marketplace/item/1234567890"
        self.assertEqual(download_image(href_short, img_src), file_name)
        self.assertTrue(os.path.isfile(file_name))
