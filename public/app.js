// 전역 변수
let analyzedScenes = [];
let generatedImages = [];

// DOM 요소
const scriptInput = document.getElementById('scriptInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const generateBtn = document.getElementById('generateBtn');
const editBtn = document.getElementById('editBtn');
const downloadAllBtn = document.getElementById('downloadAllBtn');
const restartBtn = document.getElementById('restartBtn');

const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');
const step3 = document.getElementById('step3');
const step4 = document.getElementById('step4');

const scenesPreview = document.getElementById('scenesPreview');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const generationLog = document.getElementById('generationLog');
const imagesGrid = document.getElementById('imagesGrid');
const loadingOverlay = document.getElementById('loadingOverlay');

// 유틸리티 함수
function showLoading() {
  loadingOverlay.style.display = 'flex';
}

function hideLoading() {
  loadingOverlay.style.display = 'none';
}

function showStep(stepNumber) {
  [step1, step2, step3, step4].forEach(step => step.style.display = 'none');
  
  switch(stepNumber) {
    case 1: step1.style.display = 'block'; break;
    case 2: step2.style.display = 'block'; break;
    case 3: step3.style.display = 'block'; break;
    case 4: step4.style.display = 'block'; break;
  }
  
  // 부드러운 스크롤
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function addLogEntry(message, type = 'info') {
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  generationLog.appendChild(entry);
  generationLog.scrollTop = generationLog.scrollHeight;
}

// 1. 대본 분석
analyzeBtn.addEventListener('click', async () => {
  const script = scriptInput.value.trim();
  
  if (!script) {
    alert('대본을 입력해주세요!');
    return;
  }
  
  if (script.length < 100) {
    alert('대본이 너무 짧습니다. 더 자세한 내용을 입력해주세요.');
    return;
  }
  
  showLoading();
  
  try {
    const response = await fetch('/api/analyze-script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script })
    });
    
    if (!response.ok) {
      throw new Error('대본 분석에 실패했습니다.');
    }
    
    const data = await response.json();
    analyzedScenes = data.scenes;
    
    // 장면 미리보기 렌더링
    renderScenesPreview();
    
    hideLoading();
    showStep(2);
    
  } catch (error) {
    hideLoading();
    alert(`오류 발생: ${error.message}`);
    console.error(error);
  }
});

// 장면 미리보기 렌더링
function renderScenesPreview() {
  scenesPreview.innerHTML = '';
  
  analyzedScenes.forEach((scene, index) => {
    const sceneCard = document.createElement('div');
    sceneCard.className = 'scene-card';
    sceneCard.innerHTML = `
      <span class="scene-number">장면 ${scene.scene_number}</span>
      <h3>${scene.description}</h3>
      <p><strong>프롬프트:</strong> ${scene.image_prompt.substring(0, 100)}...</p>
      <p><strong>키워드:</strong> ${scene.keywords.join(', ')}</p>
    `;
    scenesPreview.appendChild(sceneCard);
  });
}

// 2. 이미지 생성
generateBtn.addEventListener('click', async () => {
  if (analyzedScenes.length === 0) {
    alert('먼저 대본을 분석해주세요!');
    return;
  }
  
  showStep(3);
  generationLog.innerHTML = ''; // 로그 초기화
  
  try {
    const response = await fetch('/api/generate-images', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenes: analyzedScenes })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          
          if (data.type === 'progress') {
            const percent = (data.current / data.total) * 100;
            progressFill.style.width = `${percent}%`;
            progressText.textContent = `${data.current} / ${data.total}`;
            addLogEntry(`🎨 장면 ${data.current}: ${data.scene}`);
          } else if (data.type === 'image_saved') {
            addLogEntry(data.message);
            generatedImages.push(data.path);
          } else if (data.type === 'complete') {
            addLogEntry('✅ ' + data.message, 'success');
            // 이미지 로드
            await loadGeneratedImages();
            setTimeout(() => showStep(4), 1000);
          } else if (data.type === 'error') {
            addLogEntry('❌ ' + data.message, 'error');
          } else if (data.type === 'info') {
            addLogEntry('ℹ️ ' + data.message, 'info');
          }
        }
      }
    }
    
  } catch (error) {
    addLogEntry(`오류: ${error.message}`, 'error');
    console.error(error);
  }
});

// 생성된 이미지 로드 함수
async function loadGeneratedImages() {
  try {
    const response = await fetch('/api/images');
    const data = await response.json();
    
    imagesGrid.innerHTML = '';
    
    if (data.images && data.images.length > 0) {
      data.images.forEach(img => {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.innerHTML = `
          <img src="${img.path}" alt="Scene ${img.scene_number}">
          <div class="image-overlay">
            <strong>장면 ${img.scene_number}</strong>
            <br>${img.filename}
          </div>
        `;
        imagesGrid.appendChild(imageItem);
      });
    }
  } catch (error) {
    console.error('이미지 로드 오류:', error);
  }
}

// 3. 장면 편집 (간단한 재분석)
editBtn.addEventListener('click', () => {
  if (confirm('장면을 다시 분석하시겠습니까?')) {
    showStep(1);
  }
});

// 4. ZIP 다운로드
downloadAllBtn.addEventListener('click', async () => {
  try {
    showLoading();
    
    const response = await fetch('/api/images');
    const data = await response.json();
    
    if (!data.images || data.images.length === 0) {
      hideLoading();
      alert('다운로드할 이미지가 없습니다.');
      return;
    }
    
    // ZIP 파일 다운로드
    const link = document.createElement('a');
    link.href = '/api/download-zip';
    link.download = `youtube-images-${new Date().toISOString().slice(0, 10)}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    hideLoading();
    alert(`${data.images.length}개의 이미지를 ZIP으로 다운로드합니다!`);
    
  } catch (error) {
    hideLoading();
    alert(`다운로드 오류: ${error.message}`);
    console.error(error);
  }
});

// 5. 새로 시작
restartBtn.addEventListener('click', () => {
  if (confirm('처음부터 다시 시작하시겠습니까?')) {
    scriptInput.value = '';
    analyzedScenes = [];
    generatedImages = [];
    scenesPreview.innerHTML = '';
    generationLog.innerHTML = '';
    progressFill.style.width = '0%';
    progressText.textContent = '0 / 10';
    showStep(1);
  }
});

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
  showStep(1);
  console.log('🎬 유튜브 이미지 생성기 준비 완료!');
});
