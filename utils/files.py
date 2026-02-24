
import csv
import os
from datetime import datetime
from dtypes import Product, Category


def save_results(products: Product, category: Category, path: str):
    all_field_keys = set()
    for product in products:
        all_field_keys.update(product.fields.keys())

    filename = '-'.join([
        category.title,
        datetime.now().strftime("%Y%m%dT%H%M%S"),
    ]) + ".csv"
    fieldnames = sorted(all_field_keys)

    with open(os.path.join(path, filename), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for product in products:
            row = {}
            for key in all_field_keys:
                row[key] = product.fields.get(key, "")

            writer.writerow(row)
