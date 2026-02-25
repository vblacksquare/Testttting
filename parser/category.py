import json

import aiohttp
import asyncio
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from dtypes import Product

from loguru import logger


class CategoryParser(ABC):
    path: str = "/base"

    def __init__(self, root: str, session: aiohttp.ClientSession, headers: dict):
        self.log = logger.bind(classname=self.__class__.__name__)
        self._root = root
        self._headers = headers
        self._session: aiohttp.ClientSession = session

    @abstractmethod
    async def _get_full_products_page(self, page: int) -> tuple[list[Product], int]:
        pass

    async def _get_products_page(self, page: int) -> list[Product]:
        products, _ = await self._get_full_products_page(page)
        self.log.info(f"Parsed page {page}: got {len(products)} products")
        return products

    async def get_products(self) -> list[Product]:
        products, pages = await self._get_full_products_page(1)

        self.log.info(f"Parsing first page: total_pages={pages}")

        results = await asyncio.gather(*[
            self._get_products_page(page)
            for page in range(2, pages + 1)
        ])

        for result in results:
            products += result

        return products


class SmartfonyParser(CategoryParser):
    path: str = "/smartfony-mobilni-telefony/smartfony"

    async def parse_product(self, product: Product) -> None:
        async with self._session.get(
            url=''.join((self._root, product.path)),
            headers=self._headers
        ) as response:
            self.log.debug(response)
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')

        page_data_el = soup.select_one("#__NEXT_DATA__")
        page_data = json.loads(page_data_el.get_text())
        product_data = page_data["props"]["pageProps"]["initialReduxState"]["product"]["product"]

        price = product_data["price"]["firstPrice"]
        promo_price = product_data["price"]["sellingPrice"]

        if price == promo_price:
            promo_price = None

        product.fields.update({
            "brand": product_data.get("brandName"),
            "model": None,
            "availability": product_data["status"],
            "status": "new",
            "color": None,
            "storage": None,
            "price": price,
            "promo_price": promo_price
        })

        for row in product_data["properties"]:
            if row["slug"] == "model-smartfony":
                product.fields["model"] = row["items"][0]["value"]

            elif row["slug"] == "kolir-osnovnyi-smartfony":
                product.fields["color"] = row["items"][0]["value"]

            elif row["slug"] == "vbudovana-pamiat-smartfony":
                parts = row["items"][0]["value"].split()
                k = {
                    "ГБ": 1,
                    "TB": 1024
                }.get(parts[1].upper())
                product.fields["storage"] = int(parts[0]) * k

    async def _get_full_products_page(self, page: int) -> tuple[list[Product], int]:
        products = []
        last_page = -1

        async with self._session.get(
            url=''.join((self._root, self.path)),
            params={"page": page} if page > 1 else None,
            headers=self._headers
        ) as response:

            self.log.debug(response)
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')

        paginations = soup.select("div[class*='_pagination_link'] a")
        for pagination in paginations:
            page = int(pagination.get_text(strip=True))

            if page > last_page:
                last_page = page

        cards = soup.select("div[class*='_product_card']")
        for card in cards:
            title_el = card.select_one("div[class*='_card_title'] a")

            products.append(Product(
                title=title_el.get_text(strip=True),
                path=title_el.get("href")
            ))

        await asyncio.gather(*[
            self.parse_product(product)
            for product in products
        ])

        return products, last_page
