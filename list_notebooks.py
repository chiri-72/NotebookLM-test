import asyncio
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient
from selenium.webdriver.common.by import By

async def list_notebooks():
    config = load_config("notebooklm-config.json")
    config.headless = True
    client = NotebookLMClient(config)
    
    try:
        await client.start()
        # Navigate to home
        client.driver.get("https://notebooklm.google.com/")
        await asyncio.sleep(8) # Wait for cards to load
        
        # Find all notebook cards
        # NotebookLM uses a grid of cards
        cards = client.driver.find_elements(By.CSS_SELECTOR, "a[href*='/notebook/']")
        
        print(f"DEBUG_COUNT: {len(cards)}")
        for card in cards:
            title = card.text
            href = card.get_attribute("href")
            nb_id = href.split("/")[-1]
            title_clean = title.replace("\n", " ")
            print(f"NOTEBOOK_ID: {nb_id} | TITLE: {title_clean}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(list_notebooks())
