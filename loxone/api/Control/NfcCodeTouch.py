from typing import Optional, Any, Dict, List

import urllib.parse
from loxone.api.Control import Control
from loxone.api.ApiClient import ApiClient
import logging
import json
from enum import Enum
from datetime import datetime, timezone
import pytz

logger = logging.getLogger(__name__)

class CodeType(Enum):
    """CodeType enum represents the different types of codes that can be used in the NfcCodeTouch system.

    It includes:
    - PERMANENT: Permanent codes do not have a time limit.
    - ONE_TIME: One-time codes are activated for a single use (for 90 seconds).
    - TIME_DEPENDENT: Time-dependent codes are activated for a specific datetime range.
    - VALID_UNTIL: Codes that are valid until a certain datetime.
    - VALID_FROM: Codes that are valid from a certain datetime.
    - DEACTIVATED: Codes that are deactivated and cannot be used.
    """
    PERMANENT = 0
    ONE_TIME = 1
    TIME_DEPENDENT = 2
    VALID_UNTIL = 3
    VALID_FROM = 4
    DEACTIVATED = 5


class Code:   
    """Code class represents a code for the NfcCodeTouch system.
    
    It includes properties such as UUID, name, code, type, outputs, default output,
    activation status, and time range for the code.
    """

    # Constants
    NUM_OUTPUTS = 6

    # Properties
    nfc: "NfcCodeTouch"
    uuid: str = ""
    name: str = ""
    is_active: bool = False
    is_empty: bool = True
    type: CodeType  = CodeType.DEACTIVATED
    outputs: List[bool] = [False] * NUM_OUTPUTS
    default_output: int = 1
    code: str = ""
    time_from: Optional[datetime] = None
    time_to: Optional[datetime] = None

    def __init__(self, nfc: "NfcCodeTouch"):
        self.nfc = nfc
    
    def create(self) -> bool:
        """Creates a new NFC code for the NfcCodeTouch device.
        
        This method constructs the endpoint URL with the provided code properties and sends a request to create the code.
        :return: True if the code was created successfully, False if the user is not permitted to create codes.
        :raises RuntimeError: If the API response indicates an error during code creation.
        """
        name_encoded = urllib.parse.quote(self.name)
        outputs = Code._encode_bitmask(self.outputs)

        endpoint = (f"jdev/sps/io/{self.nfc.uuid}/code/create/"
                    f"{name_encoded}/{self.code}/{self.type.value}/"
                    f"{outputs}/{self.default_output}"
                    f"{self.__get_time_parameters()}")

        response = self.nfc.client.get(endpoint)['LL']
        if response.get('Code') != '200':
            logger.error(f"Failed to create code: {response.get('value', 'Unknown error')}")
            return False

        self.refresh()
        return True
    
    def update(self) -> bool:
        """Updates the code properties for the NfcCodeTouch device.
        
        This method is used to update the properties of an existing code, such as its name, type, outputs, default output,
        code, and time range.
        It constructs the endpoint URL with the updated code properties and sends the request to the Loxone API.
        :return: True if the code was updated successfully, False if the user is not permitted to update codes.
        :raises RuntimeError: If the API response indicates an error during code update.
        """
        is_active = 0 if self.type == CodeType.DEACTIVATED else 1
        outputs = Code._encode_bitmask(self.outputs)
        code = -1 if self.code == "" else self.code
        
        endpoint = (f"jdev/sps/io/{self.nfc.uuid}/code/update/"
                    f"{self.uuid}/{is_active}/{self.name}/"
                    f"{code}/{self.type.value}/"
                    f"{outputs}/{self.default_output}"
                    f"{self.__get_time_parameters()}")

        response = self.nfc.client.get(endpoint)['LL']
        if response.get('Code') != '200':
            logger.error(f"Failed to update code (name: {self.name}): {response.get('value', 'Unknown error')}")
            return False
   
        self.nfc.refresh()
        return True
    
    def activate(self) -> bool:
        """Activates the code.
        
        This method sends a request to the Loxone API to activate the code identified by its UUID.
        :return: True if the code was activated successfully, False if the user is not permitted to activate codes.
        :raises RuntimeError: If the API response indicates an error during code activation.
        """
        endpoint = f"jdev/sps/io/{self.nfc.uuid}/code/activate/{self.uuid}"
        response = self.nfc.client.get(endpoint)['LL']
        if response.get('Code') != '200':
            logger.error(f"Failed to activate code: {response.get('value', 'Unknown error')}")
            return False
        
        self.nfc.refresh()
        return True

    def deactivate(self) -> bool:
        """Deactivates the code.
        
        This method sends a request to the Loxone API to deactivate the code.
        :return: True if the code was deactivated successfully, False if the user is not permitted to deactivate codes.
        :raises RuntimeError: If the API response indicates an error during code deactivation.
        """
        endpoint = f"jdev/sps/io/{self.nfc.uuid}/code/deactivate/{self.uuid}"
        response = self.nfc.client.get(endpoint)['LL']
        if response.get('Code') != '200':
            logger.error(f"Failed to deactivate code: {response.get('value', 'Unknown error')}")
            return False
        
        self.nfc.refresh()
        return True
    
    def delete(self, refresh_nfc: bool = True) -> bool:
        """Deletes the code from the NfcCodeTouch device.
        
        This method sends a request to the Loxone API to delete the code.
        :param code: A NfcCodeTouch.Code object representing the code to be deleted.
        :raises RuntimeError: If the API response indicates an error during code deletion.
        """
        endpoint = f"jdev/sps/io/{self.nfc.uuid}/code/delete/{self.uuid}"
        response = self.nfc.client.get(endpoint)['LL']
        if response.get('Code') == '500' and response.get('value') == 'uuid could not be read: ':
            return True  # Code already deleted, no action needed
        
        if response.get('Code') != '200':
            logger.error(f"Failed to delete code: {response.get('value', 'Unknown error')}")
            return False

        if refresh_nfc:
            self.nfc.refresh()
        return True
    
    def refresh(self):
        """Refreshes the current Code object with the latest data from the NfcCodeTouch device.
        
        This method retrieves the latest code data from the NfcCodeTouch device and updates the current Code object.
        """
        self.nfc.refresh()

        refreshed_code = None
        if self.uuid == None or self.uuid == "":
            refreshed_code  = next((code for code in self.nfc.codes() if code.name == self.name))
        else:
            refreshed_code = next((code for code in self.nfc.codes() if code.uuid == self.uuid))

        self.__dict__ = refreshed_code.__dict__

    def __get_time_parameters(self) -> str:
        """Returns the endpoint time parameters for the code based on its type.
        
        :return: A string representing the time parameters for the code.
        :raises ValueError: If the time parameters are not set correctly for the code type.
        """
        if self.type == CodeType.TIME_DEPENDENT:
            if not self.time_from:
                raise ValueError("time_from must be set for TIME_DEPENDENT codes")
            if not self.time_to:
                raise ValueError("time_to must be set for TIME_DEPENDENT codes")

            time_from = int(self.time_from.timestamp())
            time_to = int(self.time_to.timestamp())
            return f"/{time_from}/{time_to}"
        
        if self.type == CodeType.VALID_UNTIL:
            if not self.time_to:
                raise ValueError("time_from must be set for VALID_UNTIL codes")
            time_to = int(self.time_to.timestamp())
            return f"/{time_to}"
        
        if self.type == CodeType.VALID_FROM:
            if not self.time_from:
                raise ValueError("time_to must be set for VALID_FROM codes")
            time_from = int(self.time_from.timestamp())
            return f"/{time_from}"
    
        return ''

    @staticmethod
    def _encode_bitmask(outputs: List[bool]) -> int:
        """Encodes a list of boolean outputs into a bitmask.
        
        :param outputs: A list of boolean values representing the outputs (length must be NUM_OUTPUTS).
        :return: An integer representing the bitmask of the outputs.
        """
        bitmask = 0
        for i in range(1, Code.NUM_OUTPUTS + 1):
            if outputs[i - 1]:
                bitmask |= (1 << (i - 1))
        return bitmask
    
    @staticmethod
    def _decode_bitmask(bitmask: int) -> List[bool]:
        """Decodes a bitmask into a list of boolean outputs.
        
        :param bitmask: An integer representing the bitmask of the outputs.
        :return: A list of boolean values representing the outputs (length must be NUM_OUTPUTS).
        """
        output_list = [False] * Code.NUM_OUTPUTS
        for i in range(1, 7):
            if bitmask & (1 << (i - 1)):
                output_list[i - 1] = True
        return output_list

    def __str__(self):
        str = f"Code(uuid={self.uuid}, name={self.name}, is_active={self.is_active}, " \
                f"is_empty={self.is_empty}, type={self.type.name}, " \
                f"outputs={self.outputs}, " \
                f"default_output={self.default_output}"
        if self.time_from:
            str += f", time_from={self.time_from.astimezone(pytz.timezone('Europe/Brussels')).isoformat()}"
        if self.time_to:
            str += f", time_to={self.time_to.astimezone(pytz.timezone('Europe/Brussels')).isoformat()}"
        str += ")"
        return str


