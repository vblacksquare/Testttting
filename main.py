
import asyncio
import json

from parser import Parser

from config import get_config
from utils.logger import setup_logger
from utils.files import save_results


async def main():
    config = get_config()
    setup_logger(config.logger.path, config.logger.level)

    with open(config.parser.headers, "r", encoding="utf-8") as f:
        data = json.load(f)

    async with Parser(
        root=config.parser.root,
        rps_limit=config.parser.rps_limit,
        headers=data
    ) as parser:

        categories = await parser.get_categories()
        category = categories[3]

        products = await parser.get_products(category)

    save_results(products, category, config.parser.results_path)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
