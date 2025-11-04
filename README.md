# 🎬 유튜브 이미지 자동 생성기 v2.0

노년 건강 콘텐츠용 유튜브 영상 이미지를 **Gemini 2.5 Flash Image Preview**로 자동 생성

## ✨ 주요 기능

- 📝 **대본 자동 분석**: Gemini AI가 대본을 10개 장면으로 자동 분할
- 🎨 **이미지 프롬프트 생성**: 각 장면에 최적화된 프롬프트 자동 생성
- ⚡ **병렬 비동기 처리**: 10개 이미지를 동시 생성 (4배 빠름)
- 🖼️ **실시간 이미지 표출**: 생성 즉시 각 장면에 표시
- 💾 **개별 다운로드**: 각 이미지를 개별적으로 다운로드 가능
- 📦 **ZIP 일괄 다운로드**: 모든 이미지를 ZIP으로 한 번에 다운로드
- 🍌 **Gemini Nano Banana**: Google의 공식 이미지 생성 모델 사용

## 🚀 빠른 시작

### 1. 설치
```bash
npm install
```

### 2. 환경 설정
```bash
cp .env.example .env
```

`.env` 파일 편집:
```
GEMINI_API_KEY=your_gemini_api_key_here
PORT=3000
```

### 3. Gemini API 키 발급
1. https://aistudio.google.com/app/apikey 접속
2. "Get API Key" 클릭
3. 키 복사하여 `.env`에 입력

### 4. Billing 설정 (필수)
무료 한도 초과 시:
1. https://console.cloud.google.com/billing
2. 결제 계정 생성
3. 카드 등록

### 5. 서버 실행
```bash
npm start
```

### 6. 브라우저 접속
```
http://localhost:3000
```

## 💰 비용 안내

### Gemini 2.5 Flash Image Preview

**10개 이미지 생성 비용:**
```
대본 분석: $0.003
이미지 생성: $0.41
-----------------
총: $0.41 (약 550원)
```

**100개 이미지: $4.10 (약 5,500원)**

## ⚡ v2.0 성능 향상

### 이전 (순차 처리):
```
이미지 1 → 이미지 2 → ... → 총 150초
```

### 현재 (병렬 처리):
```
이미지 1~10 동시 생성 → 총 30-40초
```

**속도 향상: 약 4배!** 🚀

## 🎨 이미지 생성 모델

**Gemini 2.5 Flash Image Preview** (`gemini-2.5-flash-image-preview`)

### 특징:
- ✅ Google 공식 이미지 생성 모델
- ✅ 고품질 이미지
- ✅ 텍스트 렌더링 우수
- ✅ 캐릭터 일관성
- ✅ 단일 API 키로 사용

### 스타일:
- **사실적 표현** (Photorealistic)
- **영화 같은 구도** (Cinematic)
- **자연스러운 조명** (Natural Warm Lighting)
- **16:9 비율** (1920x1080)

## 📖 사용 방법

1. **대본 입력**: 영상 대본 입력
2. **분석**: 10개 장면 자동 분할
3. **이미지 생성**: 병렬 방식으로 동시 생성
4. **실시간 확인**: 생성 즉시 화면에 표시
5. **다운로드**:
   - 개별: 각 이미지 하단 버튼
   - 전체: ZIP 압축 다운로드

## 🛠️ 기술 스택

- **백엔드**: Node.js, Express
- **AI**: Gemini 2.5 Flash Image Preview
- **프론트엔드**: Vanilla JavaScript, HTML5, CSS3
- **비동기**: Promise.all (병렬 처리)
- **압축**: Archiver (ZIP)
- **실시간**: Server-Sent Events (SSE)

## 📁 프로젝트 구조

```
youtube-image-generator/
├── server.js              # 병렬 처리 백엔드
├── package.json           # 의존성
├── .env.example           # 환경변수 예시
├── .gitignore             # Git 제외
├── README.md              # 문서
├── SETUP_GUIDE.md         # 설정 가이드
└── public/
    ├── index.html        # UI
    ├── app.js            # 프론트엔드 로직
    └── style.css         # 스타일
```

## 🔧 API 엔드포인트

- `POST /api/analyze-script` - 대본 분석
- `POST /api/generate-images` - 이미지 병렬 생성 (SSE)
- `GET /api/images` - 이미지 목록
- `GET /api/download-zip` - ZIP 다운로드
- `GET /images/:filename` - 개별 이미지

## 💡 프롬프트 작성 팁

### 더 나은 이미지를 위한 팁:
1. **구체적으로 작성**: "운동" → "공원에서 가벼운 스트레칭"
2. **장면 명확히**: 주제를 구분하면 정확한 이미지 생성
3. **시각적 요소**: 장소, 시간, 분위기 포함

### 생성 시간:
- 대본 분석: 30초
- 이미지 생성: 30-40초 (병렬)
- 전체: 약 1-1.5분

## 📝 라이선스

MIT License

## 🤝 기여

이슈 제보 및 Pull Request 환영합니다!

---

Made with ❤️ for 노년 건강 콘텐츠 크리에이터 | ⚡ v2.0 Gemini Nano Banana
