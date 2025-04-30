#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marketface import database


def update_year():
    years_mapping = {
        "i3": 2017,
        "i5": 2017,
        "i7": 2018,
        "i9": 2018,
        "m1": 2021,
        "m2": 2022,
        "m3": 2023,
        "m4": 2024,
    }
    cpus = set(years_mapping.keys())

    all_records = database.get_all()
    for i, record in enumerate(all_records):
        if record.cpu not in cpus:
            continue
        if record.year_bought != 0:
            continue
        year_bought = years_mapping[record.cpu]
        database.update_item_by_id(record.id, {
            "yearBought": float(year_bought),
        })
        print(i, record.price_usd, record.cpu, record.year_bought, year_bought)

if __name__ == "__main__":
    update_year()