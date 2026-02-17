import asyncio
import json
import os
from notebooklm_mcp.api_client import NotebookLMClient
from notebooklm_mcp.auth import load_cached_tokens

async def run_analysis():
    # 1. Load tokens
    tokens = load_cached_tokens()
    if not tokens:
        print("Tokens not found. Run authentication first.")
        return
        
    client = NotebookLMClient(
        cookies=tokens.cookies,
        csrf_token=tokens.csrf_token,
        session_id=tokens.session_id
    )
    
    try:
        # 2. Create Notebook
        print("새 노트북 생성 중: 'EO KOREA Analysis'...")
        notebook = client.create_notebook(title="EO KOREA Analysis")
        if not notebook:
            print("노트북 생성 실패")
            return
            
        notebook_id = notebook.id
        print(f"✅ 노트북 생성 성공! ID: {notebook_id}")
        print(f"URL: {notebook.url}")
        
        # 3. Add Sources (EO KOREA Specific Videos)
        print("EO KOREA 최신 영상 소스 추가 중...")
        video_urls = [
            "https://www.youtube.com/watch?v=jDJZxERIhnc",
            "https://www.youtube.com/watch?v=08p4OiYebHg",
            "https://www.youtube.com/watch?v=Xj4iVEZPaNw",
            "https://www.youtube.com/watch?v=U4ZAWsLyZaY",
            "https://www.youtube.com/watch?v=y9OKMX66UKE",
            "https://www.youtube.com/watch?v=uIw_XH3_AQs",
            "https://www.youtube.com/watch?v=Or8v7oQD77s",
            "https://www.youtube.com/watch?v=ih-AEOW-z1g",
            "https://www.youtube.com/watch?v=Hcu3tCh6Bfs",
            "https://www.youtube.com/watch?v=d_QFe3Jxk6Y"
        ]
        
        added_count = 0
        for url in video_urls:
            print(f"추가 시도: {url}")
            source = client.add_url_source(notebook_id, url=url)
            if source:
                print(f"✅ 추가 성공: {source.get('title', 'Unknown')}")
                added_count += 1
            else:
                print(f"❌ 추가 실패: {url}")
        
        if added_count == 0:
            print("모든 소스 추가 실패")
            return

        # 4. Wait for indexing and perform initial query
        print(f"데이터 인덱싱 대기 중 (30초, 총 {added_count}개 소스)...")
        await asyncio.sleep(30)
        
        print("립리서치(Deep Research) 수행 중...")
        query = "이 채널의 영상들을 분석해서 립리서치 보고서를 작성해줘. 핵심 인사이트와 주요 창업가들의 메시지를 요약해줘."
        result = client.query(notebook_id, query_text=query)
        
        if result and 'answer' in result:
            print("\n=== 립리서치 결과 ===\n")
            print(result['answer'])
            print("\n==================\n")
            
            # Save report
            with open("EO_KOREA_Final_Report.md", "w", encoding="utf-8") as f:
                f.write(result['answer'])
            print("보고서가 EO_KOREA_Final_Report.md에 저장되었습니다.")
        else:
            print("쿼리 결과가 없습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(run_analysis())
