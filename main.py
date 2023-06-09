from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import shutil
import requests
import json
from urllib.parse import urljoin
import time


# TODO! move this to module instead
def create_http_server(path: str = "", port: int = 8000, config: str = "") -> None:
    """
    Creates a simple HTTP server on the specified path and port.

    Args:
        path (str, optional): The directory from which to serve files. Defaults to the current working directory.
        port (int, optional): The port number to run the server on. Defaults to 8000.
        config (str, optional): The config JSON file path to change working directory,
            expect `simple_http_server_dir` variable inside the JSON.
    Returns:
        None
    """

    server_address = ("", port)
    httpd = TCPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server running on port {port}")
    try:
        # Change the current working directory to serve files from the specified path
        if config:
            # reads config file
            with open(config, "r") as json_config:
                # Load the JSON data into a dictionary
                config_data = json.load(json_config)
            # changes working dir according to config file
            os.chdir(config_data["simple_http_server_dir"])
        elif path:
            os.chdir(path)

        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


# TODO! move this to module instead
def get_transcription(
    api_key: str, audio_url: str, model: str = "base"
) -> requests.Response:
    """
    Retrieve transcription using the RunPod API.

    Args:
        api_key (str): The API key for authentication.
        audio_url (str): The URL of the audio file to transcribe.
        model (str, optional): Whisper model options
            `tiny`, `base`, `small`, `medium`, `large`, `large-v2` Defaults to `base`.

    Returns:
        requests.Response: The response object containing the transcription result.
    """
    output = None

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

    queue_headers = {"accept": "application/json", "authorization": api_key}

    # run whisper api url endpoint
    run_url = "https://api.runpod.ai/v2/faster-whisper/run"
    check_job_url = "https://api.runpod.ai/v2/faster-whisper/status/"

    # push transcription to api endpoint
    response = requests.post(run_url, json=payload, headers=headers)

    # if request successful periodically check the queue
    response.raise_for_status()

    # gets queue id from json response
    queue_id = response.json()["id"]

    # append job id
    check_job_url = urljoin(check_job_url, queue_id)

    # periodically check if the job is completed
    while True:
        # put sleep at top so i dont forget about it
        time.sleep(1)

        queue_headers = {"accept": "application/json", "authorization": api_key}

        # retrieve transcription status from api endpoint
        queue_response = requests.get(check_job_url, headers=queue_headers)

        # raise any request error
        queue_response.raise_for_status()

        # convert queue_response to dict
        queue_response = queue_response.json()

        # gets queue status from json response
        status = queue_response["status"]

        if status == "COMPLETED":
            output = queue_response["output"]
            break

        print(status)

    return output


def move_file_to_folder(
    file_path: str, folder_path: str = "/temp/runpod_file_queue"
) -> str:
    """
    Moves a file to a specified folder and returns the new file path.

    Args:
        file_path (str): The path of the file to be moved.
        folder_path (str, optional): The path of the destination folder.
            Defaults to `/temp/runpod_file_queue`.


    Returns:
        str: The new file path after moving the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    # Extract the file name from the file path
    file_name = os.path.basename(file_path)

    # Create the destination folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Construct the new file path in the destination folder
    new_file_path = os.path.join(folder_path, file_name)

    # Move the file to the destination folder
    shutil.move(file_path, new_file_path)

    # Return the new file path
    return new_file_path


def convert_local_path_to_url(file_path: str, config: str) -> str:
    """
    this is dummy function relies on simplehttpserver to serve the file to runpod api
    please change this function with proper s3 bucket

    Args:
        file_path (str): The path of the file to be replaced with public url.
        config (str): json path to some credentials settings.

    Returns:
        str: publicly accessible file url.
    """

    with open(config, "r") as json_config:
        # Load the JSON data into a dictionary
        config_data = json.load(json_config)

    # move the file into publicly shared folder
    path = move_file_to_folder(
        file_path=file_path, folder_path=config_data["simple_http_server_dir"]
    )

    # get file name
    filename = os.path.basename(path)

    return urljoin(config_data["cloudflare_zero_trust_domain"], filename)


# test stuff

# 1st create simple http server to store the file
# file must be transfered into that local dir


# publicly available temp dir
config_dir = "config.json"
splitted_audio_file = "/path/to/audio"
file_url = convert_local_path_to_url(file_path=splitted_audio_file, config=config_dir)
print(file_url)

# reads credentials
with open("creds.json", "r") as creds:
    # Load the JSON data into a dictionary
    credentials = json.load(creds)


transcription_result = get_transcription(
    api_key=credentials["api_key"], audio_url=file_url
)
print(transcription_result)
# create_http_server(port=8080, config=config_dir)
# 2nd convert local path to public url

print()
