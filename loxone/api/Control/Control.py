from loxone.api.ApiClient import ApiClient

class Control:
    def __init__(self, client: ApiClient, uuid: str, name: str):
        self.uuid = uuid
        self.name = name
        self.client = client