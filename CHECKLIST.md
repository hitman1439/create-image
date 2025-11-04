# ✅ FLUX 마이그레이션 체크리스트

## 🔧 필수 작업

### 1. 파일 교체
- [x] `server.js` - 메인 서버 파일 (FLUX 로직 포함)
- [x] `package.json` - replicate 패키지 추가
- [x] `.env.example` → `.env` - 환경변수 템플릿

### 2. 패키지 설치
```bash
npm install
```
새로 추가된 `replicate` 패키지가 자동 설치됩니다.

### 3. 환경변수 설정
`.env` 파일 생성 및 수정:
```bash
GEMINI_API_KEY=your_gemini_key_here
REPLICATE_API_TOKEN=your_replicate_token_here  # ⭐ 새로 필요!
PORT=3000
```

### 4. API 토큰 발급

#### Gemini (기존)
- https://aistudio.google.com/app/apikey
- 무료

#### Replicate (새로 필요) ⭐
- https://replicate.com/account/api-tokens
- 신규 가입 시 $5 무료 크레딧

---

## 📝 핵심 변경 사항

| 항목 | 이전 | 변경 후 |
|------|------|---------|
| **이미지 엔진** | Gemini 2.5 Flash Image | Replicate FLUX 1.1 Pro |
| **필요 토큰** | 1개 (Gemini) | 2개 (Gemini + Replicate) |
| **비용** | $0.39/10장 | $0.40/10장 |
| **속도** | ~10초/장 | ~5초/장 |
| **품질** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🚀 실행 순서

```bash
# 1. 패키지 설치
npm install

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 편집 (Gemini + Replicate 토큰)

# 3. 서버 실행
npm start

# 4. 브라우저 접속
# http://localhost:3000
```

---

## ⚠️ 주의사항

### 반드시 확인할 것:
1. ✅ `.env` 파일에 **2개의 API 키** 모두 입력
2. ✅ Replicate 계정에 크레딧 확인
3. ✅ `npm install` 완료 후 서버 시작

### 변경되지 않는 파일:
- `public/index.html` - 그대로 사용
- `public/app.js` - 그대로 사용
- `public/style.css` - 그대로 사용

프론트엔드는 수정 불필요합니다!

---

## 🎯 빠른 비용 절감 팁

더 저렴하게 사용하고 싶다면 `server.js` 수정:

```javascript
const IMAGE_CONFIG = {
  MODEL: "black-forest-labs/flux-schnell",  // 이 줄 변경
  // ...
};
```

**효과:**
- 비용: $0.40 → $0.03 (10개 기준)
- 속도: ~5초 → ~2초
- 품질: 약간 감소 (여전히 우수)

---

## 🐛 문제 해결

### "REPLICATE_API_TOKEN이 설정되지 않았습니다"
→ `.env` 파일 확인

### "replicate를 찾을 수 없습니다"
→ `npm install` 다시 실행

### 이미지 생성 실패
→ Replicate 크레딧 확인

### 생성 속도 느림
→ 정상 (5초/이미지는 빠른 편)

---

## 📊 테스트 확인

- [ ] 서버 시작 성공
- [ ] 대본 분석 작동
- [ ] 이미지 생성 작동 (10개)
- [ ] 이미지 품질 만족
- [ ] ZIP 다운로드 작동

---

## 🎉 완료!

모든 체크리스트를 완료했다면 이제 FLUX AI로 초고품질 이미지를 생성할 수 있습니다!

**FLUX의 장점:**
- 🏆 사진 같은 리얼리즘
- ⚡ 빠른 생성 속도
- 💪 높은 안정성
- 💰 합리적인 가격
