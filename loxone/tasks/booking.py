from loxone import logger

import frappe

from typing import cast
from loxone.loxone.doctype.loxone_user.loxone_user import LoxoneUser, save_user_in_miniserver
import json

@frappe.whitelist()
def sync_loxone_access():
    logger.info("Starting sync_loxone_access task")

    sql = """
        -- Selection of confirmed events that have not yet finished (with a 5-minute buffer)
        WITH events AS
        (
            SELECT
                user,
                booking_resource,
                starts_on - INTERVAL 5 MINUTE as starts_on,
                ends_on + INTERVAL 5 MINUTE as ends_on
            FROM
                `tabItem Booking` booking
            WHERE
                booking.status = 'Confirmed'
                AND booking_resource IS NOT NULL
                AND user IS NOT NULL
                AND ends_on + INTERVAL 5 MINUTE >= SYSDATE()
        ),
        -- Selection of the soonest events per user and enrich with Loxone users and groups
        soonest_events AS
        (
            SELECT
                evt.user AS user_dockos,
                evt.booking_resource,
                evt.starts_on,
                evt.ends_on,
                DENSE_RANK() OVER (
                    PARTITION BY evt.user
                    ORDER BY evt.starts_on
                ) AS event_rank,
                user_grp.lx_uuid AS group_uuid,
                user_grp.name AS group_name,
                user_grp.lx_miniserver AS group_miniserver,
                usr.lx_uuid AS user_uuid,
                usr.name AS user_name,
                usr.lx_miniserver AS user_miniserver
            FROM
                events evt
                JOIN `tabLoxone Link Group-BookingResource` grp_link
                    ON grp_link.lx_booking_resource = evt.booking_resource
                JOIN `tabLoxone User Group` user_grp
                    ON user_grp.name = grp_link.parent
                JOIN `tabLoxone User` usr
                    ON usr.lx_dokos_user = evt.user
                    AND usr.lx_miniserver = user_grp.lx_miniserver
        )
        -- Aggregation of Loxone groups by user
        SELECT
            user_dockos,
            user_name,
            user_uuid,
            user_miniserver,
            CASE
                WHEN MIN(starts_on) <= SYSDATE()
                    THEN 'Y'
                ELSE 'N'
            END AS has_started,
            MIN(starts_on) AS starts_on,
            MAX(ends_on) AS ends_on,
            JSON_ARRAYAGG(DISTINCT group_name) AS lx_groups
        FROM
            soonest_events
        WHERE
            event_rank = 1
        GROUP BY
            user_dockos,
            user_name,
            user_uuid,
            user_miniserver
        ORDER BY
            starts_on ASC
    """

    rows = frappe.db.sql(sql, as_dict=True)

    for row in rows:
        logger.debug("Processing row: %s", row)
        
        doc = LoxoneUser.get_doc(row.get('user_name'))

        hasChanged = False

        # Configure temporary access
        if doc.lx_state != "4 - Time-Dependent":
            doc.lx_state = "4 - Time-Dependent"
            hasChanged = True

        if doc.lx_valid_from != row.get('starts_on'):
            doc.lx_valid_from = row.get('starts_on')
            hasChanged = True

        if doc.lx_valid_until != row.get('ends_on'):
            doc.lx_valid_until = row.get('ends_on')
            hasChanged = True
        
        # Configure groups
        expected_groups = set(json.loads(row.get('lx_groups')))
        actual_groups = set(link.lx_group_id for link in doc.lx_groups)
        # Remove all groups not in the expected list
        for child in doc.lx_groups:
            if child.lx_group_id not in expected_groups:
                doc.remove(child)
                hasChanged = True

        # Add all missing groups from the expected list
        for g in set(expected_groups - actual_groups):
            doc.append('lx_groups', {'lx_group_id': g})
            hasChanged = True

        if hasChanged:
            logger.info("Access changes detected for user: %s", doc.name)
            doc.flags.triggered_by_loxone = True
            doc.save()
            save_user_in_miniserver(doc)