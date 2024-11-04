import requests

def make_request(url, params):
    """
    Makes an HTTP GET request to the specified URL with the given parameters.

    :param url: The API endpoint URL.
    :param params: A dictionary of query parameters.
    :return: Parsed JSON response data or None if an error occurs.
    """
    params['output'] = 'json'  # Ensure the response is in JSON format
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None