class CodeBuilder:
    """CodeBuilder class is used to construct a NfcCodeTouch.Code object.
    
    It provides methods to set properties such as UUID, name, code type, outputs,
    default output, code string, and time range.
    It validates the inputs and ensures that the constructed code meets the requirements.
    """
    def __init__(self, nfc: "NfcCodeTouch"):
        self.nfc = nfc
        self._code = Code(nfc)

    def uuid(self, uuid: str):
        self._code.uuid = uuid
        return self

    def name(self, name: str):
        self._code.name = name.strip()
        return self

    def type(self, type: CodeType):
        self._code.type = type
        if type == CodeType.DEACTIVATED:
            self._code.is_active = False
        return self

    def outputs(self, outputs: List[bool]):
        if len(outputs) != Code.NUM_OUTPUTS:
            raise ValueError(f"outputs must be a list of {Code.NUM_OUTPUTS} boolean values")
        self._code.outputs = outputs
        return self
    
    def set_output(self, output_number: int, value: bool = True):
        if not (1 <= output_number <= 6):
            raise ValueError("output_number must be between 1 and 6")
        self._code.outputs[output_number - 1] = value
        return self

    def default_output(self, default_output: int):
        if default_output < 1 or default_output > 6:
            raise ValueError("default_output must be between 1 and 6")
        self._code.default_output = default_output
        return self

    def code(self, code: str):
        if not code.isdigit() or not (2 <= len(code) <= 8):
            raise ValueError("Code must be numeric and between 2 and 8 digits long")
        self._code.code = code
        self._code.is_empty = False
        return self

    def time_from(self, time_from: Optional[datetime]):
        self._code.time_from = time_from
        return self

    def time_to(self, time_to: Optional[datetime]):
        self._code.time_to = time_to
        return self
    
    @staticmethod
    def from_dict(nfc: "NfcCodeTouch", code_dict: Dict[str, Any]):
        """Parses a code dictionary into a NfcCodeTouch.Code object.

        :param data: A dictionary containing code properties such as uuid, name, type, outputs, standardOutput,
                     timeFrom, timeTo, isActive, and isEmpty.
        :return: A NfcCodeTouch.Code object with the parsed properties.
        """
        builder = (CodeBuilder(nfc)
                   .uuid(code_dict.get('uuid', ''))
                   .name(code_dict.get('name', ''))
                   .type(CodeType(code_dict.get('type', CodeType.DEACTIVATED)))
                   .outputs(Code._decode_bitmask(code_dict.get('outputs', 0)))
                   .default_output(code_dict.get('standardOutput', 1))
                   )

        if 'timeFrom' in code_dict:
            builder.time_from(datetime.fromtimestamp(code_dict['timeFrom'], tz=timezone.utc))
        if 'timeTo' in code_dict:
            builder.time_to(datetime.fromtimestamp(code_dict['timeTo'], tz=timezone.utc))

        code = builder.build(skip_code=True)
 
        code.is_active = code_dict.get('isActive', False)
        code.is_empty = code_dict.get('isEmpty', True)

        return code

    def build(self, skip_code: bool = False) -> Code:
        """
        Builds the NfcCodeTouch.Code object with the provided properties.
        
        It validates the properties and raises ValueError if any validation fails.
        :param skip_code: If True, skips validation of the code string.
                        This is useful as the code is not provided by the Loxone API.
        :return: The constructed NfcCodeTouch.Code object.
        :raises ValueError: If any validation fails, such as empty name, code,
                            or invalid time range for the code type.
        """
        # Validate name
        if self._code.name == "":
            raise ValueError("Name cannot be empty")
        # Validate code
        if not skip_code and self._code.code == "":
            raise ValueError("Code cannot be empty")
        # Validate time_from and time_to
        if self._code.type is CodeType.VALID_UNTIL and self._code.time_to is None:
            raise ValueError("time_to must be set for VALID_UNTIL codes")
        if self._code.type is CodeType.VALID_FROM and self._code.time_from is None:
            raise ValueError("time_from must be set for VALID_FROM codes")
        if self._code.type is CodeType.TIME_DEPENDENT:
            if self._code.time_from is None or self._code.time_to is None:
                raise ValueError("Both time_from and time_to must be set for TIME_DEPENDENT codes")
            if self._code.time_from >= self._code.time_to:
                raise ValueError("time_from must be before time_to")
        # Validate default output
        if self._code.outputs[self._code.default_output - 1] == 0:
            raise ValueError("default_output must be in the list of outputs")

        return self._code


