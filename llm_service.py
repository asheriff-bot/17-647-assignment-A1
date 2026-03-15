import requests
from config import Config


def _placeholder_summary(title, author='', description=''):
    return f"Summary for '{title}' by {author}. {description}".strip()


def _extract_summary_from_response(response_json):
    if not isinstance(response_json, dict):
        return None

    output_text = response_json.get('output_text')
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = response_json.get('output')
    if isinstance(output, list):
        for element in output:
            if isinstance(element, dict):
                content = element.get('content')
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    joined = ''.join(str(item) for item in content if isinstance(item, str))
                    if joined.strip():
                        return joined.strip()

    choices = response_json.get('choices') or []
    if isinstance(choices, list):
        for choice in choices:
            if isinstance(choice, dict):
                text = choice.get('text') or choice.get('content')
                if isinstance(text, str) and text.strip():
                    return text.strip()

    return None


def _request_llm(prompt, max_output_tokens=1024, temperature=0.7):
    if not Config.LLM_API_KEY:
        return None

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.LLM_API_KEY}'
        }
        payload = {
            'model': Config.LLM_MODEL,
            'input': prompt,
            'max_output_tokens': max_output_tokens,
            'temperature': temperature,
        }
        response = requests.post(Config.LLM_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return _extract_summary_from_response(response.json())
    except Exception:
        return None


def generate_book_summary(title, author, description):
    prompt = (
        f"Please provide a 500-word summary for the following book:\n"
        f"Title: {title}\n"
        f"Author: {author}\n"
        f"Description: {description}\n\n"
        "Generate a detailed, engaging summary of approximately 500 words."
    )
    summary = _request_llm(prompt, max_output_tokens=1024, temperature=0.7)
    return summary or _placeholder_summary(title, author, description)


def generate_quote_for_book(title, isbn):
    prompt = (
        f"Generate a 500-character summary for a book with the following details:\n"
        f"Title: {title}\n"
        f"ISBN: {isbn}\n\n"
        "Keep the summary concise, engaging, and book-related."
    )

    quote = _request_llm(prompt, max_output_tokens=512, temperature=0.7)
    if quote:
        return quote
    return f"{title} (ISBN {isbn}) is a compelling read worth investigating."
