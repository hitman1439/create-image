// 전역 변수
let analyzedScenes = [];
let generatedImages = {};

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

const scenesPreview = document.getElementById('scenesPreview');
const generationStatus = document.getElementById('generationStatus');
const loadingOverlay = document.getElementById('loadingOverlay');

// 유틸리티 함수
function showLoading() {
  loadingOverlay.style.display = 'flex';
}

function hideLoading() {
  loadingOverlay.style.display = 'none';
}

function showStep(stepNumber) {
  [step1, step2, step3].forEach(step => step.style.display = 'none');
  
  switch(stepNumber) {
    case 1: step1.style.display = 'block'; break;
    case 2: step2.style.display = 'block'; break;
    case 3: step3.style.display = 'block'; break;
  }
  
  // 부드러운 스크롤
  window.scrollTo({ top: 0, behavior: 'smooth' });
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

// 장면 미리보기 렌더링 (이미지 플레이스홀더 포함)
function renderScenesPreview() {
  scenesPreview.innerHTML = '';
  
  analyzedScenes.forEach((scene, index) => {
    const sceneCard = document.createElement('div');
    sceneCard.className = 'scene-card';
    sceneCard.id = `scene-card-${scene.scene_number}`;
    sceneCard.innerHTML = `
      <div class="scene-header">
        <span class="scene-number">장면 ${scene.scene_number}</span>
        <div class="scene-status" id="status-${scene.scene_number}">
          <span class="status-badge">대기중</span>
        </div>
      </div>
      <h3>${scene.description}</h3>
      
      <!-- 이미지 영역 -->
      <div class="scene-image-container" id="image-container-${scene.scene_number}">
        <div class="image-placeholder">
          <span class="placeholder-icon">🖼️</span>
          <p>이미지가 여기에 표시됩니다</p>
        </div>
      </div>
      
      <div class="scene-details">
        <p><strong>프롬프트:</strong> ${scene.image_prompt.substring(0, 100)}...</p>
        <p><strong>키워드:</strong> ${scene.keywords.join(', ')}</p>
      </div>
      
      <!-- 개별 다운로드 버튼 (이미지 생성 후 표시) -->
      <div class="download-btn-container" id="download-btn-${scene.scene_number}" style="display: none;">
        <button class="btn btn-download" onclick="downloadSingleImage(${scene.scene_number})">
          <span class="btn-icon">💾</span>
          이 이미지 다운로드
        </button>
      </div>
    `;
    scenesPreview.appendChild(sceneCard);
  });
}

// 2. 이미지 생성 (병렬 처리)
generateBtn.addEventListener('click', async () => {
  if (analyzedScenes.length === 0) {
    alert('먼저 대본을 분석해주세요!');
    return;
  }
  
  showStep(3);
  generationStatus.innerHTML = '<p class="status-message">🚀 병렬 방식으로 10개 이미지를 동시 생성합니다...</p>';
  
  // Step2의 장면 카드 초기화
  analyzedScenes.forEach(scene => {
    updateSceneStatus(scene.scene_number, 'pending', '대기중');
  });
  
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
          handleSSEEvent(data);
        }
      }
    }
    
  } catch (error) {
    addStatusMessage(`❌ 오류: ${error.message}`, 'error');
    console.error(error);
  }
});

// SSE 이벤트 핸들러
function handleSSEEvent(data) {
  switch(data.type) {
    case 'info':
      addStatusMessage(`ℹ️ ${data.message}`, 'info');
      break;
      
    case 'start':
      updateSceneStatus(data.scene_number, 'generating', '생성중...');
      addStatusMessage(`🎨 ${data.message}`);
      break;
      
    case 'image_complete':
      // 실시간으로 이미지 표시
      displayImageInScene(data.scene_number, data.imageData, data.path);
      updateSceneStatus(data.scene_number, 'complete', '완료');
      addStatusMessage(`✅ ${data.message}`, 'success');
      
      // 생성된 이미지 정보 저장
      generatedImages[data.scene_number] = {
        path: data.path,
        imageData: data.imageData
      };
      break;
      
    case 'error':
      updateSceneStatus(data.scene_number, 'error', '실패');
      addStatusMessage(`❌ ${data.message}`, 'error');
      break;
      
    case 'complete':
      addStatusMessage(`🎉 ${data.message}`, 'success');
      // 모든 이미지 생성 완료 후 전체 다운로드 버튼 활성화
      if (data.successCount > 0) {
        downloadAllBtn.disabled = false;
      }
      break;
  }
}

