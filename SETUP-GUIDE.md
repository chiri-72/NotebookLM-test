# NotebookLM 연동 설정 가이드 (10분 완성)

## 🎯 목표
Claude Code에서 NotebookLM을 제어하여 자동으로 노트북을 생성하고 관리합니다.

---

## Step 1: Google Cloud 프로젝트 생성 (3분)

### 1-1. Google Cloud Console 접속
🔗 https://console.cloud.google.com

### 1-2. 새 프로젝트 생성
1. 상단 메뉴에서 **"프로젝트 선택"** 클릭
2. **"새 프로젝트"** 클릭
3. 프로젝트 이름 입력: `notebooklm-automation`
4. **"만들기"** 클릭
5. ✅ **프로젝트 ID 복사해두기** (예: `notebooklm-automation-123456`)

---

## Step 2: NotebookLM Enterprise API 활성화 (2분)

### 2-1. API 라이브러리 이동
1. 왼쪽 메뉴 > **"APIs & Services"** > **"Library"**
2. 또는 직접 링크: https://console.cloud.google.com/apis/library

### 2-2. NotebookLM API 활성화
1. 검색창에 `NotebookLM` 입력
2. **"NotebookLM API"** 클릭
3. **"사용 설정"** 버튼 클릭
4. ✅ API 활성화 완료

⚠️ **중요**: 프로젝트에 결제 계정이 연결되어 있어야 합니다.
- 무료 크레딧($300)으로 시작 가능
- 왼쪽 메뉴 > "결제" > "결제 계정 연결"

---

## Step 3: 서비스 계정 생성 및 키 다운로드 (3분)

### 3-1. 서비스 계정 페이지 이동
1. 왼쪽 메뉴 > **"IAM & Admin"** > **"Service Accounts"**
2. 또는 직접 링크: https://console.cloud.google.com/iam-admin/serviceaccounts

### 3-2. 서비스 계정 생성
1. **"+ 서비스 계정 만들기"** 클릭
2. **서비스 계정 세부정보**:
   - 서비스 계정 이름: `notebooklm-cli`
   - 서비스 계정 ID: 자동 생성됨
   - **"만들기 및 계속하기"** 클릭

### 3-3. 역할 부여
1. **"역할 선택"** 드롭다운 클릭
2. 검색: `NotebookLM`
3. 다음 중 하나 선택:
   - ✅ **"NotebookLM Admin"** (모든 권한)
   - 또는 **"NotebookLM Editor"** (읽기/쓰기)
4. **"계속"** 클릭
5. **"완료"** 클릭

### 3-4. JSON 키 파일 다운로드
1. 생성된 서비스 계정 클릭
2. 상단 **"키"** 탭 클릭
3. **"키 추가"** > **"새 키 만들기"** 클릭
4. 키 유형: **"JSON"** 선택
5. **"만들기"** 클릭
6. ✅ **JSON 파일 자동 다운로드됨**

**다운로드된 파일을 안전한 위치로 이동:**
```bash
# 예: Downloads에서 프로젝트 폴더로 이동
mv ~/Downloads/notebooklm-automation-*.json \
   "/Users/chiri/Desktop/AI 서비스/DeepResearch/notebooklm-service-account.json"
```

⚠️ **보안 주의**: 이 JSON 파일은 매우 중요합니다. Git에 커밋하지 마세요!

---

## Step 4: 환경 변수 설정 (2분)

### 4-1. 임시 설정 (현재 터미널에만)
```bash
# Step 1에서 복사한 프로젝트 ID
export GOOGLE_CLOUD_PROJECT_ID='notebooklm-automation-123456'

# Step 3에서 다운로드한 JSON 파일 경로
export GOOGLE_APPLICATION_CREDENTIALS="/Users/chiri/Desktop/AI 서비스/DeepResearch/notebooklm-service-account.json"

# 설정 확인
echo "Project ID: $GOOGLE_CLOUD_PROJECT_ID"
echo "Credentials: $GOOGLE_APPLICATION_CREDENTIALS"
```

