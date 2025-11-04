# app_gradio.py (PNG 강제 + ZIP 다운로드 수정)
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
        ratio = self.output_rules.get("aspect_ratio", "16:9")
        return str(ratio)
    
    def _parse_target_size(self):
        size = self.output_rules.get("size", "1920x1080")
        if isinstance(size, str) and 'x' in size:
            width, height = map(int, size.split('x'))
            return (width, height)
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
    
    def _build_negative_prompt(self):
        avoid_items = []
        avoid_items.extend(self.negative_prompts)
        disallow = self.output_rules.get("disallow", [])
        avoid_items.extend(disallow)
        
        avoid_items.extend([
            "non-Korean people",
            "Western faces",
            "Caucasian",
            "African",
            "European setting",
            "American setting",
            "foreign country"
        ])
        
        if avoid_items:
            return f"Avoid: {', '.join(avoid_items)}. "
        return ""
    
    def _build_character_description(self, character_names):
        descriptions = []
        
        for char_name in character_names:
            if char_name in self.character_bible:
                char = self.character_bible[char_name]
                desc = f"Korean person, {char.get('age', 'adult')}"
                
                if 'appearance' in char:
                    desc += f", {char['appearance']}"
                if 'clothing' in char:
                    desc += f", wearing {char['clothing']}"
                
                descriptions.append(desc)
            else:
                descriptions.append(f"Korean person")
        
        return "; ".join(descriptions) if descriptions else "Korean people"
    
    def _build_camera_description(self, camera_info):
        parts = []
        if "shot" in camera_info:
            parts.append(camera_info["shot"])
        if "lens" in camera_info:
            parts.append(f"{camera_info['lens']} lens")
        if "angle" in camera_info:
            parts.append(camera_info["angle"])
        if "lighting" in camera_info:
            parts.append(camera_info["lighting"])
        return ", ".join(parts) if parts else ""
    
    def _add_korean_context(self, description):
        if "Korea" in description or "Korean" in description or "korea" in description or "korean" in description:
            return description
        return f"{description} Set in Korea with Korean architecture and environment."
    
    def _create_prompt(self, scene):
        prompt_parts = []
        prompt_parts.append("IMPORTANT: All people must be Korean with East Asian facial features. Setting must be in Korea.")
        
        main_description = scene.get("DESCRIPTION", "")
        main_description = self._add_korean_context(main_description)
        prompt_parts.append(f"\n{main_description}")
        
        characters = scene.get("CHARACTERS", [])
        if characters or "환자" in main_description or "의사" in main_description or "사람" in main_description:
            char_desc = self._build_character_description(characters)
            prompt_parts.append(f"\nCharacters: {char_desc}")
        else:
            prompt_parts.append("\nIf any people appear: They must be Korean with East Asian features.")
        
        prompt_parts.append("\nLocation: Korea (South Korea)")
        prompt_parts.append("Environment: Korean setting with authentic Korean architectural elements, Korean street signs, Korean interior design")
        
        style_desc = self._build_style_description()
        if style_desc:
            prompt_parts.append(f"\nStyle: {style_desc}")
        
        camera = scene.get("CAMERA", {})
        camera_desc = self._build_camera_description(camera)
        if camera_desc:
            prompt_parts.append(f"\nCamera: {camera_desc}")
        
        negative = self._build_negative_prompt()
        if negative:
            prompt_parts.append(f"\n{negative}")
        
        prompt_parts.append("\nCreate a single cohesive scene with realistic details.")
        prompt_parts.append("Ensure Korean ethnicity for all people and Korean setting for all locations.")
        
        return "\n".join(prompt_parts)
    
    def generate_scene(self, scene, scene_index, temp_dir, max_retries=3):
        """단일 장면 생성 (재시도 로직 포함) - PNG 파일로 저장"""
        aspect_ratio = self._parse_aspect_ratio()
        target_size = self._parse_target_size()
        
        prompt = self._create_prompt(scene)
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio=aspect_ratio
                        )
                    )
                )
                
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        image = Image.open(BytesIO(part.inline_data.data))
                        
                        # RGB 모드 변환 (PNG 호환성)
                        if image.mode == 'RGBA':
                            pass
                        elif image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        if image.size != target_size:
                            image = image.resize(target_size, Image.LANCZOS)
                        
                        # PNG 파일로 저장
                        scene_num = scene.get("SCENE_NUMBER", scene_index + 1)
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
                
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    import re
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
                
                return {
                    'success': False,
                    'scene_index': scene_index,
                    'error': str(e),
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
                    log_text += f"\n\n🇰🇷 All images: Korean people & settings | Format: PNG"
                    
                    # None이 아닌 파일 경로만 필터링
                    current_gallery = [fp for fp in gallery_data if fp is not None]
                    
                    # 실시간 업데이트
                    progress(completed / total_scenes, desc=f"Completed: {completed}/{total_scenes}")
                    yield current_gallery, log_text, None
        
        # 최종 로그
        final_log = f"🎉 Generation complete! {len(filepaths_dict)}/{total_scenes} scenes generated.\n\n"
        final_log += "\n".join(logs)
        final_log += f"\n\n🇰🇷 All images: Korean people & settings | Format: PNG"
        
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
                       f"✅ Scene {scene_idx + 1} generated successfully!\n\n🇰🇷 Korean people & setting | Format: PNG\n\nFile: {os.path.basename(filepath)}\n\nPrompt:\n{result['prompt']}", \
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
with gr.Blocks(title="Nano Banana Generator 🇰🇷", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🍌 Nano Banana Image Generator 🇰🇷
    Generate cinematic images from JSON scene descriptions using Google's Gemini 2.5 Flash Image
    
    **✅ 모든 이미지: 한국인 & 한국 배경 | PNG 형식**
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
        "TITLE": "서울_거리",
        "DESCRIPTION": "붐비는 서울 명동 거리",
        "CHARACTERS": [],
        "CAMERA": {"shot": "wide shot"}
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
            
            gr.Markdown("### 📸 Generated Images (PNG)")
            output_gallery = gr.Gallery(
                label="Output",
                show_label=False,
                elem_id="gallery",
                columns=2,
                rows=2,
                height="auto",
                object_fit="contain",
                type="filepath"  # 파일 경로로 표시
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
    - **PNG 형식**: 모든 이미지가 PNG로 저장 (무손실)
    - **병렬 처리**: 여러 이미지 동시 생성
    - **실시간 표시**: 완료 즉시 Gallery 업데이트
    - **한국 컨텍스트**: 자동 적용
    
    ### 🇰🇷 자동 적용
    - 등장인물: 한국인
    - 배경: 한국
    - 형식: PNG
    """)

if __name__ == "__main__":
    demo.launch(share=True)