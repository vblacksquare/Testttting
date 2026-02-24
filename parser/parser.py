

import aiohttp
from loguru import logger
from bs4 import BeautifulSoup
from aiolimiter import AsyncLimiter

from dtypes import Category, Product

from .session import RateLimitedSession
from .category import CategoryParser


class Parser:
    def __init__(self, root: str, rps_limit: int, headers: dict):
        self.log = logger.bind(classname=self.__class__.__name__)

        self._session: aiohttp.ClientSession = None
        self._root = root
        self._headers = headers
        self.rps_limit = rps_limit

    def start(self) -> None:
        self.log.debug("Started session")
        self._session = RateLimitedSession(
            limiter=AsyncLimiter(self.rps_limit, 1)
        )

    async def stop(self) -> None:
        self.log.debug("Stopped session")
        await self._session.close()

    async def __aenter__(self) -> "Parser":
        self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> "Parser":
        await self.stop()

        if exc:
            raise exc

    async def get_categories(self) -> list[Category]:
        async with self._session.get(
            url="https://shop.kyivstar.ua"
        ) as response:
            self.log.debug(response)
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")

        categories = []

        raw_categories = soup.select("div[class*='catalog'] div[class*='punkt_'] a")
        for raw_category in raw_categories:
            categories.append(Category(
                title=raw_category.get_text(strip=True),
                path=raw_category.get("href"),
            ))

        return categories

    async def get_products(self, category: Category) -> list[Product]:
        category_parsers = CategoryParser.__subclasses__()
        target_parser: CategoryParser = None

        for category_parser in category_parsers:
            if category_parser.path == category.path:
                target_parser = category_parser(session=self._session, root=self._root, headers=self._headers)
                break

        if target_parser is None:
            raise Exception(f"Category parser for {category} not found")

        return await target_parser.get_products()
