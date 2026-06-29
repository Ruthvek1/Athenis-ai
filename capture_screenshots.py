import asyncio
from playwright.async_api import async_playwright
import os
import uuid

async def main():
    os.makedirs("frontend/public/assets", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Capture Login Page
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await page.goto("http://localhost:3000/")
        await page.wait_for_selector("text=Sign In")
        await page.screenshot(path="frontend/public/assets/login.png")
        
        random_id = str(uuid.uuid4())[:8]
        user_email = f"user_{random_id}@example.com"
        
        # Register user
        await page.click("text=Register")
        await page.click("text=User Access")
        await page.fill("input[type=email]", user_email)
        await page.fill("input[type=password]", "password123")
        await page.click("button[type=submit]")
        
        await page.wait_for_timeout(1000)
        
        # Login user
        await page.click("text=Sign In")
        await page.click("text=User Access")
        await page.fill("input[type=email]", user_email)
        await page.fill("input[type=password]", "password123")
        await page.click("button[type=submit]")
        
        # Wait for Chat UI
        try:
            await page.wait_for_selector("text=New Chat", timeout=5000)
            await page.screenshot(path="frontend/public/assets/chat.png")
        except Exception as e:
            print("Could not capture chat:", e)
        await context.close()
        
        # 2. Capture Admin Dashboard
        admin_email = f"admin_{random_id}@example.com"
        context2 = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page2 = await context2.new_page()
        await page2.goto("http://localhost:3000/")
        
        await page2.click("text=Register")
        await page2.click("text=Admin Access")
        await page2.fill("input[type=email]", admin_email)
        await page2.fill("input[type=password]", "password123")
        await page2.click("button[type=submit]")
        
        await page2.wait_for_timeout(1000)
        
        await page2.click("text=Sign In")
        await page2.click("text=Admin Access")
        await page2.fill("input[type=email]", admin_email)
        await page2.fill("input[type=password]", "password123")
        await page2.click("button[type=submit]")
        
        try:
            await page2.wait_for_selector("text=Unified", timeout=5000)
            await page2.screenshot(path="frontend/public/assets/dashboard.png")
            
            await page2.click("text=Document Management")
            await page2.wait_for_selector("text=Knowledge Base", timeout=5000)
            await page2.screenshot(path="frontend/public/assets/admin.png")
        except Exception as e:
            print("Could not capture admin:", e)
            
        await context2.close()
        await browser.close()
        print("Screenshots captured successfully.")

if __name__ == "__main__":
    asyncio.run(main())
