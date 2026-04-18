#!/usr/bin/env python3
"""
NotebookLM CLI - Claude Code에서 NotebookLM을 제어하는 커맨드 라인 도구

사용법:
  python notebooklm-cli.py create "My Notebook" --sources url1 url2 url3
  python notebooklm-cli.py list
  python notebooklm-cli.py add-sources NOTEBOOK_ID --sources url1 url2
  python notebooklm-cli.py get NOTEBOOK_ID

필수 환경 변수:
  GOOGLE_CLOUD_PROJECT_ID: Google Cloud 프로젝트 ID
  GOOGLE_APPLICATION_CREDENTIALS: 서비스 계정 키 JSON 파일 경로
"""

import argparse
import json
import os
import sys
from typing import List, Optional
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import requests

# NotebookLM API Base URL
API_BASE_URL = "https://notebooklm.googleapis.com/v1"


class NotebookLMClient:
    """NotebookLM API 클라이언트"""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Args:
            project_id: Google Cloud 프로젝트 ID
            credentials_path: 서비스 계정 키 JSON 파일 경로 (없으면 환경변수 사용)
        """
        self.project_id = project_id

        # 인증 설정
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        else:
            # 환경변수에서 자동으로 로드
            credentials = service_account.Credentials.from_service_account_file(
                os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )

        self.session = AuthorizedSession(credentials)

    def create_notebook(self, title: str, sources: Optional[List[str]] = None) -> dict:
        """
        새 노트북 생성

        Args:
            title: 노트북 제목
            sources: 추가할 소스 URL 리스트

        Returns:
            생성된 노트북 정보
        """
        url = f"{API_BASE_URL}/projects/{self.project_id}/notebooks"

        payload = {
            "displayName": title,
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        notebook = response.json()
        notebook_id = notebook['name'].split('/')[-1]

        print(f"✅ 노트북 생성 완료: {title}")
        print(f"📝 Notebook ID: {notebook_id}")

        # 소스 추가
        if sources:
            print(f"\n📚 {len(sources)}개 소스 추가 중...")
            for i, source_url in enumerate(sources, 1):
                try:
                    self.add_source(notebook_id, source_url)
                    print(f"  [{i}/{len(sources)}] ✓ {source_url}")
                except Exception as e:
                    print(f"  [{i}/{len(sources)}] ✗ {source_url} - Error: {e}")

        return notebook

    def list_notebooks(self) -> List[dict]:
        """
        모든 노트북 목록 조회

        Returns:
            노트북 리스트
        """
        url = f"{API_BASE_URL}/projects/{self.project_id}/notebooks"

        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        notebooks = data.get('notebooks', [])

        print(f"📚 총 {len(notebooks)}개의 노트북:")
        print()
        for notebook in notebooks:
            notebook_id = notebook['name'].split('/')[-1]
            title = notebook.get('displayName', 'Untitled')
            print(f"  • {title}")
            print(f"    ID: {notebook_id}")
            print(f"    Created: {notebook.get('createTime', 'N/A')}")
            print()

        return notebooks

    def get_notebook(self, notebook_id: str) -> dict:
        """
        특정 노트북 정보 조회

        Args:
            notebook_id: 노트북 ID

        Returns:
            노트북 정보
        """
        url = f"{API_BASE_URL}/projects/{self.project_id}/notebooks/{notebook_id}"

        response = self.session.get(url)
        response.raise_for_status()

        notebook = response.json()

        print(f"📖 노트북: {notebook.get('displayName', 'Untitled')}")
        print(f"   ID: {notebook_id}")
        print(f"   Created: {notebook.get('createTime', 'N/A')}")
        print(f"   Updated: {notebook.get('updateTime', 'N/A')}")

        # 소스 목록 조회
        sources = self.list_sources(notebook_id)
        print(f"   Sources: {len(sources)}개")

        return notebook

    def add_source(self, notebook_id: str, source_url: str) -> dict:
        """
        노트북에 소스 추가

        Args:
            notebook_id: 노트북 ID
            source_url: 추가할 소스 URL

        Returns:
            추가된 소스 정보
        """
        url = f"{API_BASE_URL}/projects/{self.project_id}/notebooks/{notebook_id}/sources"

        payload = {
            "url": source_url
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        return response.json()

    def list_sources(self, notebook_id: str) -> List[dict]:
        """
        노트북의 모든 소스 조회

        Args:
            notebook_id: 노트북 ID

        Returns:
            소스 리스트
        """
        url = f"{API_BASE_URL}/projects/{self.project_id}/notebooks/{notebook_id}/sources"

        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        sources = data.get('sources', [])

        return sources

    def get_source(self, notebook_id: str, source_id: str) -> dict:
        """
        특정 소스 정보 조회

        Args:
            notebook_id: 노트북 ID
            source_id: 소스 ID

        Returns:
            소스 정보
        """
        url = f"{API_BASE_URL}/projects/{self.project_id}/notebooks/{notebook_id}/sources/{source_id}"

        response = self.session.get(url)
        response.raise_for_status()

        return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM CLI - Claude Code에서 NotebookLM 제어",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 새 노트북 생성 (소스 없이)
  python notebooklm-cli.py create "AI Research Notebook"

  # 새 노트북 생성 (소스와 함께)
  python notebooklm-cli.py create "AI Research" --sources \\
    https://example.com/article1 \\
    https://example.com/article2

  # 모든 노트북 목록 보기
  python notebooklm-cli.py list

  # 특정 노트북 정보 보기
  python notebooklm-cli.py get NOTEBOOK_ID

  # 노트북에 소스 추가
  python notebooklm-cli.py add-sources NOTEBOOK_ID --sources \\
    https://example.com/new-article
        """
    )

    # 서브커맨드
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 커맨드')

    # create 커맨드
    create_parser = subparsers.add_parser('create', help='새 노트북 생성')
    create_parser.add_argument('title', help='노트북 제목')
    create_parser.add_argument('--sources', nargs='+', help='추가할 소스 URL들')

    # list 커맨드
    subparsers.add_parser('list', help='모든 노트북 목록 조회')

    # get 커맨드
    get_parser = subparsers.add_parser('get', help='특정 노트북 정보 조회')
    get_parser.add_argument('notebook_id', help='노트북 ID')

    # add-sources 커맨드
    add_sources_parser = subparsers.add_parser('add-sources', help='노트북에 소스 추가')
    add_sources_parser.add_argument('notebook_id', help='노트북 ID')
    add_sources_parser.add_argument('--sources', nargs='+', required=True, help='추가할 소스 URL들')

    args = parser.parse_args()

    # 환경변수 확인
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not project_id:
        print("❌ 오류: GOOGLE_CLOUD_PROJECT_ID 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export GOOGLE_CLOUD_PROJECT_ID='your-project-id'")
        sys.exit(1)

    if not credentials_path:
        print("❌ 오류: GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account-key.json'")
        sys.exit(1)

    # 클라이언트 초기화
    try:
        client = NotebookLMClient(project_id, credentials_path)
    except Exception as e:
        print(f"❌ 오류: NotebookLM 클라이언트 초기화 실패")
        print(f"   {e}")
        sys.exit(1)

    # 커맨드 실행
    try:
        if args.command == 'create':
            client.create_notebook(args.title, args.sources)

        elif args.command == 'list':
            client.list_notebooks()

        elif args.command == 'get':
            client.get_notebook(args.notebook_id)

        elif args.command == 'add-sources':
            print(f"📚 {len(args.sources)}개 소스 추가 중...")
            for i, source_url in enumerate(args.sources, 1):
                try:
                    client.add_source(args.notebook_id, source_url)
                    print(f"  [{i}/{len(args.sources)}] ✓ {source_url}")
                except Exception as e:
                    print(f"  [{i}/{len(args.sources)}] ✗ {source_url} - Error: {e}")

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
