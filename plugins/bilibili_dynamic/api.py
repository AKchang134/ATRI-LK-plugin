import asyncio

from playwright.async_api import async_playwright

from ATRI.utils import request
from ATRI.exceptions import RequestError
from ATRI.log import log

from .exception import BilibiliDynamicError


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
                if "web-dynamic/v1/feed/space" in response.url:
                    if response.status != 200:
                        log.warning(f'请求失败:{response.status}')
                    else:
                        log.info('获取数据中...')
                    try:
                        json_data = await response.json()
                        api_response_data.update(json_data)
                    except Exception as e:
                        raise e from e

            page.on("response", handle_response)
            await page.goto(f"https://space.bilibili.com/{self.uid}/dynamic", timeout=60000)
            max_attempts = 20
            for _ in range(max_attempts):
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(5)
                if 'code' in api_response_data:
                    break
            await browser.close()
            if api_response_data.get("code") != 0:
                raise BilibiliDynamicError(f'获取失败:{api_response_data.get("code")}')
            return api_response_data
