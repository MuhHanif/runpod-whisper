from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer


def create_http_server(port: int) -> None:
    """
    Creates a simple HTTP server.

    Args:
        port: The port number to run the server on.

    Returns:
        None
    """
    server_address = ("", port)
    httpd = TCPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()


def get_transcription(
    url: str, api_key: str, audio_url: str, model: str
) -> requests.Response:
    """
    Retrieve transcription using the RunPod API.

    Args:
        url (str): The API endpoint URL.
        api_key (str): The API key for authentication.
        audio_url (str): The URL of the audio file to transcribe.
        model (str): Whisper model options `tiny`, `base`, `small`, `medium`, `large`, `large-v2`.

    Returns:
        requests.Response: The response object containing the transcription result.
    """
    payload = {
        "input": {
            "audio": audio_url,
            "model": model,
            "transcription": "plain text",
            "translate": False,
            "temperature": 0,
            "best_of": 5,
            "beam_size": 5,
            "suppress_tokens": "-1",
            "condition_on_previous_text": False,
            "temperature_increment_on_fallback": 0.2,
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1,
            "no_speech_threshold": 0.6,
        }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": api_key,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response
