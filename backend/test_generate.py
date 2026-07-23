import os
import sys
import logging
import traceback
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_generate")

from app.core.config import settings

try:
    import google.genai as genai
    from google.genai import types
    sdk_version = getattr(genai, "__version__", "unknown")
except Exception as e:
    logger.error("Failed to import google-genai: %s", e)
    sys.exit(1)

def test_generate():
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    model = settings.GEMINI_MODEL or os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    api_key_present = bool(api_key)
    request_type = "generate_content (non-streaming)"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    logger.info("==================================================")
    logger.info("GEMINI DIAGNOSTIC TEST: generate_content")
    logger.info("Configured Model : %s", model)
    logger.info("API Key Present  : %s", api_key_present)
    logger.info("SDK Version      : %s", sdk_version)
    logger.info("Request Type     : %s", request_type)
    logger.info("Target Endpoint  : %s", endpoint)
    logger.info("==================================================")

    if not api_key:
        logger.error("GEMINI_API_KEY is not configured!")
        return

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        temperature=settings.GEMINI_TEMPERATURE,
        top_p=settings.GEMINI_TOP_P,
        top_k=settings.GEMINI_TOP_K,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    )

    prompt = "Write a 1-sentence confirmation that Gemini generate_content is working."

    try:
        logger.info("Executing client.models.generate_content(model='%s')...", model)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        logger.info("Response Status  : SUCCESS 200 OK")
        logger.info("Response Text    : %s", response.text)
        logger.info("Response Details : %s", response)
    except Exception as exc:
        logger.error("Response Status  : FAILED")
        logger.error("Exception Type   : %s", type(exc).__name__)
        logger.error("Exception Message: %s", str(exc))
        logger.error("Full Traceback   :\n%s", traceback.format_exc())

if __name__ == "__main__":
    test_generate()
