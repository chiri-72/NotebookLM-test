import asyncio
import os
from notebooklm_mcp.config import load_config
from notebooklm_mcp.client import NotebookLMClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

async def analyze_eo_v2():
    config = load_config("notebooklm-config.json")
    # 분석 과정을 확인하기 위해 잠시 헤드리스를 끕니다. (문제 해결 후 다시 켤 수 있음)
    config.headless = False 
    client = NotebookLMClient(config)
    
    try:
        await client.start()
        await client.authenticate()
        
        target_id = config.default_notebook_id
        print(f"노트북 접속 중: {target_id}")
        await client.navigate_to_notebook(target_id)
        
        # 페이지 로딩 대기 (소스들이 많을 수 있으므로 충분히)
        print("페이지 요소 로딩 대기 중 (15초)...")
        await asyncio.sleep(15)
        
        # 채팅 입력창 찾기 (다양한 방법 시도)
        print("채팅 입력창 찾는 중...")
        selectors = [
            "textarea[placeholder*='Ask']",
            "textarea[aria-label*='message']",
            "div[contenteditable='true']",
            "textarea"
        ]
        
        chat_input = None
        for selector in selectors:
            try:
                chat_input = WebDriverWait(client.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if chat_input:
                    print(f"입력창 발견! (셀렉터: {selector})")
                    break
            except:
                continue
        
        if not chat_input:
            print("입력창을 결국 찾지 못했습니다. 스크린샷이나 페이지 구조 확인이 필요할 수 있습니다.")
            return

        # 메시지 전송
        print("분석 요청 메시지 입력 중...")
        message = "이 노트북에 있는 모든 EO KOREA 영상들을 분석해서 '립리서치' 보고서를 작성해줘. 핵심 인사이트와 주요 인터뷰 내용을 포함해줘."
        
        # 클릭 후 입력
        chat_input.click()
        await asyncio.sleep(1)
        chat_input.send_keys(message)
        await asyncio.sleep(1)
        chat_input.send_keys(Keys.ENTER)
        
        print("메시지 전송 완료. 답변 생성 대기 중 (최대 3분)...")
        
        # 답변 완료 대기 및 가져오기
        response = await client.get_response(wait_for_completion=True, max_wait=180)
        
        print("\n=== 분석 결과 ===\n")
        print(response)
        print("\n================\n")
        
        # 결과를 파일로 저장
        with open("eo_land_research.txt", "w", encoding="utf-8") as f:
            f.write(response)
        print("결과가 eo_land_research.txt에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        await asyncio.sleep(5)
        await client.close()

if __name__ == "__main__":
    asyncio.run(analyze_eo_v2())
