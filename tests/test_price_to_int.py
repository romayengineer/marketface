import unittest

from marketface.play_dynamic import price_str_to_int


def number_to_str(number: int, sep: str) -> str:
    """
    turns an int to an str in the most accepted format in the world
    use dot to separate 3 digits and comma to separate decimals
    """
    numberStr = str(number)
    reversedNumberStr = numberStr[::-1]
    # print(f"reversedNumberStr: {reversedNumberStr}")
    # add first digit
    reversedFormatedNumberStr = reversedNumberStr[0]
    # skip first digit
    for i in range(1, len(reversedNumberStr)):
        # if 3rd number add dot
        if i % 3 == 0:
            reversedFormatedNumberStr += sep
        reversedFormatedNumberStr += reversedNumberStr[i]
    # print(f"reversedFormatedNumberStr: {reversedFormatedNumberStr}")
    formatedNumberStr = reversedFormatedNumberStr[::-1]
    return formatedNumberStr

def number_to_str_dot(number: int) -> str:
    return number_to_str(number, ".")

def number_to_str_comma(number: int) -> str:
    return number_to_str(number, ",")


class TestPriceStrToInt(unittest.TestCase):

    def test_number_to_str_dot(self):
        self.assertEqual(number_to_str_dot(123456), "123.456")
        self.assertEqual(number_to_str_dot(1234567), "1.234.567")
        self.assertEqual(number_to_str_dot(12345678), "12.345.678")
        self.assertEqual(number_to_str_dot(123456789), "123.456.789")
        self.assertEqual(number_to_str_dot(1234567890), "1.234.567.890")

    def test_number_to_str_comma(self):
        self.assertEqual(number_to_str_comma(123456), "123,456")
        self.assertEqual(number_to_str_comma(1234567), "1,234,567")
        self.assertEqual(number_to_str_comma(12345678), "12,345,678")
        self.assertEqual(number_to_str_comma(123456789), "123,456,789")
        self.assertEqual(number_to_str_comma(1234567890), "1,234,567,890")

    def test_price_str_to_int_1(self):
        priceReal = 123456
        priceFormated = number_to_str_dot(priceReal)
        priceParsed = price_str_to_int(priceFormated)
        print(f"priceFormated: {priceFormated}")
        print(f"priceParsed: {priceParsed}")
        self.assertIsNotNone(priceParsed)
        self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_2(self):
        # TODO fix price_str_to_int
        priceReal = 123456
        priceFormated = number_to_str_dot(priceReal)*2
        priceParsed = price_str_to_int(priceFormated)
        print(f"priceFormated: {priceFormated}")
        print(f"priceParsed: {priceParsed}")
        self.assertIsNotNone(priceParsed)
        self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_3(self):
        priceReal = 123456
        priceFormated = ("ARS"+number_to_str_comma(priceReal))*2
        priceParsed = price_str_to_int(priceFormated)
        print(f"priceFormated: {priceFormated}")
        print(f"priceParsed: {priceParsed}")
        self.assertIsNotNone(priceParsed)
        self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_4(self):
        # TODO fix price_str_to_int
        priceReal = 1234567
        priceFormated = ("$"+number_to_str_comma(priceReal))*2
        priceParsed = price_str_to_int(priceFormated)
        print(f"priceFormated: {priceFormated}")
        print(f"priceParsed: {priceParsed}")
        self.assertIsNotNone(priceParsed)
        self.assertEqual(priceReal, priceParsed)