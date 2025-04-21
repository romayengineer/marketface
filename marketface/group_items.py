
#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tabulate import tabulate
from marketface import database

# attributes = ("model", "cpu", "memory", "disk", "screen", "ciclos", "year_bought", "year_model")
# attributes = ("model", "cpu", "memory", "disk")
attributes = ("cpu", "memory", "disk")


groups = {}
all_records = database.get_all()
for record in all_records:
    if not record.reviewed:
        continue
    item_attrs = []
    for attr in attributes:
        val = getattr(record, attr)
        item_attrs.append(val)
        if not val:
            continue
    if record.price_usd < 200:
        continue
    # memory multiple of 4
    if item_attrs[1] % 8 != 0:
        item_attrs[1] = 8 * round(item_attrs[1] / 8)
    # disk multiple of 32
    if item_attrs[2] % 32 != 0:
        item_attrs[2] = 32 * round(item_attrs[2] / 32)
    item_attrs = tuple(item_attrs)
    if item_attrs not in groups:
        groups[item_attrs] = {
            "count": 1,
            "price": record.price_usd,
            "min": record.price_usd,
            "max": record.price_usd,
        }
    else:
        groups[item_attrs]["count"] += 1
        groups[item_attrs]["price"] += record.price_usd
        groups[item_attrs]["min"] = min(record.price_usd, groups[item_attrs]["min"])
        groups[item_attrs]["max"] = max(record.price_usd, groups[item_attrs]["max"])

rows = []
for group, data in groups.items():
    # print(group, data["count"], data["min"], round(data["price"] / data["count"], 2), data["max"],)
    if not group[0] or not group[1] or not group[2]:
        continue
    rows.append(list(group) + [
        data["count"],
        round(data["min"]),
        round(data["price"] / data["count"]),
        round(data["max"]),
    ])

headers = list(attributes) + ["count", "min", "average", "max"]
# print(headers)
# print(rows)
rows = sorted(rows, key=lambda x: x[5])
in_group = sum(map(lambda x: x[3], rows))
total = len(list(filter(lambda x: x.reviewed, all_records)))
print(tabulate(rows, headers, tablefmt="grid"))
print()
print("Total in Groups: ", in_group)
print("Reviewed Records: ", total)
print("Percentage: ", round(100 * in_group / total, 2), "%")