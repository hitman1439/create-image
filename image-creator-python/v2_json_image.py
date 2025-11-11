# app_gradio.py (수정 버전 - 16:9 비율 정확히 유지 + 조건부 배경)
import gradio as gr
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import json
import time
import zipfile
import os
import tempfile
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class NanoBananaGenerator:
    def __init__(self, api_key, config_dict):
        self.client = genai.Client(api_key=api_key)
        self.config = config_dict
        self.output_rules = self.config.get("OUTPUT_RULES", {})
        self.style = self.config.get("STYLE", {})
        self.negative_prompts = self.config.get("NEGATIVE_PROMPTS", [])
        self.character_bible = self.config.get("CHARACTER_BIBLE", {})
        self.scenes = self.config["RUN"]["SCENES"]
        
    def _parse_aspect_ratio(self):
        """16:9 고정"""
        return "16:9"
    
    def _parse_target_size(self):
        """1920x1080 고정 (유튜브 롱폼)"""
        return (1920, 1080)
    
    def _build_style_description(self):
        style_parts = []
        if self.style.get("photorealism"):
            style_parts.append("photorealistic")
        if self.style.get("cinematic"):
            style_parts.append("cinematic composition")
        if "color_grade" in self.style:
            style_parts.append(f"{self.style['color_grade']} color grading")
        if "depth_of_field" in self.style:
            style_parts.append(f"{self.style['depth_of_field']} depth of field")
        if "skin_texture" in self.style:
            style_parts.append(f"{self.style['skin_texture']} skin texture")
        if "film_grain" in self.style:
            style_parts.append(f"{self.style['film_grain']} film grain")
        return ", ".join(style_parts)
    
    def _is_illustration_or_diagram(self, description):
        """3D 일러스트, 다이어그램, 그래픽인지 판단"""
        keywords = [
            'illustration', 'diagram', '3d', 'icon', 'infographic', 
            'graphic', 'chart', 'visualization', 'concept',
            '일러스트', '다이어그램', '그래픽', '도표', '아이콘'
        ]
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in keywords)
    
    def _build_negative_prompt(self, is_illustration=False):
        """네거티브 프롬프트 생성 (장면 타입에 따라 다르게)"""
        avoid_items = []
        avoid_items.extend(self.negative_prompts)
        disallow = self.output_rules.get("disallow", [])
        avoid_items.extend(disallow)
        
        if is_illustration:
            # 일러스트/다이어그램: 배경 요소 제거
            avoid_items.extend([
                "busy background",
                "complex background",
                "architectural background",
                "landscape background",
                "Korean buildings",
                "traditional architecture",
                "street scene"
            ])
        else:
            # 실사 장면: 비한국적 요소 및 전통 요소 제거
            avoid_items.extend([
                "non-Korean people",
                "Western faces",
                "Caucasian",
                "African",
                "European setting",
                "American setting",
                "foreign country",
                "traditional hanbok",
                "traditional Korean clothing",
                "hanok",
                "traditional Korean architecture",
                "traditional Korean building",
                "historic Korea",
                "ancient Korea",
                "Joseon era"
            ])
        
        if avoid_items:
            return f"Avoid: {', '.join(avoid_items)}. "
        return ""
    
    def _build_camera_description(self, camera):
        camera_parts = []
        if "shot" in camera:
            camera_parts.append(camera["shot"])
        if "angle" in camera:
            camera_parts.append(camera["angle"])
        if "movement" in camera:
            camera_parts.append(camera["movement"])
        return ", ".join(camera_parts)
    
    def _create_prompt(self, scene):
        """프롬프트 생성 - 조건부 배경 적용"""
        prompt_parts = []
        
        # 기본 설명
        description = scene.get("DESCRIPTION", "")
        prompt_parts.append(description)
        
        # 캐릭터 추가
        characters = scene.get("CHARACTERS", [])
        if characters:
            for char in characters:
                char_info = self.character_bible.get(char, {})
                if char_info:
                    char_desc = f"{char}: {char_info.get('description', '')}"
                    prompt_parts.append(char_desc)
        
        # 🔧 장면 타입 판단
        is_illustration = self._is_illustration_or_diagram(description)
        
        if is_illustration:
            # 일러스트/다이어그램: 깔끔한 배경
            prompt_parts.append("\nBackground: Clean, minimal background with soft gradient or solid color")
            prompt_parts.append("Style: Professional 3D illustration or educational diagram with clear focus on subject")
        else:
            # 실사 장면: 현대 한국 배경
            prompt_parts.append("\nLocation: Present-day Korea (2020s), modern Korean setting")
            prompt_parts.append("Environment: Contemporary Korean architecture with modern buildings, city streets with Korean signage, modern Korean interior design")
            prompt_parts.append("People: Korean ethnicity with natural Korean features, wearing modern casual clothing (contemporary fashion, casual wear, everyday clothes)")
            prompt_parts.append("Time period: Modern era (2020s), contemporary lifestyle")
        
        # 스타일
        style_desc = self._build_style_description()
        if style_desc:
            prompt_parts.append(f"\nStyle: {style_desc}")
        
        # 카메라
        camera = scene.get("CAMERA", {})
        camera_desc = self._build_camera_description(camera)
        if camera_desc:
            prompt_parts.append(f"\nCamera: {camera_desc}")
        
        # 네거티브 프롬프트
        negative = self._build_negative_prompt(is_illustration)
        if negative:
            prompt_parts.append(f"\n{negative}")
        
        # 마무리
        prompt_parts.append("\nCreate a single cohesive scene with realistic details.")
        
        if not is_illustration:
            prompt_parts.append("Ensure Korean ethnicity for all people in modern casual clothing and contemporary Korean setting (2020s).")
        
        return "\n".join(prompt_parts)
    
    def _crop_to_aspect_ratio(self, image, target_ratio=(16, 9)):
        """이미지를 왜곡 없이 16:9 비율로 중앙 크롭"""
        img_width, img_height = image.size
        img_ratio = img_width / img_height
        target_ratio_value = target_ratio[0] / target_ratio[1]
        
        if abs(img_ratio - target_ratio_value) < 0.01:
            # 이미 비율이 맞으면 그대로 반환
            return image
        
        if img_ratio > target_ratio_value:
            # 이미지가 더 가로로 넓음 -> 좌우 크롭
            new_width = int(img_height * target_ratio_value)
            left = (img_width - new_width) // 2
            return image.crop((left, 0, left + new_width, img_height))
        else:
            # 이미지가 더 세로로 길음 -> 상하 크롭
            new_height = int(img_width / target_ratio_value)
            top = (img_height - new_height) // 2
            return image.crop((0, top, img_width, top + new_height))
    
    def generate_scene(self, scene, scene_index, temp_dir, max_retries=3):
        """단일 장면 생성 (재시도 로직 포함) - PNG 파일로 저장 with Gemini Image"""
        import base64
        import re
        
        target_size = self._parse_target_size()
        
        prompt = self._create_prompt(scene)
        
        # 16:9 비율 강조 및 현대적 설정 강조
        prompt = f"16:9 aspect ratio, widescreen format, modern contemporary setting. {prompt}"
        
        for attempt in range(max_retries):
            try:
                # ✅ Gemini 2.5 Flash Image API 호출
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=prompt
                )
                
                # ✅ Gemini 응답 처리
                if not response.candidates:
                    return {
                        'success': False,
                        'scene_index': scene_index,
                        'error': "No response from API",
                        'scene': scene
                    }
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # inline_data.data 타입 확인 및 처리
                        image_data_raw = part.inline_data.data
                        
                        # 타입에 따라 처리
                        if isinstance(image_data_raw, str):
                            image_data = base64.b64decode(image_data_raw)
                        elif isinstance(image_data_raw, bytes):
                            image_data = image_data_raw
                        else:
                            image_data = bytes(image_data_raw)
                        
                        # BytesIO로 이미지 로드
                        image = Image.open(BytesIO(image_data))
                        
                        # 🔧 16:9 비율로 중앙 크롭 (왜곡 없음)
                        image = self._crop_to_aspect_ratio(image, target_ratio=(16, 9))
                        
                        # RGB 모드 변환 (PNG 호환성)
                        if image.mode == 'RGBA':
                            # RGBA를 RGB로 변환 (흰 배경)
                            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                            rgb_image.paste(image, mask=image.split()[3])
                            image = rgb_image
                        elif image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        # 🔧 1920x1080으로 리사이즈 (이미 16:9이므로 왜곡 없음)
                        if image.size != target_size:
                            image = image.resize(target_size, Image.LANCZOS)
                        
                        # PNG 파일로 저장
                        scene_num_raw = scene.get("SCENE_NUMBER", scene_index + 1)
                        scene_num = int(scene_num_raw) if isinstance(scene_num_raw, (str, int)) else scene_index + 1
                        title = scene.get("TITLE", f"Scene_{scene_index+1}")
                        safe_title = title.replace(' ', '_').replace('/', '_')
                        filename = f"scene_{scene_num:02d}_{safe_title}.png"
                        filepath = os.path.join(temp_dir, filename)
                        
                        # PNG로 저장 (압축 최적화)
                        image.save(filepath, format='PNG', optimize=True)
                        
                        return {
                            'success': True,
                            'scene_index': scene_index,
                            'filepath': filepath,
                            'prompt': prompt,
                            'scene': scene
                        }
                
                return {
                    'success': False,
                    'scene_index': scene_index,
                    'error': "No image data in response",
                    'scene': scene
                }
                    
            except Exception as e:
                error_str = str(e)
                
                # Rate limit 처리
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    wait_match = re.search(r'retry in (\d+(?:\.\d+)?)', error_str)
                    if wait_match:
                        wait_time = float(wait_match.group(1))
                    else:
                        wait_time = 60
                    
                    if attempt < max_retries - 1:
                        print(f"⏳ Scene {scene_index + 1} rate limit hit. Waiting {wait_time:.0f} seconds...")
                        time.sleep(wait_time + 1)
                        continue
                    else:
                        return {
                            'success': False,
                            'scene_index': scene_index,
                            'error': f"Rate limit exceeded. Wait {wait_time:.0f}s",
                            'scene': scene
                        }
                
                # 기타 에러
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Scene {scene_index + 1} failed (attempt {attempt + 1}/{max_retries}): {error_str}")
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        'success': False,
                        'scene_index': scene_index,
                        'error': error_str,
                        'scene': scene
                    }
        
        return {
            'success': False,
            'scene_index': scene_index,
            'error': "Max retries exceeded",
            'scene': scene
        }


