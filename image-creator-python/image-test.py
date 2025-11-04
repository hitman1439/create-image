from google import genai

client = genai.Client(api_key="")

# 방법 1: contents를 키워드 인수로 명시
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=""
)

# 생성된 이미지 저장
for part in response.candidates[0].content.parts:
    if part.inline_data:
        import base64
        image_data = part.inline_data.data
        with open("output.png", "wb") as f:
            f.write(image_data)
        print("이미지가 output.png로 저장되었습니다!")
