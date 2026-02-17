import json
import time
from pathlib import Path

def manual_cookie_import():
    print("NotebookLM 쿠키 수동 가져오기 도구")
    print("====================================")
    print("1. 브라우저에서 NotebookLM 접속 후 F12 -> Network -> batchexecute 요청 선택")
    print("2. Request Headers의 'cookie:' 항목 값을 전체 복사해 주세요.")
    
    # In agentic mode, we'll ask the user via notify_user and write the result here
    # But for now, let's provide a script that can parse a string
    
    cookie_string = input("\n쿠키 문자열을 입력하세요 (엔터로 종료): ").strip()
    if not cookie_string:
        print("입력값이 없습니다.")
        return

    # Parse cookie string into dict
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name] = value

    # Create auth_data
    auth_data = {
        "cookies": cookies,
        "csrf_token": "", # Will be auto-extracted by client
        "session_id": "", # Will be auto-extracted by client
        "extracted_at": time.time()
    }

    cache_dir = Path.home() / ".notebooklm-mcp"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / "auth.json"

    with open(cache_path, "w") as f:
        json.dump(auth_data, f, indent=2)

    print(f"\n✅ 인증 정보가 {cache_path}에 저장되었습니다.")
    print(f"파싱된 쿠키 개수: {len(cookies)}개")

if __name__ == "__main__":
    manual_cookie_import()