def create_zip_file(filepaths_dict, scenes):
    """PNG 파일들을 ZIP으로 압축"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"nano_banana_scenes_{timestamp}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # scene_index 순서대로 정렬
        sorted_indices = sorted(filepaths_dict.keys())
        
        for idx in sorted_indices:
            filepath = filepaths_dict[idx]
            # 파일명만 추출
            filename = os.path.basename(filepath)
            # ZIP에 추가
            zipf.write(filepath, filename)
    
    return zip_path


def generate_all_images(api_key, json_text, retry_on_limit, max_workers, progress=gr.Progress()):
    """모든 장면을 병렬로 생성 (실시간 업데이트)"""
    
    if not api_key:
        yield [], "❌ Please enter your API key", None
        return
    
    try:
        config_dict = json.loads(json_text)
    except json.JSONDecodeError as e:
        yield [], f"❌ Invalid JSON: {e}", None
        return
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix="nano_banana_")
    
    try:
        generator = NanoBananaGenerator(api_key, config_dict)
        scenes = config_dict['RUN']['SCENES']
        total_scenes = len(scenes)
        
        # 결과 저장용
        filepaths_dict = {}  # {scene_index: filepath}
        gallery_data = [None] * total_scenes  # 순서 유지용
        logs = [f"⏳ Waiting..." for _ in range(total_scenes)]
        
        max_retries = 3 if retry_on_limit else 1
        completed = 0
        lock = threading.Lock()
        
        # 초기 상태 yield
        initial_log = f"🚀 Starting parallel generation of {total_scenes} scenes with {max_workers} workers...\n\n"
        initial_log += "\n".join([f"Scene {i+1}: ⏳ Queued" for i in range(total_scenes)])
        yield [], initial_log, None
        
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 작업 제출
            future_to_index = {
                executor.submit(generator.generate_scene, scene, i, temp_dir, max_retries): i 
                for i, scene in enumerate(scenes)
            }
            
            # 완료되는 대로 처리
            for future in as_completed(future_to_index):
                result = future.result()
                scene_idx = result['scene_index']
                scene = result['scene']
                
                with lock:
                    completed += 1
                    
                    if result['success']:
                        filepath = result['filepath']
                        filepaths_dict[scene_idx] = filepath
                        
                        # Gallery 데이터 업데이트 (파일 경로 사용)
                        gallery_data[scene_idx] = filepath
                        
                        logs[scene_idx] = f"✅ Scene {scene_idx + 1}: {scene.get('TITLE', 'Untitled')}"
                    else:
                        logs[scene_idx] = f"❌ Scene {scene_idx + 1}: {result['error']}"
                    
                    # 로그 생성
                    log_text = f"🎬 Progress: {completed}/{total_scenes} scenes completed\n\n"
                    log_text += "\n".join(logs)
                    log_text += f"\n\n🇰🇷 Modern Korean people (2020s) | Contemporary clothing & settings | Clean background for illustrations | 16:9 Format | PNG"
                    
                    # None이 아닌 파일 경로만 필터링
                    current_gallery = [fp for fp in gallery_data if fp is not None]
                    
                    # 실시간 업데이트
                    progress(completed / total_scenes, desc=f"Completed: {completed}/{total_scenes}")
                    yield current_gallery, log_text, None
        
        # 최종 로그
        final_log = f"🎉 Generation complete! {len(filepaths_dict)}/{total_scenes} scenes generated.\n\n"
        final_log += "\n".join(logs)
        final_log += f"\n\n🇰🇷 Modern Korean people (2020s) | Contemporary clothing & settings | Clean background for illustrations | 16:9 Format | PNG"
        
        # ZIP 파일 생성
        zip_path = None
        if len(filepaths_dict) > 0:
            try:
                zip_path = create_zip_file(filepaths_dict, scenes)
                final_log += f"\n\n📦 ZIP file ready! Click the download button below."
                final_log += f"\n   File: {os.path.basename(zip_path)}"
                final_log += f"\n   Contains: {len(filepaths_dict)} PNG images"
            except Exception as e:
                final_log += f"\n\n⚠️ Failed to create ZIP file: {e}"
        
        if len(filepaths_dict) < total_scenes:
            final_log += "\n\n⚠️ Some scenes failed. Check billing settings."
        
        # 최종 Gallery 데이터 (None 제거)
        final_gallery = [fp for fp in gallery_data if fp is not None]
        
        yield final_gallery, final_log, zip_path
            
    except Exception as e:
        yield [], f"❌ Error: {e}", None
    finally:
        # 임시 디렉토리는 cleanup에서 처리하지 않음 (다운로드 위해 유지)
        pass


def generate_single_image(api_key, json_text, scene_index, retry_on_limit, progress=gr.Progress()):
    """단일 장면 생성"""
    
    if not api_key:
        return [], "❌ Please enter your API key", None
    
    try:
        config_dict = json.loads(json_text)
    except json.JSONDecodeError as e:
        return [], f"❌ Invalid JSON: {e}", None
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix="nano_banana_")
    
    try:
        generator = NanoBananaGenerator(api_key, config_dict)
        scenes = config_dict['RUN']['SCENES']
        
        scene_idx = int(scene_index)
        max_retries = 3 if retry_on_limit else 1
        
        if 0 <= scene_idx < len(scenes):
            progress(0.5, desc=f"Generating scene {scene_idx + 1}...")
            scene = scenes[scene_idx]
            result = generator.generate_scene(scene, scene_idx, temp_dir, max_retries=max_retries)
            progress(1.0, desc="Complete!")
            
            if result['success']:
                filepath = result['filepath']
                
                # ZIP 파일 생성
                filepaths_dict = {scene_idx: filepath}
                zip_path = create_zip_file(filepaths_dict, [scene])
                
                return [filepath], \
                       f"✅ Scene {scene_idx + 1} generated successfully!\n\n🇰🇷 Modern Korea (2020s) | 16:9 Format | PNG\n\nFile: {os.path.basename(filepath)}\n\nPrompt:\n{result['prompt']}", \
                       zip_path
            else:
                error_msg = f"❌ Failed to generate scene {scene_idx + 1}\n\nError: {result['error']}"
                if "Rate limit" in result['error'] or "quota" in result['error'].lower():
                    error_msg += "\n\n💡 Solutions:\n"
                    error_msg += "1. Enable billing in Google Cloud Console\n"
                    error_msg += "2. Wait for quota reset\n"
                    error_msg += "3. Enable 'Auto-retry on rate limit'"
                return [], error_msg, None
        else:
            return [], f"❌ Invalid scene index: {scene_idx}", None
            
    except Exception as e:
        return [], f"❌ Error: {e}", None


# Gradio Interface
with gr.Blocks(title="Nano Banana Generator 🇰🇷 (Modern Korea)", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🌟 Nano Banana Image Generator 🇰🇷 (Modern Korea Edition)
    Generate cinematic images from JSON scene descriptions using **Gemini 2.5 Flash Image**
    
    **✅ 실사 장면: 현대 한국인 & 현대 의상 & 현대 배경 | 일러스트: 깔끔한 배경 | 16:9 비율 | PNG 형식**
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            api_key_input = gr.Textbox(
                label="API Key",
                placeholder="Enter your Gemini API key",
                type="password"
            )
            
            with gr.Row():
                retry_checkbox = gr.Checkbox(
                    label="Auto-retry on rate limit",
                    value=True,
                    info="자동 재시도"
                )
                
                max_workers_slider = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=3,
                    step=1,
                    label="Parallel Workers",
                    info="병렬 작업 수 (높을수록 빠름)"
                )
            
            gr.Markdown("""
            ### 📝 JSON Configuration
            JSON에 장면 설명을 입력하세요.
            
            **자동 배경 처리:**
            - 🎨 "illustration", "3D", "diagram" → 깔끔한 배경
            - 👤 일반 장면 → 현대 한국 배경 (2020s)
            
            **모든 실사는 현대적 의상과 배경으로 생성됩니다.**
            """)
            json_input = gr.Code(
                label="Scene Configuration",
                language="json",
                lines=18,
                value="""{
  "OUTPUT_RULES": {
    "aspect_ratio": "16:9",
    "size": "1920x1080",
    "disallow": ["collage", "grid", "text"]
  },
  "STYLE": {
    "photorealism": true,
    "cinematic": true,
    "color_grade": "natural warm"
  },
  "NEGATIVE_PROMPTS": ["cartoon", "anime"],
  "CHARACTER_BIBLE": {},
  "RUN": {
    "SCENES": [
      {
        "SCENE_NUMBER": 1,
        "TITLE": "병원_진료실",
        "DESCRIPTION": "현대적인 병원 진료실",
        "CHARACTERS": [],
        "CAMERA": {"shot": "medium shot"}
      },
      {
        "SCENE_NUMBER": 2,
        "TITLE": "혈관_일러스트",
        "DESCRIPTION": "A soft 3D educational illustration of healthy blood vessels",
        "CHARACTERS": [],
        "CAMERA": {"shot": "close up"}
      }
    ]
  }
}"""
            )
            
        with gr.Column(scale=1):
            gr.Markdown("### 🎬 Generation")
            
            with gr.Tabs():
                with gr.Tab("Generate All (Parallel)"):
                    generate_all_btn = gr.Button("🚀 Generate All Scenes", variant="primary", size="lg")
                    
                with gr.Tab("Generate Single"):
                    scene_selector = gr.Number(
                        label="Scene Index (0-based)",
                        value=0,
                        precision=0,
                        minimum=0
                    )
                    generate_single_btn = gr.Button("Generate Scene", size="lg")
            
            gr.Markdown("### 📸 Generated Images (PNG, 16:9)")
            output_gallery = gr.Gallery(
                label="Output",
                show_label=False,
                elem_id="gallery",
                columns=2,
                rows=2,
                height="auto",
                object_fit="contain",
                type="filepath"
            )
            
            gr.Markdown("### 📦 Download All (ZIP)")
            download_zip_btn = gr.File(
                label="Click to download ZIP file",
                visible=True,
                interactive=False
            )
            
            gr.Markdown("### 📋 Generation Log")
            output_log = gr.Textbox(
                label="Log",
                lines=8,
                show_label=False
            )
    
    # Event handlers
    generate_all_btn.click(
        fn=generate_all_images,
        inputs=[api_key_input, json_input, retry_checkbox, max_workers_slider],
        outputs=[output_gallery, output_log, download_zip_btn]
    )
    
    generate_single_btn.click(
        fn=generate_single_image,
        inputs=[api_key_input, json_input, scene_selector, retry_checkbox],
        outputs=[output_gallery, output_log, download_zip_btn]
    )
    
    gr.Markdown("""
    ---
    ### 💡 사용 방법
    
    **개별 다운로드 (PNG):**
    1. Gallery에서 이미지 클릭
    2. 우클릭 → "다른 이름으로 저장"
    3. **확장자 확인: .png로 저장됨**
    
    **일괄 다운로드 (ZIP):**
    1. 이미지 생성 완료 후
    2. "Download All (ZIP)" 섹션의 파일 클릭
    3. ZIP 파일 다운로드 (모든 이미지 PNG 포함)
    
    ### ⚡ 특징
    - **16:9 비율**: 왜곡 없이 정확한 유튜브 롱폼 비율
    - **조건부 배경**: 일러스트는 깔끔한 배경, 실사는 현대 한국 배경
    - **현대적 설정**: 모든 실사는 2020년대 현대 한국 (현대 의상, 현대 배경)
    - **PNG 형식**: 모든 이미지가 PNG로 저장 (무손실)
    - **병렬 처리**: 여러 이미지 동시 생성
    - **실시간 표시**: 완료 즉시 Gallery 업데이트
    
    ### 🎨 자동 배경 선택
    - **3D 일러스트/다이어그램**: "illustration", "3D", "diagram" 감지 → 깔끔한 단색 배경
    - **실사 장면**: 사람, 거리, 인테리어 등 → 현대 한국 배경 (2020s, 현대 의상, 현대 건축)
    
    ### 🚫 자동 제외 요소
    - 전통 한복, 전통 한국 건축, 한옥, 조선시대 등 전통 요소 자동 제외
    - 모든 인물은 현대적 캐주얼 의상 착용
    
    ### 📊 Gemini 2.5 Flash Image
    - ✅ 빠른 생성 속도
    - ✅ 자연스러운 이미지
    - 💰 비용: $0.04/이미지
    """)

if __name__ == "__main__":
    demo.launch(share=True)