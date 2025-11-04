# 🎬 유튜브 이미지 자동 생성기 (FLUX Edition)

노년 건강 콘텐츠용 유튜브 영상 이미지를 Gemini AI + Replicate FLUX로 자동 생성하는 시스템

## ✨ 주요 기능

- 📝 **대본 자동 분석**: Gemini AI가 대본을 분석하여 10개 장면으로 자동 분할
- 🎨 **이미지 프롬프트 생성**: 각 장면에 최적화된 이미지 생성 프롬프트 자동 생성
- ⚡ **FLUX 이미지 생성**: Replicate FLUX AI로 초고품질 이미지 자동 생성 (16:9, 1920x1080)
- 📊 **실시간 진행률**: 생성 과정을 실시간으로 확인
- 📦 **ZIP 다운로드**: 생성된 이미지를 ZIP 파일로 한 번에 다운로드

## 🚀 빠른 시작

### 1. 설치

```bash
cd youtube-image-generator
npm install
```

### 2. 환경 설정

`.env` 파일을 생성하고 API 키를 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일 편집:
```
GEMINI_API_KEY=your_gemini_api_key_here
REPLICATE_API_TOKEN=your_replicate_token_here
PORT=3000
```

### 3. API 키 발급

#### Gemini API 키 (무료)
1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. "Get API Key" 클릭
3. 생성된 키를 `.env` 파일에 입력

#### Replicate API 토큰
1. [Replicate](https://replicate.com) 가입
2. [API Tokens 페이지](https://replicate.com/account/api-tokens) 접속
3. "Create token" 클릭
4. 생성된 토큰을 `.env` 파일에 입력

💡 **Replicate 크레딧**: 신규 가입 시 무료 크레딧 제공됩니다.

### 4. 서버 실행

```bash
# 개발 모드
npm run dev

# 프로덕션 모드
npm start
```

### 5. 브라우저에서 접속

```
http://localhost:3000
```

## 📖 사용 방법

1. **대본 입력**: 유튜브 영상 대본을 텍스트 영역에 입력
2. **분석 시작**: "대본 분석하기" 버튼 클릭
3. **장면 확인**: 자동 생성된 10개 장면 미리보기
4. **이미지 생성**: "이미지 생성 시작" 버튼 클릭
5. **ZIP 다운로드**: 생성된 이미지를 ZIP 파일로 다운로드

## 💰 비용 안내

### FLUX 1.1 Pro (추천)

**10개 이미지 생성 비용:**
```
Gemini 분석: $0.002 (무시할 수준)
FLUX 1.1 Pro: $0.40 (10개 × $0.04)
-------------------------------------------
총 비용: 약 $0.40 (약 550원)
```

**장점:**
- ✅ 최고 품질의 이미지
- ✅ 뛰어난 텍스트 렌더링
- ✅ 자연스러운 사람 표현
- ✅ 빠른 생성 속도 (~5초/이미지)

### FLUX Schnell (빠른 생성용)

모델을 `black-forest-labs/flux-schnell`로 변경하면:
```
비용: $0.003/이미지
속도: ~2초/이미지
품질: ⭐⭐⭐⭐ (Pro보다 약간 낮음)
```

## ⚙️ 모델 변경 방법

`server.js` 파일의 `IMAGE_CONFIG`에서 모델을 변경할 수 있습니다:

```javascript
const IMAGE_CONFIG = {
  MODEL: "black-forest-labs/flux-1.1-pro",  // 최고 품질 (추천)
  // MODEL: "black-forest-labs/flux-schnell", // 빠른 생성용
  // ...
};
```

## ⚠️ 완전 작동 시스템

이 시스템은 **Replicate FLUX AI**를 사용하여 실제로 이미지를 생성합니다.

**구현 완료된 기능:**
- ✅ 대본 분석 및 장면 추출
- ✅ 이미지 프롬프트 자동 생성
- ✅ 실제 이미지 생성 (FLUX AI)
- ✅ 실시간 진행 상황 표시
- ✅ ZIP 파일 다운로드
- ✅ UI/UX 완성

## 🎨 이미지 스타일

기본 스타일은 노년 건강 콘텐츠에 최적화되어 있습니다:

- **사실적 표현** (Photorealistic)
- **영화 같은 구도** (Cinematic)
- **자연스러운 따뜻한 조명** (Natural Warm Lighting)
- **부드러운 필름 그레인** (Subtle Film Grain)
- **16:9 비율, Full HD (1920x1080)**

## 💡 사용 팁

### 더 나은 이미지를 위한 대본 작성법:
1. **구체적인 설명 사용**: "운동하기" 보다 "공원에서 가벼운 스트레칭하기"
2. **장면 나누기**: 주제를 명확하게 구분하면 더 정확한 이미지 생성
3. **시각적 요소 포함**: 장소, 시간대, 분위기 등을 대본에 포함

### 생성 시간:
- 대본 분석: 약 30초
- 이미지 생성 (FLUX 1.1 Pro): 장면당 약 5-7초
- 전체 10개: 약 1-2분

### 문제 해결:
- **이미지 품질이 낮다면**: 프롬프트를 더 상세하게 수정
- **생성 실패**: API 키 확인 및 Replicate 크레딧 확인
- **느린 속도**: 인터넷 연결 및 Replicate 서버 상태 확인

## 🛠️ 기술 스택

- **백엔드**: Node.js, Express
- **AI 분석**: Google Gemini 2.0 Flash
- **이미지 생성**: Replicate FLUX 1.1 Pro
- **프론트엔드**: Vanilla JavaScript, HTML5, CSS3
- **HTTP**: Server-Sent Events (SSE) for real-time updates
- **압축**: Archiver (ZIP 생성)

## 🆚 FLUX vs 다른 모델 비교

| 특징 | FLUX 1.1 Pro | Stable Diffusion XL | DALL-E 3 |
|------|-------------|---------------------|----------|
| 품질 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 속도 | ~5초 | ~10초 | ~20초 |
| 가격 | $0.04 | $0.002 | $0.08 |
| 텍스트 | 우수 | 보통 | 우수 |
| 사람 | 탁월 | 좋음 | 탁월 |

**FLUX 1.1 Pro 선택 이유:**
- 🏆 최고 수준의 이미지 품질
- ⚡ 빠른 생성 속도
- 💰 합리적인 가격
- 🎯 노년층 표현에 최적화

## 📝 라이선스

MIT License

## 🤝 기여

이슈 제보 및 풀 리퀘스트 환영합니다!

---

Made with ❤️ for 노년 건강 콘텐츠 크리에이터

**Powered by:**
- 🧠 Google Gemini AI
- 🎨 Replicate FLUX 1.1 Pro
