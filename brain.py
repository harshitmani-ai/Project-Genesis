import time

from google import genai
from google.genai import types


PRIMARY_MODEL = "gemini-3.5-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10

client = genai.Client()


def generate_response(prompt, use_web=False):
    models_to_try = [
        PRIMARY_MODEL,
        FALLBACK_MODEL,
    ]

    last_error = None

    for model_name in models_to_try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(
                    f"Using {model_name} "
                    f"(attempt {attempt}/{MAX_RETRIES})..."
                )

                config = None

                if use_web:
                    config = types.GenerateContentConfig(
                        tools=[
                            types.Tool(
                                google_search=types.GoogleSearch()
                            )
                        ]
                    )

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return response.text

            except Exception as error:
                last_error = error
                error_code = getattr(error, "code", None)

                if error_code == 429:
                    print(
                        f"{model_name} quota is currently exhausted."
                    )
                    print("Switching to the fallback model...")
                    break

                if error_code == 503:
                    print(
                        f"{model_name} is temporarily unavailable."
                    )

                    if attempt < MAX_RETRIES:
                        print(
                            f"Retrying in "
                            f"{RETRY_DELAY_SECONDS} seconds..."
                        )
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue

                    print("Switching to the fallback model...")
                    break

                raise

    raise RuntimeError(
        "All available Gemini models are unavailable "
        "or have exhausted their quota. Try again later."
    ) from last_error


def ask_ai(prompt):
    return generate_response(
        prompt=prompt,
        use_web=False,
    )


def ask_ai_with_web(prompt):
    return generate_response(
        prompt=prompt,
        use_web=True,
    )