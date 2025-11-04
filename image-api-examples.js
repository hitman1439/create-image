/**
 * 이미지 생성 API 연동 예시
 * 
 * Gemini API는 텍스트 생성만 지원하므로,
 * 실제 이미지 생성을 위해서는 아래 API 중 하나를 선택하여 연동해야 합니다.
 */

// ============================================
// 옵션 1: Stability AI (Stable Diffusion XL)
// ============================================
// npm install replicate

const Replicate = require('replicate');

async function generateWithStabilityAI(prompt) {
  const replicate = new Replicate({
    auth: process.env.REPLICATE_API_TOKEN,
  });

  const output = await replicate.run(
    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    {
      input: {
        prompt: prompt,
        width: 1920,
        height: 1080,
        num_outputs: 1,
        scheduler: "K_EULER",
        guidance_scale: 7.5,
        num_inference_steps: 50
      }
    }
  );

  return output[0]; // 이미지 URL 반환
}

// ============================================
// 옵션 2: Leonardo.ai
// ============================================
// npm install axios

const axios = require('axios');

async function generateWithLeonardo(prompt) {
  const response = await axios.post(
    'https://cloud.leonardo.ai/api/rest/v1/generations',
    {
      prompt: prompt,
      modelId: 'e316348f-7773-490e-adcd-46757c738eb7', // Leonardo Diffusion XL
      width: 1920,
      height: 1080,
      num_images: 1,
      guidance_scale: 7,
      sd_version: 'SDXL_1_0'
    },
    {
      headers: {
        'Authorization': `Bearer ${process.env.LEONARDO_API_KEY}`,
        'Content-Type': 'application/json'
      }
    }
  );

  const generationId = response.data.sdGenerationJob.generationId;
  
  // 이미지 생성 대기 (폴링)
  await new Promise(resolve => setTimeout(resolve, 10000));
  
  const resultResponse = await axios.get(
    `https://cloud.leonardo.ai/api/rest/v1/generations/${generationId}`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.LEONARDO_API_KEY}`
      }
    }
  );

  return resultResponse.data.generations_by_pk.generated_images[0].url;
}

// ============================================
// 옵션 3: OpenAI DALL-E 3
// ============================================
// npm install openai

const OpenAI = require('openai');

async function generateWithDALLE3(prompt) {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
  });

  const response = await openai.images.generate({
    model: "dall-e-3",
    prompt: prompt,
    n: 1,
    size: "1792x1024", // DALL-E 3는 16:9가 정확하지 않음
    quality: "hd"
  });

  return response.data[0].url;
}

// ============================================
// server.js에 통합하는 방법
// ============================================

// 1. 위의 함수 중 하나를 선택하여 server.js 상단에 추가

// 2. /api/generate-images 엔드포인트 수정:

app.post('/api/generate-images', async (req, res) => {
  try {
    const { scenes } = req.body;
    
    if (!scenes || !Array.isArray(scenes)) {
      return res.status(400).json({ error: '장면 데이터가 필요합니다.' });
    }

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const sendProgress = (data) => {
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    };

    // 각 장면에 대해 이미지 생성
    for (let i = 0; i < scenes.length; i++) {
      const scene = scenes[i];
      
      sendProgress({
        type: 'progress',
        current: i + 1,
        total: scenes.length,
        scene: scene.description
      });

      try {
        // ⭐ 여기서 실제 이미지 생성 API 호출
        const imageUrl = await generateWithStabilityAI(scene.image_prompt);
        
        // 이미지 다운로드 및 저장
        const imageResponse = await axios.get(imageUrl, { 
          responseType: 'arraybuffer' 
        });
        
        const imagePath = path.join(
          OUTPUT_DIR, 
          `scene_${String(i + 1).padStart(2, '0')}.png`
        );
        
        fs.writeFileSync(imagePath, imageResponse.data);
        
        sendProgress({
          type: 'image_saved',
          path: imagePath,
          scene_number: i + 1
        });

      } catch (error) {
        sendProgress({
          type: 'error',
          message: `장면 ${i + 1} 생성 실패: ${error.message}`,
          scene_number: i + 1
        });
      }
    }

    sendProgress({ 
      type: 'complete', 
      message: '모든 이미지 생성 완료!' 
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

// ============================================
// 비용 및 속도 비교
// ============================================

/*
1. Stability AI (Replicate)
   - 비용: $0.0023/이미지
   - 속도: ~10초/이미지
   - 품질: ⭐⭐⭐⭐⭐
   - 추천: ✅ 최고의 가성비

2. Leonardo.ai
   - 비용: 무료 티어 있음
   - 속도: ~15초/이미지
   - 품질: ⭐⭐⭐⭐
   - 추천: ✅ 무료로 시작하기 좋음

3. DALL-E 3
   - 비용: $0.04/이미지 (HD)
   - 속도: ~20초/이미지
   - 품질: ⭐⭐⭐⭐⭐
   - 추천: 예산이 충분한 경우

30개 이미지 기준:
- Stability AI: $0.07
- Leonardo.ai: 무료 (제한적)
- DALL-E 3: $1.20
*/

module.exports = {
  generateWithStabilityAI,
  generateWithLeonardo,
  generateWithDALLE3
};
