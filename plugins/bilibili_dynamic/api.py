import asyncio

from playwright.async_api import async_playwright

from ATRI.utils import request
from ATRI.exceptions import RequestError


class API:
    def __init__(self, uid: int):
        self.uid = uid

    @staticmethod
    async def _request(url: str, params=None, headers=None) -> dict:
        if params is None:
            params = {}

        try:
            resp = await request.get(url, params=params, headers=headers)
        except Exception:
            raise RequestError("Request failed!")

        return resp.json()

    async def get_user_info(self) -> dict:
        url = "https://api.bilibili.com/x/web-interface/card"
        params = {"mid": self.uid}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "Referer": "https://space.bilibili.com/",
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*"
        }
        return await self._request(url, params, headers)

    async def get_user_dynamics(self) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            api_response_data = {}

            async def handle_response(response):
                if "web-dynamic/v1/feed/space" in response.url and response.status == 200:
                    try:
                        json_data = await response.json()
                        api_response_data.update(json_data)
                    except Exception as e:
                        raise e from e

            page.on("response", handle_response)
            await page.goto(f"https://space.bilibili.com/{self.uid}/dynamic", timeout=60000)
            await asyncio.sleep(30)
            await browser.close()
            return api_response_data
