import asyncio
import sys
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient

async def test_auth():
    config_path = "notebooklm-config.json"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found")
        return

    config = load_config(config_path)
    # Force headless false for initial setup if needed
    config.headless = False 
    
    print("--- NotebookLM Connection Test ---")
    print(f"Using profile: {config.auth.profile_dir}")
    
    client = NotebookLMClient(config)
    try:
        print("Starting browser...")
        await client.start()
        
        print("Checking authentication...")
        is_auth = await client.authenticate()
        
        if is_auth:
            print("✅ Already Authenticated!")
        else:
            print("❌ Authentication required.")
            print("Please log in to Google in the browser window that just opened.")
            print("After logging in, this script will detect it or you can restart it.")
            
            # Wait a bit for user to potentially log in
            for i in range(60):
                await asyncio.sleep(5)
                if await client.authenticate():
                    print("✅ Authentication successful!")
                    break
                print(f"Waiting... ({i*5}s)")
        
        if client._is_authenticated:
            print("Current URL:", client.driver.current_url)
            # You could add more tests here, like listing elements
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Keep browser open if auth failed so user can login
        if client._is_authenticated:
            await client.close()
            print("Browser closed.")
        else:
            print("Browser left open for manual login. Please close it manually when done.")

if __name__ == "__main__":
    asyncio.run(test_auth())
