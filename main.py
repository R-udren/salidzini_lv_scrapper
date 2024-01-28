from urllib.parse import urlparse
from pprint import pprint
import sqlite3
import datetime

import requests
from bs4 import BeautifulSoup

headers = {
    'accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0'
}

DB_NAME = 'database.db'


class Item:
    def __init__(self, query, name, price, link, shop, amount, date):
        self.query = query
        self.name = name
        self.price = price
        self.link = link
        self.shop = shop
        self.amount = amount
        self.date = date

    def __str__(self):
        return f'{self.query} - {self.name} - {self.price} - {self.link} - {self.shop} - {self.amount} - {self.date}'

    def to_dict(self):
        return {
            'query': self.query,
            'name': self.name,
            'price': self.price,
            'link': self.link,
            'shop': self.shop,
            'amount': self.amount,
            'date': self.date
        }


def get_html(url, save=""):
    """Get html code from url"""
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    if save:
        with open(f'{save.replace(" ", "_")}.html', 'w', encoding='UTF-8') as file:
            file.write(r.text)
    return r.text


def get_content(html, query):
    """Get content from html code"""
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='item_box_main', itemprop='offers')
    result = []

    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for item in items:
        name = item.find('h2', class_='item_name').get_text()
        price = float(item.find('span', itemprop='price').get_text(strip=True).replace(',', '.'))
        link = item.find('a', class_='item_link')['href']
        link = f'https://www.salidzini.lv{link}'
        shop = item.find('div', class_='item_shop_name').get_text(strip=True)
        amount = item.find('div', class_='item_stock').get_text(strip=True)
        if not amount:
            amount = 0
        else:
            amount = int(amount.split(':')[1].replace(' ', '').replace('+', ''))
        result.append(Item(query, name, price, link, shop, amount, date).to_dict())
    return result


def create_db():
    """Create database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        name TEXT,
        price INTEGER,
        link TEXT,
        shop TEXT,
        amount INTEGER,
        date TEXT
    )""")
    conn.commit()


def insert_items_into_db(items):
    """Insert items into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for item_data in items:
        cursor.execute("""INSERT INTO items (query, name, price, link, shop, amount, date)
                          VALUES (?, ?, ?, ?, ?, ?, ?)""",
                       (item_data['query'], item_data['name'], item_data['price'], item_data['link'],
                        item_data['shop'], item_data['amount'], item_data['date']))
    conn.commit()
    conn.close()


def get_items_from_db():
    """Retrieve items from the database and return them as a list of dictionaries."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM items")
    fetched_items = cursor.fetchall()

    items_list = []
    for item in fetched_items:
        items_list.append({
            'query': item[1],
            'name': item[2],
            'price': item[3],
            'link': item[4],
            'shop': item[5],
            'amount': item[6],
            'date': item[7]
        })

    conn.close()
    return items_list


def main():
    if not urlparse(DB_NAME).scheme:
        create_db()

    item = input('Enter item to search: ')
    url = f'https://www.salidzini.lv/cena?q={item.replace(" ", "+")}'
    html = get_html(url, save=item)
    content = get_content(html, item)

    insert_items_into_db(content)

    print('Items from the database:')
    pprint(get_items_from_db())


if __name__ == '__main__':
    main()
