# NotebookLM CLI - Claude Code 통합 가이드

Claude Code에서 NotebookLM을 자동으로 제어할 수 있는 커맨드 라인 도구입니다.

## 🎯 기능

- ✅ 노트북 생성 (소스와 함께 또는 없이)
- ✅ 노트북 목록 조회
- ✅ 특정 노트북 정보 조회
- ✅ 노트북에 소스 추가 (URL, YouTube, 문서 등)
- ✅ Google Cloud NotebookLM Enterprise API 사용

## 📋 사전 요구사항

### 1. Google Cloud 설정

NotebookLM CLI는 [Google Cloud NotebookLM Enterprise API](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)를 사용합니다.

**필수 설정:**

1. **Google Cloud 프로젝트 생성**
   - https://console.cloud.google.com
   - 새 프로젝트 생성 또는 기존 프로젝트 선택

2. **NotebookLM Enterprise API 활성화**
   - APIs & Services > Library
   - "NotebookLM API" 검색 및 활성화

3. **서비스 계정 생성**
   - IAM & Admin > Service Accounts
   - "Create Service Account" 클릭
   - 역할: NotebookLM Admin 또는 Editor
   - JSON 키 파일 다운로드 (예: `notebooklm-service-account.json`)

### 2. Python 환경

- Python 3.8 이상
- pip

## 🚀 설치

### 자동 설치 (권장)

```bash
cd /Users/chiri/Desktop/AI\ 서비스/DeepResearch/scripts
chmod +x setup-notebooklm.sh
./setup-notebooklm.sh
```

### 수동 설치

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install google-auth google-auth-oauthlib google-auth-httplib2 requests
```

## ⚙️ 환경 변수 설정

```bash
# Google Cloud 프로젝트 ID
export GOOGLE_CLOUD_PROJECT_ID='your-project-id'

# 서비스 계정 키 파일 경로
export GOOGLE_APPLICATION_CREDENTIALS='/path/to/notebooklm-service-account.json'
```

**영구 설정 (선택사항):**

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
echo 'export GOOGLE_CLOUD_PROJECT_ID="your-project-id"' >> ~/.bashrc
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"' >> ~/.bashrc
source ~/.bashrc
```

## 📖 사용법

### 1. 새 노트북 생성

```bash
# 빈 노트북 생성
python notebooklm-cli.py create "AI Research Notebook"

# 소스와 함께 노트북 생성
python notebooklm-cli.py create "AI Foundation Models" --sources \
  https://simonwillison.net/2025/Dec/31/the-year-in-llms/ \
  https://zilliz.com/learn/mamba-architecture-potential-transformer-replacement \
  https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms
```

**출력 예시:**
```
✅ 노트북 생성 완료: AI Foundation Models
📝 Notebook ID: abc123xyz

📚 3개 소스 추가 중...
  [1/3] ✓ https://simonwillison.net/2025/Dec/31/the-year-in-llms/
  [2/3] ✓ https://zilliz.com/learn/mamba-architecture-potential-transformer-replacement
  [3/3] ✓ https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms
```

### 2. 모든 노트북 목록 조회

```bash
python notebooklm-cli.py list
```

**출력 예시:**
```
📚 총 3개의 노트북:

  • AI Foundation Models
    ID: abc123xyz
    Created: 2026-02-18T10:30:00Z

  • Business Applications
    ID: def456uvw
    Created: 2026-02-18T11:00:00Z

  • Ethics & Governance
    ID: ghi789rst
    Created: 2026-02-18T11:30:00Z
```

### 3. 특정 노트북 정보 조회

```bash
python notebooklm-cli.py get abc123xyz
```

**출력 예시:**
```
📖 노트북: AI Foundation Models
   ID: abc123xyz
   Created: 2026-02-18T10:30:00Z
   Updated: 2026-02-18T12:00:00Z
   Sources: 15개
```

### 4. 노트북에 소스 추가

```bash
python notebooklm-cli.py add-sources abc123xyz --sources \
  https://www.youtube.com/watch?v=example1 \
  https://arxiv.org/abs/2401.12345 \
  https://medium.com/@user/article
```

**출력 예시:**
```
📚 3개 소스 추가 중...
  [1/3] ✓ https://www.youtube.com/watch?v=example1
  [2/3] ✓ https://arxiv.org/abs/2401.12345
  [3/3] ✓ https://medium.com/@user/article
```

## 🔧 Claude Code 통합

### 방법 1: Bash Hook으로 통합

`~/.claude/hooks/notebooklm-create` 생성:

```bash
#!/bin/bash
# NotebookLM 노트북 생성 Hook

TITLE="$1"
shift
SOURCES="$@"

cd /Users/chiri/Desktop/AI\ 서비스/DeepResearch/scripts
source venv/bin/activate
python notebooklm-cli.py create "$TITLE" --sources $SOURCES
```

사용:
```bash
chmod +x ~/.claude/hooks/notebooklm-create
notebooklm-create "My Research" https://example.com/article1 https://example.com/article2
```

