import base64
import requests
import os

def extract_text_from_image(image_bytes: bytes, api_key: str = None) -> str:
    """
    Uses OpenAI's Vision API as an OCR to extract and describe text/financial data from screenshots.
    If no specific OCR key is provided, it falls back to OPENAI_API_KEY.
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise Exception("OpenAI API Key is required for image processing (OCR via Vision API)")

    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    payload = {
        "model": "gpt-4o-mini", # or gpt-4-vision-preview depending on account access
        "messages": [
            {
                "role": "system",
                "content": "You are a precise OCR tool. Extract all the text and numbers from the provided financial screenshot accurately. Do not invent any numbers."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all financial data and text from this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"OCR Error: {response.text}")
