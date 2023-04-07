import sqlite3
import csv
import time

lines = []

with open("Vocab_List.csv", "r") as f:
    reader = csv.reader(f, delimiter=',', quotechar='"')

    for row in reader:
        lines.append(list(row))

headers = lines[0]
values = lines[1:]


def db_dict_factory(cursor, row):
    # Used to return database query results as dictionaries.
    # From the docs: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory

    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


db = sqlite3.connect("dictionary.db")
db.row_factory = db_dict_factory
cursor = db.cursor()

categories_query = "SELECT ID, EnglishName FROM Categories"
cursor.execute(categories_query)
categories = cursor.fetchall()

created_at = round(time.time() * 1000)  # Convert to milliseconds


for value in values:

    category_id = None
    for category in categories:
        if category["EnglishName"].lower().strip() == value[4].lower().strip():
            category_id = int(category["ID"])

    if (category_id == None):
        print(value)
        continue

    query = """INSERT INTO Words (MaoriSpelling, EnglishSpelling, YearLevelFirstEncountered, EnglishDefinition, CreatedBy, CreatedAt, CategoryID)
                            VALUES (?, ?, ?, ?, ?, ?, ?)"""
    cursor.execute(query, [value[0], value[1], value[2],
                   value[3], 1, created_at, category_id])

db.commit()
db.close()
