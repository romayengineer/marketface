from itertools import combinations
from typing import List, Any
from json import dumps


def power_set(elements: List) -> List[List[Any]]:
    # Generate all combinations of lengths 0 to len(elements)
    result = [
        list(combo)
        for r in range(len(elements) + 1)
        for combo in combinations(elements, r)
    ]
    return result


def power_set_length(n: int) -> int:
    return 2 ** n


class LaptopAttributes:

    attributes = ["model", "cpu", "memory", "disk", "screen", "year_bought"]

    def __init__(
            self,
            price_usd: float,
            model: str = "",
            cpu: str = "",
            memory: float = 0,
            disk: float = 0,
            screen: float = 0,
            year_bought: float = 0,
        ):
        self.model = model
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.screen = screen
        self.price_usd = price_usd
        self.year_bought = year_bought

    def print(self):
        attrs = {attr: getattr(self, attr) for attr in LaptopAttributes.attributes}
        attrs["price_usd"] = self.price_usd
        print(dumps(attrs))


def get_products_from_power_set(record: LaptopAttributes, power_set: List[List[str]]) -> List[LaptopAttributes]:
    power_set_of_products = []
    for set_in in power_set:
        new_product = LaptopAttributes(record.price_usd)
        for attr in set_in:
            setattr(new_product, attr, getattr(record, attr))
        power_set_of_products.append(new_product)
    return power_set_of_products


def power_set_of_product(record: LaptopAttributes) -> List[LaptopAttributes]:
    power_set_of_attributes = power_set(LaptopAttributes.attributes)
    return get_products_from_power_set(record, power_set_of_attributes)


def get_known_attrs(record: LaptopAttributes) -> List[str]:
    known_attrs: List[str] = []
    for attr in LaptopAttributes.attributes:
        # if attribute is 0 or "" (unknown) is ignored
        if not getattr(record, attr):
            continue
        known_attrs.append(attr)
    return known_attrs


def power_set_of_known_attrs(record: LaptopAttributes) -> List[LaptopAttributes]:
    known_attrs = get_known_attrs(record)
    power_set_of_attributes = power_set(known_attrs)
    return get_products_from_power_set(record, power_set_of_attributes)


def assert_power_set():
    attributes = ["model", "cpu", "memory", "disk", "screen"]
    power_set_of_attributes = power_set(attributes)

    if len(power_set_of_attributes) != power_set_length(len(attributes)):
        raise Exception("Invalid Power Set Lenght")

    # Example usage
    for set_in in power_set_of_attributes:
        print(set_in)


def main():
    # assert_power_set()
    product = LaptopAttributes(
        price_usd = 500,
        model = "",
        cpu = "",
        memory = 0,
        disk = 512,
        screen = 13,
    )

    power_set_of_product_list = power_set_of_known_attrs(product)

    for new_product in power_set_of_product_list:
        new_product.print()

    print(len(power_set_of_product_list))


if __name__ == "__main__":
    main()