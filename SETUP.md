# 🚀 빠른 설정 가이드 (3분 완성!)

## ✅ 변경 사항

### 1. **Nano Banana (Gemini 2.5 Flash Image) 적용**
- Stability AI 대신 Google Gemini의 Nano Banana 사용
- 더 높은 품질의 이미지 생성
- 단일 API 키로 간편한 사용

### 2. **10개 이미지 생성 (테스트용)**
- 30개 → 10개로 변경
- 빠른 테스트와 비용 절감

### 3. **ZIP 다운로드**
- 개별 다운로드 → ZIP 파일 일괄 다운로드
- 편리한 파일 관리

---

## 📦 설치 및 실행

### 1단계: 패키지 설치
```bash
cd youtube-image-generator
npm install
```

### 2단계: 환경변수 설정
```bash
cp .env.example .env
```

`.env` 파일 편집:
```
GEMINI_API_KEY=여기에_API_키_입력
PORT=3000
```

### 3단계: Gemini API 키 발급
1. https://aistudio.google.com/app/apikey 접속
2. "Get API Key" 클릭
3. 생성된 키를 `.env`에 입력

### 4단계: 서버 실행
```bash
npm start
```

### 5단계: 브라우저 접속
```
http://localhost:3000
```

---

## 💰 비용

**10개 이미지 생성:**
```
분석: $0.002
이미지: $0.39 (10개)
-----------------
총: 약 520원
```

---

## 🎯 주요 기능

1. **대본 입력** → 텍스트 영역에 대본 입력
2. **분석** → 10개 장면으로 자동 분할
3. **이미지 생성** → Nano Banana로 고품질 이미지 생성
4. **ZIP 다운로드** → 모든 이미지를 ZIP으로 다운로드

---

## 🔧 문제 해결

### Q: "GEMINI_API_KEY가 설정되지 않았습니다" 에러
A: `.env` 파일에 API 키를 입력했는지 확인

### Q: 이미지 생성이 안 됩니다
A: 
1. API 키가 올바른지 확인
2. Google AI Studio에서 Gemini API 활성화 확인
3. 네트워크 연결 확인

### Q: Nano Banana 모델을 찾을 수 없습니다
A: Gemini API가 최신 버전인지 확인 (`npm update @google/generative-ai`)

---

## 🎉 완료!

이제 http://localhost:3000 에서 사용할 수 있습니다!
