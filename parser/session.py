
import aiohttp
from aiolimiter import AsyncLimiter


class RateLimitedSession(aiohttp.ClientSession):
    def __init__(self, *args, limiter: AsyncLimiter, **kwargs):
        super().__init__(*args, **kwargs)
        self._limiter = limiter

    async def _request(self, *args, **kwargs):
        async with self._limiter:
            return await super()._request(*args, **kwargs)
