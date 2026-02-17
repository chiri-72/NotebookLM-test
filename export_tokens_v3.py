import asyncio
import json
import os
import time
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import re

async def export_tokens():
    # 1. Start browser to get cookies and CSRF
    profile_path = os.path.abspath("./chrome_profile_notebooklm")
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--headless=new") # Headless mode for token extraction
    
    driver = uc.Chrome(options=options)
    try:
        print("NotebookLM 접속 중...")
        driver.get("https://notebooklm.google.com/")
        time.sleep(10) # Wait for page and scripts to load
        
        current_url = driver.current_url
        if "signin" in current_url:
            print("❌ 로그인 필요! (수동 로그인이 선행되어야 합니다)")
            return
            
        # 2. Extract cookies
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        
        # 3. Extract CSRF and Session ID from page source
        html = driver.page_source
        csrf_token = None
        session_id = None
        
        # SNlM0e is a common CSRF token key in Google's WIZ framework
        csrf_match = re.search(r'"SNlM0e":"([^"]+)"', html)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            
        # FdrFJe often contains session info
        session_match = re.search(r'"FdrFJe":"([^"]+)"', html)
        if session_match:
            session_id = session_match.group(1)
            
        print(f"추출 완료 - Cookies: {len(cookies)}개, CSRF: {'발견' if csrf_token else '미발견'}")
        
        # 4. Save to auth.json
        auth_data = {
            "cookies": cookies,
            "csrf_token": csrf_token or "",
            "session_id": session_id or "",
            "extracted_at": time.time()
        }
        
        cache_dir = Path.home() / ".notebooklm-mcp"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / "auth.json"
        
        with open(cache_path, "w") as f:
            json.dump(auth_data, f, indent=2)
            
        print(f"✅ 인증 정보가 {cache_path}에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(export_tokens())
