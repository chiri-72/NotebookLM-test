import undetected_chromedriver as uc
import json
import os
import time
from pathlib import Path
import re

def verify_and_export():
    profile_path = os.path.abspath("./chrome_profile_notebooklm")
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    # We run in NON-HEADLESS mode so the user can see and login if needed
    
    driver = uc.Chrome(options=options)
    try:
        print("NotebookLM 접속 중... 로그인이 되어 있는지 확인해 주세요.")
        driver.get("https://notebooklm.google.com/")
        
        # Wait for user to be on the home page (not login page)
        for i in range(60): # Give 60 seconds
            if "signin" not in driver.current_url and "accounts.google.com" not in driver.current_url:
                print("✅ 로그인 확인됨!")
                break
            time.sleep(1)
        else:
            print("❌ 로그인 대기 시간 초과. 브라우저에서 직접 로그인해 주세요.")
            # Keep browser open for a bit more
            time.sleep(30)
            
        # Extract everything
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
        print("이제 스크립트를 종료하고 분석을 시작합니다.")
        
    except Exception as e:
        print(f"오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    verify_and_export()