### 방법 2: Claude Code에서 직접 실행

Claude Code 대화에서:

```
@claude, NotebookLM 노트북을 생성해줘:
- 제목: "AI Ethics Research"
- 소스:
  1. https://www.weforum.org/stories/2026/01/scaling-trustworthy-ai-into-global-practice/
  2. https://www.inta.org/perspectives/features/how-the-eu-ai-act-supplements-gdpr-in-the-protection-of-personal-data/
  3. https://www.ibm.com/think/topics/explainable-ai
```

Claude가 자동으로 다음 커맨드를 실행합니다:
```bash
cd /Users/chiri/Desktop/AI\ 서비스/DeepResearch/scripts && \
source venv/bin/activate && \
python notebooklm-cli.py create "AI Ethics Research" --sources \
  https://www.weforum.org/stories/2026/01/scaling-trustworthy-ai-into-global-practice/ \
  https://www.inta.org/perspectives/features/how-the-eu-ai-act-supplements-gdpr-in-the-protection-of-personal-data/ \
  https://www.ibm.com/think/topics/explainable-ai
```

## 📊 실전 워크플로우 예시

### 시나리오: AI 리서치 프로젝트용 5개 노트북 생성

```bash
# 1. Foundation Models 노트북
python notebooklm-cli.py create "AI Foundation Models" --sources \
  https://simonwillison.net/2025/Dec/31/the-year-in-llms/ \
  https://zilliz.com/learn/mamba-architecture-potential-transformer-replacement \
  https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms \
  https://uplatz.com/blog/multimodal-models-gpt-4v-gemini-llava-explained/ \
  https://www.3blue1brown.com/lessons/gpt

# 2. Development Ecosystem 노트북
python notebooklm-cli.py create "AI Development Ecosystem" --sources \
  https://research.aimultiple.com/rag-frameworks/ \
  https://www.kernshell.com/best-practices-for-scalable-machine-learning-deployment/ \
  https://liquidmetal.ai/casesAndBlogs/vector-comparison/

# 3. Business Applications 노트북
python notebooklm-cli.py create "AI Business Applications" --sources \
  https://www.mckinsey.com/capabilities/quantumblack/our-insights/seizing-the-agentic-ai-advantage \
  https://strativera.com/ai-healthcare-business-transformation-frameworks-2025/ \
  https://resources.github.com/learn/pathways/copilot/essentials/measuring-the-impact-of-github-copilot/

# 4. Ethics & Governance 노트북
python notebooklm-cli.py create "AI Ethics & Governance" --sources \
  https://www.weforum.org/stories/2026/01/scaling-trustworthy-ai-into-global-practice/ \
  https://www.inta.org/perspectives/features/how-the-eu-ai-act-supplements-gdpr-in-the-protection-of-personal-data/ \
  https://www.ibm.com/think/topics/explainable-ai

# 5. Future Trends 노트북
python notebooklm-cli.py create "AI Future Trends" --sources \
  https://www.techradar.com/ai-platforms-assistants/chatgpt/openai-roadmap-revealed-ai-research-interns-by-2026-full-blown-agi-researchers-by-2028 \
  https://www.salesmate.io/blog/future-of-ai-agents/ \
  https://www.ibm.com/think/topics/neuromorphic-computing

# 노트북 목록 확인
python notebooklm-cli.py list
```

## 🐛 트러블슈팅

### 문제: "GOOGLE_CLOUD_PROJECT_ID 환경변수가 설정되지 않았습니다"

**해결:**
```bash
export GOOGLE_CLOUD_PROJECT_ID='your-project-id'
```

### 문제: "GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다"

**해결:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account-key.json'
```

### 문제: "NotebookLM API 활성화 오류"

**해결:**
1. Google Cloud Console로 이동
2. APIs & Services > Library
3. "NotebookLM API" 검색 및 활성화
4. 프로젝트 결제 활성화 확인

### 문제: "권한 오류 (Permission Denied)"

**해결:**
1. 서비스 계정에 올바른 역할이 부여되었는지 확인:
   - NotebookLM Admin 또는
   - NotebookLM Editor
2. IAM & Admin > Service Accounts에서 역할 확인

## 📚 참고 자료

- [NotebookLM Enterprise API 공식 문서](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
- [Create and Manage Notebooks (API)](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
- [Add and Manage Data Sources (API)](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources)
- [NotebookLM Enterprise Setup Guide](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm)

## 🚀 다음 단계

1. **웹 자동화 추가**: Playwright로 무료 버전 NotebookLM 자동화
2. **배치 처리**: 여러 노트북을 한 번에 생성하는 스크립트
3. **PDF/문서 업로드**: 로컬 파일 소스 지원
4. **AI 아티클 생성**: NotebookLM API와 Claude Code를 결합한 자동 콘텐츠 생성

---

**문의 및 피드백**: 이 도구에 대한 질문이나 개선 제안이 있으시면 언제든지 알려주세요!
