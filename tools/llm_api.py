import os
import requests
import time
import random
import json
from dotenv import load_dotenv
import threading

load_dotenv()

MODEL_ID = os.getenv("MODEL_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Headers for OpenRouter
openrouter_headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

# Simple in-memory cache for LLM responses
llm_cache = {}

def call_llm_api(
    role: str,
    user_prompt: str,
    provider: str = "openrouter",
    max_tokens: int = 700,
    max_retries: int = 3,
    throttle_seconds: int = 10
) -> str:
    """
    Call LLM API (OpenRouter) with retry mechanism and in-memory caching.
    """
    cache_key = (role, user_prompt, provider, max_tokens)
    if cache_key in llm_cache:
        return llm_cache[cache_key]
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens
    }

    if provider == "openrouter":
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = openrouter_headers
    else:
        return f"❌ Unsupported provider: {provider}"

    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'choices' in data and data['choices']:
                        result = data['choices'][0]['message']['content']
                        llm_cache[cache_key] = result
                        return result
                    else:
                        print(f"❌ Unexpected response structure: {data}")
                        result = f"❌ Unexpected response structure: {data}"
                        llm_cache[cache_key] = result
                        return result
                except Exception as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Raw response: {response.text}")
                    result = f"❌ Failed to parse JSON: {e} | Raw: {response.text}"
                    llm_cache[cache_key] = result
                    return result
            else:
                print(f"❌ API call failed with status {response.status_code}")
                print(f"Raw response: {response.text}")
            
            # Check for rate limit error
            if response.status_code == 429:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "")
                    
                    # Check for non-retryable daily limit error
                    if "rate limit" in error_message.lower():
                        return (
                            "❌ **Daily API Limit Reached** ❌\n\n"
                            "You are using the shared free-tier API key, which has a daily usage limit.\n\n"
                            "**To fix this, please:**\n"
                            "1. Get your own free API key from [openrouter.ai](https://openrouter.ai/keys)\n"
                            "2. Add it to the `.env` file in your project as `OPENROUTER_API_KEY=your_key_here`"
                        )
                except (json.JSONDecodeError, AttributeError):
                    # If parsing fails, proceed with generic retry logic
                    pass

                # For other (potentially temporary) rate limits, retry
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"⚠️ Rate limit hit. Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
                else:
                    # After all retries, return the raw error
                    return f"❌ {provider.capitalize()} error: {response.status_code} - {response.text}"
                    
            return f"❌ {provider.capitalize()} error: {response.status_code} - {response.text}"
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Request failed. Retrying in {wait_time:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return f"❌ Request failed after {max_retries} attempts: {str(e)}"
    return f"❌ Max retries ({max_retries}) exceeded"

def call_llm_api_json(
    role: str,
    user_prompt: str,
    provider: str = "openrouter",
    max_tokens: int = 400,  # Lowered default max_tokens for efficiency
    max_retries: int = 3
) -> dict:
    """
    Call LLM API with JSON response expectation for structured data.
    Tries to robustly extract and parse the first valid JSON array or object from the response.
    """
    # Enhance the prompt to ensure JSON response
    enhanced_prompt = f"{user_prompt}\n\nIMPORTANT: Respond with valid JSON only. Do not include any text before or after the JSON object or array."

    # Get raw response
    response_text = call_llm_api(role, enhanced_prompt, provider, max_tokens, max_retries)

    # If the response is an error string, return it as an error dict
    if response_text.startswith("❌") or response_text.startswith("⚠️"):
        return {
            "error": "LLM API call failed",
            "raw_response": response_text
        }

    # Try to parse JSON robustly
    try:
        response_text = response_text.strip()
        
        # Find the start of the first JSON object '{' or array '['
        json_start = -1
        first_brace = response_text.find('{')
        first_bracket = response_text.find('[')

        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            json_start = first_brace
        elif first_bracket != -1:
            json_start = first_bracket
        
        # If a start is found, find the corresponding end
        if json_start != -1:
            start_char = response_text[json_start]
            end_char = '}' if start_char == '{' else ']'
            json_end = response_text.rfind(end_char) + 1
            json_str = response_text[json_start:json_end]
        else:
            # If no JSON object/array found, it might be a JSON-encoded string
            json_str = response_text

        parsed_json = json.loads(json_str)

        # After parsing, we MUST have a dictionary or a list.
        if isinstance(parsed_json, (dict, list)):
            return parsed_json
        
        # If we get here, the LLM returned valid JSON, but not the right type (e.g., a string).
        return {
            "error": "Invalid JSON type",
            "raw_response": str(parsed_json),
            "parsing_error": "LLM did not return a JSON object or array as requested."
        }

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Response text: {response_text}")
        return {
            "error": "JSON parsing failed",
            "raw_response": response_text,
            "parsing_error": str(e)
        }
    except Exception as e:
        print(f"❌ Unexpected error in JSON parsing: {e}")
        return {
            "error": "Unexpected parsing error",
            "raw_response": response_text,
            "error_details": str(e)
        }