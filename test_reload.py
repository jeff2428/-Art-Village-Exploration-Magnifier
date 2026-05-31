import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Listen to console logs
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        print("Navigating to URL...")
        await page.goto("https://art-village-exploration-magnifier.pages.dev/")
        print("Waiting 5 seconds...")
        await asyncio.sleep(5)
        
        print("Reloading page...")
        await page.reload()
        print("Waiting 5 seconds after reload...")
        await asyncio.sleep(5)
        
        print("Evaluating page content length...")
        content = await page.content()
        print(f"Content length: {len(content)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
