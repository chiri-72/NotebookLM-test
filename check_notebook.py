import asyncio
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient
from selenium.webdriver.common.by import By

async def check():
    config_path = "notebooklm-config.json"
    if not os.path.exists(config_path):
        print("Config not found")
        return
        
    config = load_config(config_path)
    config.headless = True
    client = NotebookLMClient(config)
    
    try:
        await client.start()
        await client.authenticate()
        
        # Try to get notebook title
        await asyncio.sleep(5) # Give it time to load
        
        title = "Unknown"
        selectors = [
            "div[role='main'] h1",
            ".notebook-title",
            "title",
            "h1",
            ".current-notebook-name"
        ]
        
        for selector in selectors:
            try:
                elements = client.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    text = elements[0].text or client.driver.title
                    if text:
                        title = text
                        break
            except:
                continue
                
        print(f"DEBUG_TITLE: {title}")
        print(f"DEBUG_URL: {client.driver.current_url}")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check())
