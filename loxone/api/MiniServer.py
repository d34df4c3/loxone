from typing import Optional, overload
from loxone.api.Control.NfcCodeTouch import NfcCodeTouch
from loxone.api.ApiClient import ApiClient
from loxone.api.Control import Control
from loxone import logger
import json
from typing import cast

class MiniServer:
    """Class representing a Loxone MiniServer."""
    
    # Properties
    client: ApiClient
    serial_number: str = ""
    name: str = ""
    controls: list[Control.Control] = []

    # Private properties
    __loxapp3: dict = {}
    
    def __init__(self, client: ApiClient):
        self.client = client

    def loxapp3(self) -> dict:
        return self.__loxapp3

    def get_nfc_code_touches(self) -> list[NfcCodeTouch]:
        """Get all NFC Code Touch controls."""
        nfc_code_touches = []
        for control in self.controls:
            if isinstance(control, NfcCodeTouch):
                nfc_code_touches.append(control)
        return nfc_code_touches
    
    def get_nfc_code_touch_by_name(self, name: str) -> Optional[NfcCodeTouch]:
        """Get an NFC Code Touch control by its name."""
        for nfc in self.get_nfc_code_touches():
            if nfc.name == name:
                return nfc
        logger.warning(f"NFC Code Touch with name '{name}' not found.")
        return None
    
    def get_status(self) -> str:
        """Get the status of the MiniServer."""
        response = self.client.get("jdev/sps/status").get('LL', {})
        if response.get('Code') != '200':
            logger.error(f"Failed to get MiniServer status: {response.get('Message', 'Unknown error')}")
            raise PermissionError(f"Failed to get MiniServer status: {response.get('Message', 'Unknown error')}")
        return response['value']
    
    def get_users(self) -> list[dict]:
        """Get the list of users from the MiniServer.

        Returns:
            list[dict]: A list of user dictionaries containing user information:
                name: User's name
                uuid: User's UUID
                isAdmin: bool: Whether the user is an admin
                userState: int: Indicates whether or not a user is active and may log in or get access:
                    ● 0 = enabled, without time limitations
                    ● 1 = disabled
                    ● 2 = enabled until, disabled after that point in time
                    ● 3 = enabled from, disabled before that point in time
                    ● 4 = timespan, only enabled in between those points in time
        """

        response = self.client.get("jdev/sps/getuserlist2").get('LL', {})
        if response.get('Code') != '200':
            logger.error(f"Failed to get users: {response.get('Message', 'Unknown error')}")
            return []

        return json.loads(response.get('value'))
    
    def get_user(self, uuid: str) -> dict:
        """Get details of a specific user by UUID.

        Args:
            uuid (str): The UUID of the user.

        Returns:
            dict: A dictionary containing user details.
        """
        response = self.client.get(f"jdev/sps/getuser/{uuid}").get('LL', {})
        if response.get('Code') != '200':
            logger.error(f"Failed to get user details for {uuid}: {response.get('Message', 'Unknown error')}")
            raise PermissionError('Failed to get user details. Your Loxone user must be granted "Loxone Config" rights.')

        return json.loads(response.get('value', '{}'))

    def get_user_groups(self) -> list[dict]:
        """Get the list of user groups from the MiniServer.

        Returns:
            list[dict]: A list of user group dictionaries containing group information:
                name: Group's name
                description: Group's description
                uuid: Group's UUID
                type: int: Group type (e.g., 'user', 'admin'):
                    ● 0 = Normal
                    ● 1 = Admin (deprecated)
                    ● 2 = All
                    ● 3 = None
                    ● 4 = AllAccess → New “Admin Group”
        """
        response = self.client.get("jdev/sps/getgrouplist").get('LL', {})
        if response.get('Code') != '200':
            logger.error(f"Failed to get user groups: {response.get('Message', 'Unknown error')}")
            return []

        return json.loads(response.get('value'))

    def create_user(self, name: str) -> str | None:
        """Create a new user on the MiniServer.

        Args:
            name (str): The name of the user to create.

        Returns:
            str: The UUID of the created user if created successfully, None otherwise.
        """
        response = self.client.get(f"jdev/sps/createuser/{name}").get('LL', {})
        if response['Code'] != '200':
            logger.error(f"Failed to create user '{name}': {response.get('Message', 'Unknown error')}")
            return None

        return response['value']

    def update_user(self, user_dict: dict) -> None:
        """Update an existing user on the MiniServer.

        Args:
            user_dict (dict): A dictionary containing user details to update.
                - uuid (str): The UUID of the user.
                - name (str): The name of the user.
                - userState (int): The state of the user.
                - validFrom (str): The valid from date of the user.
                - validUntil (str): The valid until date of the user.
        """
        response = self.client.get(f"jdev/sps/addoredituser/{json.dumps(user_dict)}").get('LL', {})
        if response['Code'] != '200':
            logger.error(f"Failed to update user '{user_dict.get('uuid')}': {response.get('Message', 'Unknown error')}")
            raise PermissionError(f"Failed to update user '{user_dict.get('uuid')}': {response.get('Message', 'Unknown error')}")

    def delete_user(self, user_uuid: str) -> None:
        """Delete a user from the MiniServer.

        Args:
            user_uuid (str): The UUID of the user to delete.
        """
        response = self.client.get(f"jdev/sps/deleteuser/{user_uuid}").get('LL', {})
        if response['Code'] != '200':
            logger.error(f"Failed to delete user '{user_uuid}': {response.get('Message', 'Unknown error')}")
            raise PermissionError(f"Failed to delete user '{user_uuid}': {response.get('Message', 'Unknown error')}")

    def remove_user_from_group(self, user_uuid: str, group_uuid: str) -> None:
        """Remove a user from a group on the MiniServer.

        Args:
            user_uuid (str): The UUID of the user to remove.
            group_uuid (str): The UUID of the group to remove the user from.
        """
        response = self.client.get(f"jdev/sps/removeuserfromgroup/{user_uuid}/{group_uuid}").get('LL', {})
        if response['Code'] != '200':
            logger.error(f"Failed to remove user '{user_uuid}' from group '{group_uuid}': {response.get('Message', 'Unknown error')}")
            raise PermissionError(f"Failed to remove user '{user_uuid}' from group '{group_uuid}': {response.get('Message', 'Unknown error')}")

    def assign_user_to_group(self, user_uuid: str, group_uuid: str) -> None:
        """Assign a user to a group on the MiniServer.

        Args:
            user_uuid (str): The UUID of the user to assign.
            group_uuid (str): The UUID of the group to assign the user to.
        """
        response = self.client.get(f"jdev/sps/assignusertogroup/{user_uuid}/{group_uuid}").get('LL', {})
        if response['Code'] != '200':
            logger.error(f"Failed to assign user '{user_uuid}' to group '{group_uuid}': {response.get('Message', 'Unknown error')}")
            raise PermissionError(f"Failed to assign user '{user_uuid}' to group '{group_uuid}': {response.get('Message', 'Unknown error')}")

    def set_keycode(self, user_uuid: str, keycode: str) -> bool:
        """Set a keycode for a user on the MiniServer.

        Args:
            user_uuid (str): The UUID of the user to set the keycode for.
            keycode (str): The keycode to set for the user.
        """
        response = self.client.get(f"jdev/sps/updateuseraccesscode/{user_uuid}/{keycode}").get('LL', {})
        if response['Code'] == '400':
            logger.error(f"Failed to set keycode. User '{user_uuid}' unknown on Miniserver.")
            raise ValueError(f"Failed to set keycode. User '{user_uuid}' unknown on Miniserver.")
        if response['Code'] == '409':
            logger.warning(f"Keycode already exists.")
            return False
        if response['Code'] not in ['200', '201']:
            logger.error(f"Failed to set keycode for user '{user_uuid}': {response['Code']} - {response.get('Message', 'Unknown error')}")
            raise PermissionError(f"Failed to set keycode for user '{user_uuid}': {response['Code']} - {response.get('Message', 'Unknown error')}")
        
        return True

    def load(self) -> 'MiniServer':
        """Load the MiniServer configuration."""
        try:
            loxapp3 = self.client.get("data/LoxAPP3.json")
        except Exception as e:
            logger.error("Failed to load MiniServer configuration: %s", e)
            raise ValueError(f"Failed to load MiniServer configuration: {e}")

        self.__loxapp3 = loxapp3

        self.__load_ms_info(loxapp3.get("msInfo", {}))
        self.__load_controls(loxapp3.get("controls", {}))

        logger.info(f"MiniServer: '{self.name}' (serial: {self.serial_number}) loaded.")
        return self

    def __load_ms_info(self, ms_info: dict):
        """Load MiniServer information from the configuration."""
        self.serial_number = ms_info.get('serialNr', 'NotFound')
        self.name = ms_info.get('msName', 'NoName')

    def __load_controls(self, controls: dict):
        """Load controls from the MiniServer configuration."""
        self.controls = []
        for uuid, control in controls.items():
            if control.get('type') == "NfcCodeTouch":
                self.controls.append(NfcCodeTouch(self.client, uuid, control.get('name')))
                logger.info(f"NfcCodeTouch: '{control.get('name')}' (uuid: {uuid}) loaded.")
            else:
                logger.warning(f"Skipping control of type {control.get('type')} (uuid: {uuid}) - Not implemented")
    
    def is_loaded(self) -> bool:
        """Check if the MiniServer configuration is loaded."""
        return bool(self.__loxapp3)

@overload
def get_instance(client) -> MiniServer:
    """Get an instance of MiniServer."""
    pass

@overload
def get_instance(url: str, user: str, password: str) -> MiniServer:
    """Get an instance of MiniServer with basic authentication."""
    pass

def get_instance(*args, **kwargs) -> MiniServer:
    """Get an instance of MiniServer."""
    if len(args) == 1 and isinstance(args[0], ApiClient):
        return MiniServer(args[0])

    if len(args) == 3 \
        and isinstance(args[0], str) \
        and isinstance(args[1], str) \
        and isinstance(args[2], str):
        from ApiClient import BasicAuth
        return MiniServer(cast(ApiClient, BasicAuth(args[0], args[1], args[2])))

    raise ValueError("Invalid arguments")