require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const archiver = require('archiver');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public'));

// 출력 디렉토리 생성
const OUTPUT_DIR = path.join(__dirname, 'generated_images');
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Gemini API 초기화
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// 이미지 생성 설정
const IMAGE_CONFIG = {
  MODEL: "gemini-2.0-flash-exp",
  LANGUAGE: "ko",
  OUTPUT_RULES: {
    exact_image_count: 10,            // 테스트용 10개
    aspect_ratio: "16:9",           // 유튜브 표준 비율 (가로로 긴 구도)
    resolution: "1920x1080",        // Full HD
    disallow: ["collage", "grid", "text", "logo", "watermark"]
  },
  STYLE: {
    photorealist: true,
    cinematic: true,
    color_grade: "natural warm",
    lighting: "natural warm",
    skin_texture: "natural",
    film_grain: "subtle"
  }
};

// 1. 대본 분석하여 30개 장면 추출
app.post('/api/analyze-script', async (req, res) => {
  try {
    const { script } = req.body;
    
    if (!script) {
      return res.status(400).json({ error: '대본을 입력해주세요.' });
    }

    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });
    
    const prompt = `
당신은 노년 건강 콘텐츠 전문가입니다. 다음 유튜브 영상 대본을 분석하여 정확히 10개의 장면으로 나누고, 각 장면에 맞는 이미지 생성 프롬프트를 만들어주세요.

**프롬프트 작성 스타일 (매우 중요!)**:

모든 프롬프트는 다음 예시와 같은 **형식, 디테일 수준, 톤, 분위기**를 유지해야 합니다:

예시 (사람이 나오는 장면):
"A warm and realistic photo of an elderly Korean woman eating alone in a cozy restaurant. She has short gray hair and gentle facial features, wearing a dark cardigan over a patterned blouse. She is using chopsticks to eat noodles from a white bowl, with a bowl of rice and a glass of water on the table. The lighting is soft and warm, with blurred background showing other people dining. The mood feels peaceful and intimate, captured in a natural, documentary-style composition."

예시 (음식만 나오는 장면):
"A warm and realistic photo of a healthy Korean breakfast spread on a natural wooden table. The composition features a white ceramic bowl filled with steaming mixed grain rice, topped with black sesame seeds. Next to it, two perfectly soft-boiled eggs sit on a small white plate. Fresh seasonal fruits including persimmon slices and apple wedges are arranged on a light blue ceramic dish. A traditional Korean tea cup with green tea completes the scene. Soft morning sunlight streams from the left, creating gentle highlights and shadows. The overall mood is warm, healthy, and inviting, captured in a natural, slightly overhead documentary-style composition."

예시 (장소/환경만 나오는 장면):
"A warm and realistic photo of a serene park walking path in the early morning. The scene shows a clean paved walkway lined with lush green trees on both sides, their leaves creating dappled shadows on the ground. A few wooden benches are placed along the path. Soft golden sunlight filters through the foliage, creating a peaceful atmosphere. The composition is captured at eye-level, showing the inviting path stretching into the distance, with a natural documentary-style aesthetic."

**핵심 원칙**:

1. **장면 내용에 맞게 피사체를 선택**:
   - 대본이 사람의 행동을 말하면 → 사람 중심 이미지
   - 대본이 음식/식단을 말하면 → 음식 중심 이미지 (사람 없이)
   - 대본이 장소/환경을 말하면 → 환경 중심 이미지 (사람 없이)
   - 대본이 도구/물건을 말하면 → 사물 중심 이미지 (사람 없이)

2. **항상 유지해야 할 공통 요소**:
   ✅ "A warm and realistic photo of..."로 시작
   ✅ 16:9 aspect ratio (가로로 긴 구도)
   ✅ 매우 구체적이고 상세한 묘사 (최소 50단어)
   ✅ 조명 설명: "soft and warm lighting", "natural daylight", "golden sunlight" 등
   ✅ 분위기/무드: "peaceful", "inviting", "calm", "healthy", "professional" 등
   ✅ 촬영 스타일: "natural, documentary-style composition"
   ✅ 구도/앵글: "overhead", "eye-level", "slightly angled" 등

3. **사람이 나올 때 포함할 요소**:
   - "an elderly Korean man/woman"
   - 나이대: 60-80세
   - 외모: 머리 스타일, 피부톤
   - 의상: 구체적인 옷차림과 색상
   - 표정: 평화로운, 집중하는, 미소 짓는 등
   - 행동: 무엇을 하는지 상세히

4. **사물/배경만 나올 때 포함할 요소**:
   - 사물의 배치, 색상, 재질, 크기
   - 주변 환경과 맥락
   - 텍스처와 디테일
   - 빛과 그림자의 방향

**이미지 스타일 통일**:
- Photorealistic, natural photography
- Korean context and aesthetic
- Warm, inviting, trustworthy atmosphere
- Documentary-style, authentic moments
- No text, logos, watermarks, or graphics
- No collage or grid layouts

**JSON 형식으로만 응답**해주세요:
\`\`\`json
[
  {
    "scene_number": 1,
    "timestamp": "00:00-00:10",
    "description": "장면에 대한 한글 설명 (예: 건강한 아침 식사 이미지)",
    "image_prompt": "A warm and realistic photo of... (장면 내용에 맞게, 하지만 위 예시들과 같은 스타일과 디테일로, 최소 50단어)",
    "keywords": ["health", "breakfast", "food"]
  }
]
\`\`\`

**대본**:
${script}

정확히 10개의 장면을 만들어주세요.
각 장면의 내용을 분석하여 사람/음식/환경 중 가장 적합한 피사체를 선택하세요.
각 image_prompt는 위 예시들처럼 매우 구체적이고 상세해야 합니다 (최소 50단어).
모든 이미지는 16:9 비율로 가로로 긴 구도입니다.
JSON만 출력하고 다른 설명은 하지 마세요.
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    let text = response.text();
    
    // JSON 추출 (코드 블록 제거)
    text = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    const scenes = JSON.parse(text);
    
    if (!Array.isArray(scenes) || scenes.length !== 10) {
      throw new Error('10개의 장면이 생성되지 않았습니다.');
    }

    res.json({ 
      success: true, 
      scenes,
      config: IMAGE_CONFIG
    });

  } catch (error) {
    console.error('대본 분석 오류:', error);
    res.status(500).json({ 
      error: '대본 분석 중 오류가 발생했습니다.', 
      details: error.message 
    });
  }
});

// 2. 이미지 생성 (Gemini Nano Banana - Gemini 2.5 Flash Image)
app.post('/api/generate-images', async (req, res) => {
  try {
    const { scenes } = req.body;
    
    if (!scenes || !Array.isArray(scenes)) {
      return res.status(400).json({ error: '장면 데이터가 필요합니다.' });
    }

    if (!process.env.GEMINI_API_KEY) {
      return res.status(500).json({ 
        error: 'GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.' 
      });
    }

    // Gemini Image 모델 초기화 (Nano Banana)
    const imageModel = genAI.getGenerativeModel({ 
      model: "gemini-2.5-flash-image"
    });

    // SSE (Server-Sent Events)로 진행상황 전송
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const sendProgress = (data) => {
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    };

    sendProgress({ 
      type: 'info', 
      message: '🍌 Gemini Nano Banana로 이미지 생성을 시작합니다...' 
    });

    // 각 장면에 대한 이미지 생성
    for (let i = 0; i < scenes.length; i++) {
      const scene = scenes[i];
      
      sendProgress({
        type: 'progress',
        current: i + 1,
        total: scenes.length,
        scene: scene.description
      });

      try {
        // Gemini 2.5 Flash Image API로 이미지 생성
        const result = await imageModel.generateContent([
          scene.image_prompt
        ]);

        const response = await result.response;
        
        // 응답에서 이미지 데이터 추출
        if (response.candidates && response.candidates[0]) {
          const candidate = response.candidates[0];
          
          // 이미지 URL 또는 데이터 추출
          let imageData = null;
          
          if (candidate.content && candidate.content.parts) {
            for (const part of candidate.content.parts) {
              if (part.inlineData) {
                imageData = part.inlineData.data;
                break;
              } else if (part.fileData && part.fileData.fileUri) {
                // fileUri가 있는 경우 다운로드
                const imageUrl = part.fileData.fileUri;
                const imageResponse = await axios.get(imageUrl, { 
                  responseType: 'arraybuffer' 
                });
                imageData = Buffer.from(imageResponse.data).toString('base64');
                break;
              }
            }
          }

          if (imageData) {
            // Base64 이미지를 파일로 저장
            const imagePath = path.join(
              OUTPUT_DIR, 
              `scene_${String(scene.scene_number).padStart(2, '0')}.png`
            );
            
            const buffer = Buffer.from(imageData, 'base64');
            fs.writeFileSync(imagePath, buffer);
            
            sendProgress({
              type: 'image_saved',
              message: `✅ 장면 ${scene.scene_number} 저장 완료`,
              path: imagePath.replace(OUTPUT_DIR, '').substring(1),
              scene_number: scene.scene_number
            });
          } else {
            throw new Error('이미지 데이터를 찾을 수 없습니다');
          }
        } else {
          throw new Error('응답에서 이미지를 생성할 수 없습니다');
        }

      } catch (error) {
        console.error(`장면 ${i + 1} 생성 오류:`, error);
        sendProgress({
          type: 'error',
          message: `❌ 장면 ${scene.scene_number} 생성 실패: ${error.message}`,
          scene_number: scene.scene_number
        });
        // 오류가 나도 계속 진행
      }

      // API rate limit 방지를 위한 약간의 딜레이
      if (i < scenes.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    sendProgress({ 
      type: 'complete', 
      message: '🎉 모든 이미지 생성 완료!' 
    });
    
    res.end();

  } catch (error) {
    console.error('이미지 생성 오류:', error);
    res.write(`data: ${JSON.stringify({ 
      type: 'error', 
      message: error.message 
    })}\n\n`);
    res.end();
  }
});

// 3. 생성된 이미지 제공
app.get('/api/images', (req, res) => {
  try {
    if (!fs.existsSync(OUTPUT_DIR)) {
      return res.json({ images: [] });
    }

    const files = fs.readdirSync(OUTPUT_DIR)
      .filter(file => file.endsWith('.png'))
      .sort()
      .map(file => ({
        filename: file,
        path: `/images/${file}`,
        scene_number: parseInt(file.match(/\d+/)?.[0] || '0')
      }));

    res.json({ images: files });
  } catch (error) {
    console.error('이미지 목록 조회 오류:', error);
    res.status(500).json({ error: error.message });
  }
});

// 4. 개별 이미지 파일 제공
app.use('/images', express.static(OUTPUT_DIR));

// 5. 모든 이미지를 ZIP으로 다운로드
app.get('/api/download-zip', (req, res) => {
  try {
    if (!fs.existsSync(OUTPUT_DIR)) {
      return res.status(404).json({ error: '생성된 이미지가 없습니다.' });
    }

    const files = fs.readdirSync(OUTPUT_DIR)
      .filter(file => file.endsWith('.png'))
      .sort();

    if (files.length === 0) {
      return res.status(404).json({ error: '다운로드할 이미지가 없습니다.' });
    }

    // ZIP 파일 생성
    const archive = archiver('zip', {
      zlib: { level: 9 } // 최대 압축
    });

    // 에러 핸들링
    archive.on('error', (err) => {
      console.error('ZIP 생성 오류:', err);
      res.status(500).json({ error: err.message });
    });

    // HTTP 헤더 설정
    const timestamp = new Date().toISOString().slice(0, 10);
    res.attachment(`youtube-images-${timestamp}.zip`);
    res.setHeader('Content-Type', 'application/zip');

    // 스트림 연결
    archive.pipe(res);

    // 이미지 파일들을 ZIP에 추가
    files.forEach(file => {
      const filePath = path.join(OUTPUT_DIR, file);
      archive.file(filePath, { name: file });
    });

    // ZIP 완성
    archive.finalize();

    console.log(`ZIP 다운로드: ${files.length}개 파일`);

  } catch (error) {
    console.error('ZIP 다운로드 오류:', error);
    res.status(500).json({ error: error.message });
  }
});

// 서버 시작
app.listen(PORT, () => {
  console.log(`🚀 서버가 http://localhost:${PORT} 에서 실행중입니다.`);
  console.log(`📁 이미지 저장 경로: ${OUTPUT_DIR}`);
});