### 4-2. 영구 설정 (권장)
```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
echo 'export GOOGLE_CLOUD_PROJECT_ID="notebooklm-automation-123456"' >> ~/.zshrc
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/Users/chiri/Desktop/AI 서비스/DeepResearch/notebooklm-service-account.json"' >> ~/.zshrc

# 적용
source ~/.zshrc

# 확인
echo $GOOGLE_CLOUD_PROJECT_ID
```

---

## Step 5: NotebookLM CLI 설치 및 테스트 (2분)

### 5-1. 자동 설치
```bash
cd "/Users/chiri/Desktop/AI 서비스/DeepResearch/scripts"
./setup-notebooklm.sh
```

### 5-2. 수동 설치 (자동 설치 실패 시)
```bash
cd "/Users/chiri/Desktop/AI 서비스/DeepResearch/scripts"

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치
pip install google-auth google-auth-oauthlib google-auth-httplib2 requests
```

### 5-3. 테스트 실행
```bash
# 가상환경 활성화 (이미 활성화되어 있지 않다면)
source venv/bin/activate

# 노트북 목록 조회 (비어있어야 정상)
python notebooklm-cli.py list
```

**예상 출력:**
```
📚 총 0개의 노트북:
```

✅ 이 출력이 보이면 **설정 완료**!

---

## ❌ 트러블슈팅

### 문제 1: "API가 활성화되지 않았습니다"
**해결:**
1. https://console.cloud.google.com/apis/library 접속
2. NotebookLM API 검색 및 활성화
3. 5분 정도 대기 후 재시도

### 문제 2: "결제 계정이 연결되지 않았습니다"
**해결:**
1. https://console.cloud.google.com/billing 접속
2. "결제 계정 연결" 또는 "무료 체험판 시작"
3. 신용카드 등록 (무료 크레딧 $300 제공)

### 문제 3: "권한이 없습니다 (Permission Denied)"
**해결:**
1. IAM & Admin > Service Accounts 확인
2. 서비스 계정에 **"NotebookLM Admin"** 역할 부여
3. 새로 키 생성 및 다운로드

### 문제 4: "환경 변수를 찾을 수 없습니다"
**해결:**
```bash
# 현재 터미널에서 확인
echo $GOOGLE_CLOUD_PROJECT_ID
echo $GOOGLE_APPLICATION_CREDENTIALS

# 없다면 다시 설정
export GOOGLE_CLOUD_PROJECT_ID='your-project-id'
export GOOGLE_APPLICATION_CREDENTIALS='/path/to/key.json'
```

---

## ✅ 설정 완료 체크리스트

- [ ] Google Cloud 프로젝트 생성 완료
- [ ] NotebookLM API 활성화 완료
- [ ] 서비스 계정 생성 및 JSON 키 다운로드 완료
- [ ] 환경 변수 설정 완료 (GOOGLE_CLOUD_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS)
- [ ] NotebookLM CLI 설치 완료
- [ ] 테스트 실행 성공 (`python notebooklm-cli.py list`)

---

## 🎉 다음 단계

설정이 완료되었다면 Claude Code에게 알려주세요:

```
@claude, NotebookLM 환경 설정이 완료되었어. 이제 5개 노트북을 생성해줘!
```

Claude가 자동으로:
1. 5개 AI 키워드별 노트북 생성
2. 각 노트북에 10개 이상 소스 추가
3. Best 소스 기반 종합 노트북 생성
4. 6개 노트북별 4,000자 이상 아티클 생성

**예상 소요 시간**: 약 10-15분

---

## 📚 참고 자료

- [Google Cloud Console](https://console.cloud.google.com)
- [NotebookLM API 공식 문서](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
- [서비스 계정 가이드](https://cloud.google.com/iam/docs/service-accounts)

**문의사항이 있으시면 언제든지 Claude에게 물어보세요!** 🤖
