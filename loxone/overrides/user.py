from loxone import logger

import frappe

from loxone.loxone.doctype.loxone_miniserver.loxone_miniserver import LoxoneMiniserver
from frappe.core.doctype.user.user import User

from typing import cast

def after_insert(doc, method=None):
    logger.info(f"Preparing to insert user")

    ms_names = frappe.get_all("Miniserver", filters={"lx_auto_create_user": True}, pluck="name")
    for ms_name in ms_names:
        create_user(doc, LoxoneMiniserver.get_doc(ms_name))

def on_trash(doc, method=None):
    logger.info(f"User {doc.name} is being deleted, removing from Loxone Miniserver")

    lx_users = frappe.get_all("Loxone User", filters={"lx_dokos_user": doc.name}, pluck="name")
    for lx_user_name in lx_users:
        lx_user_doc = frappe.get_doc("Loxone User", lx_user_name)
        lx_user_doc.delete()

def create_user(doc: User, ms_doc: LoxoneMiniserver) -> None:
    from loxone.loxone.doctype.loxone_user.loxone_user import LoxoneUser

    logger.info(f"Creating Loxone User {doc.name} for Miniserver {ms_doc.lx_name}")

    # Create a new Loxone User document
    lx_user_doc = cast(LoxoneUser, frappe.new_doc("Loxone User"))
    lx_user_doc.lx_miniserver = ms_doc.name # type: ignore
    lx_user_doc.lx_dokos_user = doc.name
    lx_user_doc.lx_name = doc.name.replace("@", "[a]") # type: ignore

    if ms_doc.lx_auto_enable_user:
        lx_user_doc.lx_state = "0 - Permanent"
    else:
        lx_user_doc.lx_state = "1 - Disabled"

    # Assign default groups to Loxone User
    default_groups = frappe.get_all("Loxone User Group",
        filters={"lx_miniserver": ms_doc.name, "lx_auto_assign": True},
        pluck="name")

    logger.info(f"Assigning Loxone User {doc.name} to default groups: {default_groups}")
    for group_name in default_groups:
        lx_user_doc.append("lx_groups", {"lx_group_id": group_name})

    lx_user_doc.insert()