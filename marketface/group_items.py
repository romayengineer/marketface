
#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marketface import database

attributes = ("model", "cpu", "memory", "disk", "screen", "ciclos", "year_bought", "year_model")


groups = {}
for record in database.get_all():
    if not record.reviewed:
        continue
    item_attrs = []
    for attr in attributes:
        val = getattr(record, attr)
        item_attrs.append(val)
        if not val:
            continue
        # print(attr, val)
    # print()
    item_attrs = tuple(item_attrs)
    if item_attrs not in groups:
        groups[item_attrs] = {
            "count": 1,
            "price": record.price_ars,
        }
    else:
        groups[item_attrs]["count"] += 1
        groups[item_attrs]["price"] += record.price_ars

for group, data in groups.items():
    print(group, data["count"], data["price"] / data["count"])