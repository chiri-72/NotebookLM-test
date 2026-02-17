import asyncio
import json
import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re

def export_tokens_thorough():
    profile_path = os.path.abspath("./chrome_profile_notebooklm")
    options = Options()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--headless=new")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # 1. Visit main google domain to get session cookies
        print("Google 메인 도메인 방문 중...")
        driver.get("https://www.google.com")
        time.sleep(5)
        google_cookies = driver.get_cookies()
        
        # 2. Visit NotebookLM to get app-specific tokens
        print("NotebookLM 도메인 방문 중...")
        driver.get("https://notebooklm.google.com/")
        time.sleep(8)
        notebook_cookies = driver.get_cookies()
        
        # 3. Combine and filter cookies
        all_cookies = {c['name']: c['value'] for c in (google_cookies + notebook_cookies)}
        
        # Essential cookies check
        required = ["SID", "HSID", "SSID", "APISID", "SAPISID"]
        missing = [r for r in required if r not in all_cookies]
        if missing:
            print(f"⚠️ 필수 쿠키 누락: {missing}. 로그인이 제대로 되어있는지 확인이 필요합니다.")
        else:
            print("✅ 필수 쿠키 모두 발견!")
            
        # 4. Extract CSRF and Session ID
        html = driver.page_source
        csrf_match = re.search(r'"SNlM0e":"([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else ""
        
        session_match = re.search(r'"FdrFJe":"([^"]+)"', html)
        session_id = session_match.group(1) if session_match else ""
        
        auth_data = {
            "cookies": all_cookies,
            "csrf_token": csrf_token,
            "session_id": session_id,
            "extracted_at": time.time()
        }
        
        cache_dir = Path.home() / ".notebooklm-mcp"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / "auth.json"
        
        with open(cache_path, "w") as f:
            json.dump(auth_data, f, indent=2)
            
        print(f"✅ 인증 정보 저장 완료 (쿠키 {len(all_cookies)}개): {cache_path}")
        driver.quit()
        return True
    except Exception as e:
        print(f"오류: {e}")
        return False

if __name__ == "__main__":
    export_tokens_thorough()