class NfcCodeTouch(Control.Control):
    """NfcCodeTouch class represents a Loxone NFC Code Touch device.
    
    It provides methods to manage NFC codes, including creating, updating, activating,
    deactivating, and deleting codes. It also allows sending impulses to outputs and retrieving
    the history of NFC code usage.
    """

    def __init__(self, client: ApiClient, uuid: str, name: str):
        super().__init__(client, uuid, name)
        self.__codes: list[Code] = []

    def impulse(self, output_number: int) -> bool:
        """Sends an impulse to the specified output number (1-6).
        
        This method is used to trigger an output impulse, which can be useful for various actions such as unlocking a door or activating a device.
        :param output_number: The output number to send the impulse to (1-6).
        :return: True if the impulse was sent successfully, False if the user is not permitted to trigger output impulses.
        :raises ValueError: If output_number is not between 1 and 6.
        """
        logger.info(f"{self.name} - Sending impulse to output {output_number}")
        if not (1 <= output_number <= 6):
            raise ValueError("output_number must be between 1 and 6")
        
        endpoint = f"jdev/sps/io/{self.uuid}/output/{output_number}"
        response = self.client.get(endpoint)

        if response and response.get('Code') == '423':
            logger.warning(f"{super().name} - User is not permitted to trigger output impulses")
            return False
        return True

    def history(self) -> List[Dict]:
        endpoint = f"jdev/sps/io/{self.uuid}/history"
        response = self.client.get(endpoint)
        return response.get('LL', {}).get('value', [])

    def codes(self, use_cache = True) -> List[Code]:
        """
        Retrieves a list of codes associated with the NfcCodeTouch device.
        
        Each code includes properties such as UUID, name, type, outputs, default output, code string,
        activation status, and time range.
        :param use_cache: If True, uses cached data if available. Otherwise, fetches fresh data from the API.
        :return: A list of Code objects representing the NFC codes.
        """
        if use_cache and len(self.__codes) > 0:
            return self.__codes
        endpoint = f"jdev/sps/io/{self.uuid}/codes"
        response = self.client.get(endpoint)

        if response['LL']['Code'] != '200':
            logger.error(f"Failed to retrieve codes: {response['LL'].get('value', 'Unknown error')}")
            return []

        json_data = json.loads(response['LL']['value'])
        self.__codes = [CodeBuilder.from_dict(self, code) for code in json_data]
        return self.__codes
    
    def refresh(self):
        """Refreshes the cache by clearing the cache and fetching fresh data from the API."""
        self.__codes = []
        self.codes(use_cache=False)

    def nfc_start_learn(self) -> Any:
        endpoint = f"jdev/sps/io/{self.uuid}/nfc/startlearn"
        response = self.client.get(endpoint)['LL']
        if response.get('Code') == '423':
            raise RuntimeError("Device not capable of executing the command (offline, not configured, or battery powered)")
        if response.get('Code') == '500':
            raise RuntimeError("Other error (User not admin, user has no visu pwd, etc.)")
        return response

    def nfc_stop_learn(self) -> Any:
        endpoint = f"jdev/sps/io/{self.uuid}/nfc/stoplearn"
        return self.client.get(endpoint)
    
    def code_builder(self) -> CodeBuilder:
        return CodeBuilder(self)
    
    def __str__(self):
        return f"NfcCodeTouch(uuid={self.uuid}, name={self.name})"
