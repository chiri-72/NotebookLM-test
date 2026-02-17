import undetected_chromedriver as uc
import json
import os
import time
from pathlib import Path
import re

def auto_auth_and_export():
    profile_path = os.path.abspath("./chrome_profile_notebooklm_v4")
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    # Headless를 끄고 잠시 실행하여 세션을 잡습니다.
    # 만약 환경이 GUI를 지원하지 않으면 에러가 나겠지만, 
    # 일반적인 데스크톱 환경(Mac)에서는 작동할 것입니다.
    
    driver = uc.Chrome(options=options)
    try:
        print("NotebookLM 자동 인증 및 세션 확보 시작...")
        driver.get("https://notebooklm.google.com/")
        
        # 페이지 로딩 및 구글 세션 확인을 위해 충분히 대기
        time.sleep(15) 
        
        # 현재 브라우저의 쿠키 모두 추출
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
        
        # 패키지가 찾는 기본 경로에 저장
        cache_dir = Path.home() / ".notebooklm-mcp"
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / "auth.json"
        
        with open(cache_path, "w") as f:
            json.dump(auth_data, f, indent=2)
            
        print(f"✅ 인증 정보 자동 저장 완료: {cache_path}")
        print(f"추출된 쿠키 개수: {len(cookies)}개")
        
        required = ["SID", "HSID", "SSID", "APISID", "SAPISID"]
        found = [r for r in required if r in cookies]
        print(f"필수 쿠키 확인: {found}")
        
    except Exception as e:
        print(f"자동 인증 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    auto_auth_and_export()
