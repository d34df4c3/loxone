import frappe

from loxone import logger
from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver
from loxone.loxone.doctype.loxone_user.loxone_user import LoxoneUser

from datetime import datetime, timezone
import pytz

from enum import Enum


date_format = '%Y-%m-%d %H:%M:%S'
brussels_tz = pytz.timezone("Europe/Brussels")
EPOCH_TO_2009_SECONDS = 1230768000  # seconds

class State(Enum):
    """Enumeration of possible states for a Loxone User.

    States:
    - PERMANENT: No time limit.
    - DISABLED: User is deactivated.
    - ENABLED_UNTIL: Active until a specific datetime.
    - ENABLED_FROM: Active from a specific datetime.
    - TIME_DEPENDENT: Active within a specific datetime range.
    """
    UNASSIGNED = -1
    PERMANENT = 0
    DISABLED = 1
    ENABLED_UNTIL = 2
    ENABLED_FROM = 3
    TIME_DEPENDENT = 4

    __state_str_map = {
        PERMANENT: "0 - Permanent",
        DISABLED: "1 - Disabled",
        ENABLED_UNTIL: "2 - Enabled Until",
        ENABLED_FROM: "3 - Enabled From",
        TIME_DEPENDENT: "4 - Time-Dependent",
    }

    __str_state_map = {v: k for k, v in __state_str_map.items()}

    def to_string(self) -> str:
        """Return the string representation of the state."""
        return self.__state_str_map[self.value]

    @classmethod
    def from_string(cls, state_str: str) -> 'State':
        """Convert a string representation of the state to the State enum."""
        if state_str in cls.__str_state_map:
            return cls(cls.__str_state_map[state_str])
        else:
            raise ValueError(f"Unknown state: {state_str}")


class LoxoneUserMapper:
    """Mapper class for Loxone User document.

    This class is responsible for mapping data from Miniserver JSON to Loxone User document.
    Attributes:
        doc (LoxoneUser): The Loxone User document to map data to.
    """

    state: State

    def __init__(self, doc: LoxoneUser, ms_doc: LoxoneMiniserver):
        self.doc = doc
        self.ms_doc = ms_doc

    def load(self, data: dict) -> None:
        """Map data from JSON to the document fields.

        Args:
            data (dict): The data to map.
                - uuid (str): The UUID of the user group.
                - name (str): The name of the user group.
                - description (str): The description of the user group.
                - type (str): The type of the user group.
                - userRights (int): The user rights of the user group.
                - userState (int): The state of the user group.
                - validFrom (str): The valid from date of the user group.
                - validUntil (str): The valid until date of the user group.
                - usergroups (list): The list of user groups assigned to the user.
        """
        self.load_miniserver()
        self.load_uuid(data)
        self.load_name(data)
        self.load_state(data)
        self.load_valid_from(data)
        self.load_valid_until(data)
        self.load_user_groups(data)

        # FIXME: "lx_code"
        # FIXME: "lx_nfc_tags"


    def load_miniserver(self) -> None:
        if self.doc.lx_miniserver is None:
            self.doc.lx_miniserver = self.ms_doc.name
        if self.doc.lx_miniserver != self.ms_doc.name:
            frappe.throw(f"Loxone User {self.doc.lx_name} is assigned to a different Miniserver ({self.doc.lx_miniserver}) than the current one ({self.ms_doc.name}).")

    def load_uuid(self, data) -> None:
        if 'uuid' not in data:
            frappe.throw("Loxone User UUID not found in data.")
        self.doc.lx_uuid = data['uuid']

    def load_name(self, data) -> None:
        if 'name' not in data:
            frappe.throw("Loxone User name not found in data.")
        self.doc.lx_name = data['name']
    
    def load_state(self, data) -> None:
        """Load the state of the user from the data."""
        if 'userState' not in data:
            frappe.throw("Loxone User state not found in data.")
        self.state = State(data['userState'])
        self.doc.lx_state = self.state.to_string() # type: ignore[assignment]

    def load_valid_from(self, data) -> None:
        if self.state not in [State.ENABLED_FROM, State.TIME_DEPENDENT]:
            return
        if 'validFrom' not in data:
            frappe.throw("Loxone User valid from date not found in data.")

        self.doc.lx_valid_from = datetime.fromtimestamp(data['validFrom'] + EPOCH_TO_2009_SECONDS, tz=timezone.utc).replace(tzinfo=None)

    def load_valid_until(self, data) -> None:
        if self.state not in [State.ENABLED_UNTIL, State.TIME_DEPENDENT]:
            return
        if 'validUntil' not in data:
            frappe.throw("Loxone User valid until date not found in data.")

        self.doc.lx_valid_until = datetime.fromtimestamp(data['validUntil'] + EPOCH_TO_2009_SECONDS, tz=timezone.utc).replace(tzinfo=None)

    def load_user_groups(self, data) -> None:
        if 'usergroups' not in data:
            return
        
        user_groups = LoxoneUserMapper.get_user_groups_of(self.doc.lx_miniserver)
        name_to_uuid = {group['name']: group['lx_uuid'] for group in user_groups}
        uuid_to_name = {group['lx_uuid']: group['name'] for group in user_groups}

        uuids_to_assign = [g['uuid'] for g in data['usergroups']]
        # Delete groups that are not assigned to user in Loxone
        for child_group in self.doc.lx_groups:
            if name_to_uuid[child_group.lx_group_id] not in uuids_to_assign:
                child_group.delete()
                logger.info(f"Loxone User - Removed group {child_group.lx_group_id} from user {self.doc.lx_name}")

        # Add new groups that are assigned to user in Loxone
        assigned_uuids = [name_to_uuid[c.lx_group_id] for c in self.doc.lx_groups]
        for uuid in set(uuids_to_assign) - set(assigned_uuids):
            if uuid not in uuid_to_name:
                frappe.throw(f"Loxone group {uuid} not found in Dokos. Please load user groups first.")

            self.doc.append("lx_groups", {"lx_group_id": uuid_to_name[uuid]})
            logger.info(f"Loxone User - Added group {uuid_to_name[uuid]} to user {self.doc.lx_name}")

    
    __cache_user_groups = {}
    
    @staticmethod
    def get_user_groups_of(miniserver_name: str, use_cache: bool = True) -> list[dict]:
        if use_cache and miniserver_name in LoxoneUserMapper.__cache_user_groups:
            return LoxoneUserMapper.__cache_user_groups[miniserver_name]
        
        user_groups = frappe.get_list('Loxone User Group',
            filters={'lx_miniserver': miniserver_name},
            fields=['name', 'lx_uuid']
        )

        LoxoneUserMapper.__cache_user_groups[miniserver_name] = user_groups
        return user_groups

