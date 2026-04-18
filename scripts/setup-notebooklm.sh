#!/bin/bash
# NotebookLM CLI 설정 스크립트

echo "🚀 NotebookLM CLI 설정을 시작합니다..."
echo ""

# Python 가상환경 생성
echo "📦 Python 가상환경 생성 중..."
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 필수 패키지 설치
echo "📥 필수 패키지 설치 중..."
pip install --upgrade pip
pip install google-auth google-auth-oauthlib google-auth-httplib2 requests

echo ""
echo "✅ NotebookLM CLI 설치 완료!"
echo ""
echo "🔧 다음 단계:"
echo ""
echo "1. Google Cloud 프로젝트 ID 설정:"
echo "   export GOOGLE_CLOUD_PROJECT_ID='your-project-id'"
echo ""
echo "2. 서비스 계정 키 파일 경로 설정:"
echo "   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account-key.json'"
echo ""
echo "3. NotebookLM CLI 사용:"
echo "   python notebooklm-cli.py create \"My Notebook\" --sources https://example.com"
echo ""
echo "📚 도움말:"
echo "   python notebooklm-cli.py --help"
echo ""
