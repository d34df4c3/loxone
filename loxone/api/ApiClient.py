import requests

from loxone import logger

class ApiClient():
    """Base class for API clients.
    
    This class serves as a base for creating API clients that can interact with the Loxone API.
    It requires a URL to be specified upon initialization and defines a method `get` that must
    be implemented by subclasses to perform GET requests.
    """
    def __init__(self, url: str):
        self.url = url

    def get(self, path: str) -> dict:
        raise NotImplementedError("Subclasses must implement this method")


class BasicAuth(ApiClient):
    """A client for Loxone API with basic authentication.
    
    This client uses HTTP Basic Authentication to access the Loxone API.
    It requires a URL, a username, and an optional password.
    """

    def __init__(self, url: str, user: str, password: str = ""):
        super().__init__(url)
        self.user = user
        self.password = password

    def get(self, path: str) -> dict:
        url = f"{self.url}/{path}"
        logger.info(f"{self.__str__()} - Requesting URL: {url}")

        response = requests.get(url, auth=(self.user, self.password))
        if response.status_code != 200:
            logger.error(f"{self.__str__()} - Error: {response.status_code} - {response.text}")
            response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        if content_type != 'application/json':
           raise ValueError(f"Expected JSON response, got {content_type}")
        
        logger.info(f"{self.__str__()} - JSON: {response.json()}")
        return response.json()
    
    def __str__(self):
        return f"BasicAuth(user={self.user})"