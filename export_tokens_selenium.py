import asyncio
import json
import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import re

def export_tokens_selenium():
    profile_path = os.path.abspath("./chrome_profile_notebooklm")
    options = Options()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--headless=new")
    
    # Try to use existing chromedriver if available in PATH
    try:
        driver = webdriver.Chrome(options=options)
        print("NotebookLM 접속 중 (Standard Selenium)...")
        driver.get("https://notebooklm.google.com/")
        time.sleep(8)
        
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        html = driver.page_source
        
        csrf_match = re.search(r'"SNlM0e":"([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else ""
        
        session_match = re.search(r'"FdrFJe":"([^"]+)"', html)
        session_id = session_match.group(1) if session_match else ""
        
        auth_data = {
            "cookies": cookies,
            "csrf_token": csrf_token,
            "session_id": session_id,
            "extracted_at": time.time()
        }
        
        cache_dir = Path.home() / ".notebooklm-mcp"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / "auth.json"
        
        with open(cache_path, "w") as f:
            json.dump(auth_data, f, indent=2)
            
        print(f"✅ 인증 정보 저장 완료: {cache_path}")
        driver.quit()
        return True
    except Exception as e:
        print(f"오류: {e}")
        return False

if __name__ == "__main__":
    export_tokens_selenium()
