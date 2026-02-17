import asyncio
import json
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

async def create_new_notebook():
    config_path = "notebooklm-config.json"
    if not os.path.exists(config_path):
        print("Config not found")
        return
        
    config = load_config(config_path)
    # UI 조작이 필요하므로 초기에는 headless=False를 권장하지만, 
    # 이미 로그인이 되어 있으므로 headless=True로 시도해봅니다.
    config.headless = True 
    client = NotebookLMClient(config)
    
    try:
        await client.start()
        await client.authenticate()
        
        print("NotebookLM 홈으로 이동 중...")
        client.driver.get("https://notebooklm.google.com/")
        
        # 'New Notebook' 버튼 찾기 (플러스 아이콘이나 'New notebook' 텍스트)
        print("'New Notebook' 생성 버튼 찾는 중...")
        create_btn_selectors = [
            "button[aria-label*='New notebook']",
            "button:has(span:contains('New notebook'))",
            "div[role='button']:has(span:contains('New notebook'))",
            ".create-notebook-button",
            "//button[contains(., 'New notebook')]" # XPath fallback
        ]
        
        create_btn = None
        # 일단 가장 확실한 aria-label이나 텍스트 기반으로 찾음
        try:
            # NotebookLM의 현재 구조상 보통 '+ New notebook'이라는 텍스트가 있는 버튼임
            create_btn = WebDriverWait(client.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'New notebook')] | //div[contains(., 'New notebook') and @role='button']"))
            )
        except:
            print("기본 셀렉터 실패, 대체 셀렉터 시도...")
            for selector in create_btn_selectors:
                try:
                    if selector.startswith("//"):
                        create_btn = client.driver.find_element(By.XPATH, selector)
                    else:
                        create_btn = client.driver.find_element(By.CSS_SELECTOR, selector)
                    if create_btn: break
                except: continue

        if not create_btn:
            print("생성 버튼을 찾지 못했습니다.")
            return

        print("버튼 클릭!")
        create_btn.click()
        
        # 새 노트북 URL로 바뀔 때까지 대기
        print("새 노트북 생성 대기 중...")
        for i in range(20):
            await asyncio.sleep(1)
            current_url = client.driver.current_url
            if "/notebook/" in current_url and not current_url.endswith("/notebook/"):
                new_id = current_url.split("/")[-1].split("?")[0]
                print(f"✅ 새 노트북 생성 완료! ID: {new_id}")
                
                # Config 업데이트
                with open(config_path, "r") as f:
                    data = json.load(f)
                data["default_notebook_id"] = new_id
                with open(config_path, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"✅ {config_path} 업데이트 완료.")
                return new_id
                
        print("타임아웃: 새 노트북 ID를 가져오지 못했습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(create_new_notebook())
