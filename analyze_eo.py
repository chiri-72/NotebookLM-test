import asyncio
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

async def analyze_eo():
    config = load_config("notebooklm-config.json")
    config.headless = True
    client = NotebookLMClient(config)
    
    try:
        await client.start()
        await client.authenticate()
        
        # 1. Find the notebook
        print("Searching for EO KOREA notebook...")
        client.driver.get("https://notebooklm.google.com/")
        await asyncio.sleep(8)
        
        cards = client.driver.find_elements(By.CSS_SELECTOR, "a[href*='/notebook/']")
        target_id = None
        for card in cards:
            title = card.text.lower()
            if "eo" in title or "korea" in title:
                href = card.get_attribute("href")
                target_id = href.split("/")[-1]
                print(f"Found match: {title} ({target_id})")
                break
        
        if not target_id:
            print("EO KOREA notebook not found by title. Trying default ID.")
            target_id = config.default_notebook_id
            
        if not target_id:
            print("No notebook ID available.")
            return

        # 2. Navigate to notebook
        print(f"Navigating to notebook: {target_id}")
        await client.navigate_to_notebook(target_id)
        await asyncio.sleep(10) # Wait for sources to load
        
        # 3. Analyze
        print("Sending analysis request...")
        message = "이 노트북에 포함된 EO KOREA 유튜브 채널의 모든 영상을 대상으로 립리서치(Deep Research)를 수행해줘. 각 영상의 핵심 인사이트, 인터뷰 대상자의 주요 메시지, 그리고 전체적인 트렌드를 종합해서 상세하게 보고해줘."
        
        await client.send_message(message)
        print("Message sent. Waiting for response...")
        
        response = await client.get_response(wait_for_completion=True, max_wait=180)
        print("\n--- ANALYSIS RESULT ---\n")
        print(response)
        print("\n--- END OF RESULT ---")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(analyze_eo())
