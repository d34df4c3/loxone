__version__ = "2025.12.06"

import frappe
from logging import INFO, DEBUG

frappe.log_level = INFO
logger = frappe.logger("loxone")

@frappe.whitelist()
def check_connection(url: str, user: str, password: str) -> str:
    """Check if the connection to the Loxone Miniserver is valid."""
    from loxone.api import MiniServer
    return MiniServer.get_instance(url, user, password).get_status()

@frappe.whitelist()
def load_users(ms_name: str) -> None:
    """Load users from the MiniServer and create/update LoxoneUser documents."""
    from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver

    try:
        ms_doc = LoxoneMiniserver.get_doc(ms_name)
    except frappe.DoesNotExistError:
        logger.error(f"Miniserver '{ms_name}' does not exist.")
        return
    
    from loxone.loxone.doctype.loxone_user.loxone_user import load_users_from_miniserver
    load_users_from_miniserver(ms_doc)

@frappe.whitelist()
def load_user_groups(ms_name: str) -> None:
    """Load user groups from the MiniServer."""
    from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver

    try:
        ms_doc = LoxoneMiniserver.get_doc(ms_name)
    except frappe.DoesNotExistError:
        logger.error(f"Miniserver '{ms_name}' does not exist.")
        return

    from loxone.loxone.doctype.loxone_user_group.loxone_user_group import load_user_groups_from_miniserver
    load_user_groups_from_miniserver(ms_doc)

@frappe.whitelist()
def save_user_keycode(ms_name: str, user_name: str, keycode: str) -> None:
    """Save the keycode for the MiniServer."""
    if not (keycode.isdigit() and 2 <= len(keycode) <= 8):
        frappe.throw("Keycode must be a digit string between 2 and 8 characters long.")

    from loxone.loxone.doctype.loxone_user.loxone_user import LoxoneUser
    user_doc = LoxoneUser.get_doc(user_name)

    # Update Miniserver
    from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver
    updated = LoxoneMiniserver.get_doc(ms_name).get_miniserver().set_keycode(user_doc.lx_uuid, keycode)
    if not updated:
        frappe.throw(f"Failed to set keycode. Code is already used. Please use a different keycode.")
    
    # Update Loxone User document
    user_doc.lx_keycode = keycode
    user_doc.flags.triggered_by_loxone = True
    user_doc.save()

    logger.info(f"save_user_keycode - Keycode '{keycode}' set for user '{user_name}' on MiniServer '{ms_name}'.")

