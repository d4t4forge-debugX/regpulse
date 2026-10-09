"""
pipeline/gemini_client.py

One Gemini client and one retry wrapper, shared by the judge (retrieval_agent)
and the memo writer (impact_agent).
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from config import GEMINI_MODEL

load_dotenv()
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# HTTP status codes worth waiting out, with the base wait in seconds:
# 503 = the model is overloaded right now, 429 = we hit a rate limit
RETRYABLE_WAIT_SECONDS = {503: 15, 429: 60}


def call_gemini_with_retry(prompt, model=GEMINI_MODEL, temperature=0, max_retries=4):
    """Call Gemini, waiting and retrying on 503 (overloaded) and 429 (rate limited)."""
    for attempt in range(max_retries):
        try:
            return _client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
        except errors.APIError as e:
            base_wait = RETRYABLE_WAIT_SECONDS.get(e.code)
            if base_wait is None or attempt == max_retries - 1:
                raise
            wait = base_wait * (attempt + 1)
            print(f"  Gemini {e.code}, retrying in {wait}s (attempt {attempt + 1} of {max_retries})...")
            time.sleep(wait)