class LoxoneUserSerializer:
    """Serializer for Loxone User document to Miniserver JSON API."""

    def __init__(self, doc: LoxoneUser):
        self.doc = doc
        self.state = State.UNASSIGNED
        self.user_dict: dict = {}

    def serialize(self) -> dict:
        """Serialize the Loxone User document to a dictionary for Miniserver API.

        Returns:
            dict: A dictionary containing user details.
                - uuid (str): The UUID of the user.
                - name (str): The name of the user.
                - state (int): The state of the user.
                - validFrom (str): The valid from date in ISO format.
                - validUntil (str): The valid until date in ISO format.
                - usergroups (list): List of user groups assigned to the user.
        """
        self.serialize_uuid()
        self.serialize_name()
        self.serialize_state()
        self.serialize_valid_from()
        self.serialize_valid_until()
        
        return self.user_dict
    
    def serialize_uuid(self) -> None:
        if not self.doc.lx_uuid:
            frappe.throw(f"Loxone User {self.doc.name} does not have a UUID set.")
        self.user_dict['uuid'] = self.doc.lx_uuid
    
    def serialize_name(self) -> None:
        if not self.doc.lx_name:
            frappe.throw(f"Loxone User {self.doc.name} does not have a name set.")
        self.user_dict['name'] = self.doc.lx_name.replace("@", "[a]") # Replace '@' with '[a]' for Loxone compatibility

    def serialize_state(self) -> None:
        if not self.doc.lx_state:
            frappe.throw(f"Loxone User {self.doc.name} does not have a state set.")

        self.state = State.from_string(self.doc.lx_state).value
        self.user_dict['userState'] = self.state
    
    def serialize_valid_from(self) -> None:
        if self.state not in [State.ENABLED_FROM.value, State.TIME_DEPENDENT.value]:
            return
        if not self.doc.lx_valid_from:
            frappe.throw(f"Loxone User {self.doc.name} does not have a valid from date set.")

        self.user_dict['validFrom'] = LoxoneUserSerializer.serialize_date(self.doc.lx_valid_from)

    def serialize_valid_until(self) -> None:
        if self.state not in [State.ENABLED_UNTIL.value, State.TIME_DEPENDENT.value]:
            return
        if not self.doc.lx_valid_until:
            frappe.throw(f"Loxone User {self.doc.name} does not have a valid until date set.")

        self.user_dict['validUntil'] = LoxoneUserSerializer.serialize_date(self.doc.lx_valid_until)

    @staticmethod
    def serialize_date(date: str |datetime) -> int:
        """Convert a date string to a timestamp in seconds."""
        if not date or date == "":
            return 0

        if isinstance(date, str):
            date = brussels_tz.localize(datetime.fromisoformat(date))

        return int(date.timestamp() - EPOCH_TO_2009_SECONDS)