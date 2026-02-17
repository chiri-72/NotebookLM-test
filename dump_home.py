import asyncio
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient

async def dump_home():
    config = load_config("notebooklm-config.json")
    config.headless = True
    client = NotebookLMClient(config)
    
    try:
        await client.start()
        await client.authenticate()
        
        print("Home 이동...")
        client.driver.get("https://notebooklm.google.com/")
        await asyncio.sleep(10)
        
        with open("notebooklm_home_dump.html", "w", encoding="utf-8") as f:
            f.write(client.driver.page_source)
        print("✅ notebooklm_home_dump.html 저장 완료.")
        
    except Exception as e:
        print(f"오류: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(dump_home())