// 장면 상태 업데이트
function updateSceneStatus(sceneNumber, status, text) {
  const statusElement = document.getElementById(`status-${sceneNumber}`);
  if (statusElement) {
    const badge = statusElement.querySelector('.status-badge');
    badge.textContent = text;
    badge.className = `status-badge status-${status}`;
  }
}

// 이미지를 장면 카드에 실시간 표시
function displayImageInScene(sceneNumber, imageData, imagePath) {
  const container = document.getElementById(`image-container-${sceneNumber}`);
  if (container) {
    container.innerHTML = `
      <img src="data:image/png;base64,${imageData}" alt="Scene ${sceneNumber}" class="scene-image">
      <div class="image-overlay">
        <span>✓ 생성 완료</span>
      </div>
    `;
    
    // 개별 다운로드 버튼 표시
    const downloadBtnContainer = document.getElementById(`download-btn-${sceneNumber}`);
    if (downloadBtnContainer) {
      downloadBtnContainer.style.display = 'block';
    }
  }
}

// 상태 메시지 추가
function addStatusMessage(message, type = 'info') {
  const messageDiv = document.createElement('p');
  messageDiv.className = `status-message status-${type}`;
  messageDiv.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  generationStatus.appendChild(messageDiv);
  generationStatus.scrollTop = generationStatus.scrollHeight;
}

// 3. 개별 이미지 다운로드
function downloadSingleImage(sceneNumber) {
  const imageInfo = generatedImages[sceneNumber];
  if (!imageInfo) {
    alert('이미지 정보를 찾을 수 없습니다.');
    return;
  }
  
  // Base64를 Blob으로 변환
  const byteString = atob(imageInfo.imageData);
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }
  const blob = new Blob([ab], { type: 'image/png' });
  
  // 다운로드 트리거
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `scene_${String(sceneNumber).padStart(2, '0')}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
  
  console.log(`이미지 ${sceneNumber} 다운로드 완료`);
}

// 전역으로 노출 (HTML에서 호출 가능)
window.downloadSingleImage = downloadSingleImage;

// 4. 전체 ZIP 다운로드
downloadAllBtn.addEventListener('click', async () => {
  try {
    showLoading();
    
    const imageCount = Object.keys(generatedImages).length;
    
    if (imageCount === 0) {
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
    alert(`${imageCount}개의 이미지를 ZIP으로 다운로드합니다!`);
    
  } catch (error) {
    hideLoading();
    alert(`다운로드 오류: ${error.message}`);
    console.error(error);
  }
});

// 5. 장면 편집
editBtn.addEventListener('click', () => {
  if (confirm('장면을 다시 분석하시겠습니까?')) {
    showStep(1);
  }
});

// 6. 새로 시작
restartBtn.addEventListener('click', () => {
  if (confirm('처음부터 다시 시작하시겠습니까? (생성된 이미지는 유지됩니다)')) {
    scriptInput.value = '';
    analyzedScenes = [];
    generatedImages = {};
    scenesPreview.innerHTML = '';
    generationStatus.innerHTML = '';
    downloadAllBtn.disabled = true;
    showStep(1);
  }
});

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
  showStep(1);
  downloadAllBtn.disabled = true;
  console.log('🎬 유튜브 이미지 생성기 준비 완료!');
  console.log('⚡ 병렬 비동기 처리 모드');
});
