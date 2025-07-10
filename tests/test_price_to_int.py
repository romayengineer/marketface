import unittest

from marketface.page.facebook import price_str_to_int


def number_to_str(number: int, sep: str) -> str:
    """
    turns an int to an str in the most accepted format in the world
    use dot to separate 3 digits and comma to separate decimals
    """
    numberStr = str(number)
    reversedNumberStr = numberStr[::-1]
    # add first digit
    reversedFormatedNumberStr = reversedNumberStr[0]
    # skip first digit
    for i in range(1, len(reversedNumberStr)):
        # if 3rd number add dot
        if i % 3 == 0:
            reversedFormatedNumberStr += sep
        reversedFormatedNumberStr += reversedNumberStr[i]
    formatedNumberStr = reversedFormatedNumberStr[::-1]
    return formatedNumberStr

def number_to_str_dot(number: int) -> str:
    return number_to_str(number, ".")

def number_to_str_comma(number: int) -> str:
    return number_to_str(number, ",")

test_numbers = [
    (0, "0", "0"),
    (1, "1", "1"),
    (12, "12", "12"),
    (123, "123", "123"),
    (1234, "1.234", "1,234"),
    (12345, "12.345", "12,345"),
    (123456, "123.456", "123,456"),
    (1234567, "1.234.567", "1,234,567"),
    (12345678, "12.345.678", "12,345,678"),
    (123456789, "123.456.789", "123,456,789"),
    (1234567890, "1.234.567.890", "1,234,567,890"),
]


class TestPriceStrToInt(unittest.TestCase):

    def test_number_to_str_dot(self):
        for price, dot, _ in test_numbers:
            self.assertEqual(number_to_str_dot(price), dot)

    def test_number_to_str_comma(self):
        for price, _, comma in test_numbers:
            self.assertEqual(number_to_str_comma(price), comma)

    def test_price_str_to_int_single_dot(self):
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_dot(priceReal)
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_single_comma(self):
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_comma(priceReal)
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_twice_dot(self):
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_dot(priceReal)
            # TODO if priceFormated has less than or equal to 3 digits
            # it has no sep and we get double
            double = False
            if len(priceFormated) <= 3:
                double = True
            priceFormated = priceFormated * 2
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            if double:
                # TODO the fix is the selector we get two prices because of current and previous price
                self.assertEqual(int(f"{priceReal}{priceReal}"), priceParsed)
            else:
                self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_twice_comma(self):
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_comma(priceReal)
            # TODO if priceFormated has less than or equal to 3 digits
            # it has no sep and we get double
            double = False
            if len(priceFormated) <= 3:
                double = True
            priceFormated = priceFormated * 2
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            if double:
                # TODO the fix is the selector we get two prices because of current and previous price
                self.assertEqual(int(f"{priceReal}{priceReal}"), priceParsed)
            else:
                self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_twice_dot_sign(self):
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_dot(priceReal)
            priceFormated = f"ARS{priceFormated}" * 2
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            self.assertEqual(priceReal, priceParsed)
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_dot(priceReal)
            priceFormated = f"${priceFormated}" * 2
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_twice_comma_sign(self):
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_comma(priceReal)
            priceFormated = f"ARS{priceFormated}" * 2
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            self.assertEqual(priceReal, priceParsed)
        for priceReal, _, _ in test_numbers:
            priceFormated = number_to_str_comma(priceReal)
            priceFormated = f"${priceFormated}" * 2
            priceParsed = price_str_to_int(priceFormated)
            self.assertIsNotNone(priceParsed)
            self.assertEqual(priceReal, priceParsed)

    def test_price_str_to_int_return_none(self):
        self.assertIsNone(price_str_to_int("NOT-A-NUMBER"))
        self.assertIsNone(price_str_to_int("ARS"))
        self.assertIsNone(price_str_to_int("$..."))