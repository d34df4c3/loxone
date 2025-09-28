# Loxone

ERPNext app to integrate with Loxone Miniservers:

- Auto‑provision Loxone users when a ERPNext user is created
- Auto‑assign Loxone Groups based on room reservations in ERPNext

## About Loxone DocTypes

This module introduces three DocTypes that let you connect one or more Loxone Miniservers to your ERPNext site, manage Loxone user groups, and provision Loxone users from your ERPNext Users. If you’re an administrator, you’ll mainly work with these three:

- **Loxone Miniserver:** where you configure and monitor each Miniserver connection.
- **Loxone User Group:** where you map ERPNext Booking resources (like rooms) to Loxone groups for access control.
- **Loxone User:** where you see and control each person’s Loxone account and group memberships.

### Loxone Miniserver

The **Loxone Miniserver** DocType represents one physical controller and its API connection details. Create one record per physical controller you operate.

This is the central place to test connectivity to validate reachability and credentials, load User Groups and Users from the Miniserver.

Integration options let you automate day‑to‑day provisioning. When enabled, the Miniserver can create a Loxone account automatically whenever a new ERPNext User is added, generate and assign a keycode at creation time, and activate the new account without manual steps.

Supported authentication method:
- Basic User/Password

### Loxone User Group

The **Loxone User Group** DocType mirrors a group that already exists on a specific Miniserver and provides the bridge to ERPNext concepts such as rooms, or other booking resources. By linking a group to an ERPNext resource, you enable reservation‑driven access: when someone books that resource, the integration can grant temporary membership to the corresponding Loxone group for the booking window, then remove it afterward.

You can also define default behaviors for how ERPNext interacts with the group. For example, you may mark a group as a default so that new **Loxone Users** on that Miniserver are added automatically, giving baseline access without manual steps. Groups are always scoped to one Miniserver; if you operate multiple controllers, maintain a distinct **Loxone User Group** record for each controller’s group you want to use in ERPNext.

Group creation is managed in Loxone, not from the ERPNext Desk. First create or configure the group on the Miniserver, then open the related **Loxone Miniserver** document in ERPNext and use the "Load Users" from Miniserver action to refresh groups. 

### Loxone User

The **Loxone User** DocType represents a person’s account on a specific Miniserver. It lets you provision new accounts, update profile details, set status and validity periods (for example, “valid from” and “valid until”), define an access code, and manage group memberships. When you save the document, changes are synchronized to the target Miniserver.

Each **Loxone User** record is scoped to one Miniserver and can optionally be linked to an ERPNext User. If a user has been pulled from the Miniserver, the record will not be linked by default; you can map it manually by selecting the corresponding Dokos User in the document. Conversely, when the account is created by ERPNext—using the “Automatically create user” option configured on the **Loxone Miniserver**—the link to the ERPNext User is established automatically. This linkage allows reservation‑driven access to work end‑to‑end: when a person books a room in ERPNext, the integration can add or remove the appropriate Loxone groups on their Miniserver account for the correct time window.

## About Scheduled tasks

### Task: sync_loxone_access

The scheduled task **sync_loxone_access** runs every 2 minutes and keeps Loxone group memberships aligned with ERPNext bookings.

On each run, it evaluates current and imminent events, applies a 5‑minute buffer before the event start and after the event end, and determines the effective access window. It then resolves the associated Booking Resources that are mapped to **Loxone User Groups** and the ERPNext User linked to each event, ensuring the corresponding **Loxone User** on the same Miniserver is granted membership for the duration of the window.

During the window, the task adds or maintains the user’s membership in the mapped **Loxone User Group** and removes it once the window has elapsed. It ignores resources not mapped to **Loxone User Group** and ERPNext users not linked to a **Loxone User**.

## Prerequisites

### 1 - System timezone (OS)

Ensure the timezone is setup to Europe/Brussels

```bash
# Check timezone
timedatectl
# Set to Europe/Brussels
sudo timedatectl set-timezone Europe/Brussels
# Verify
timedatectl
```

### 2 - MariaDB timezone

MariaDB uses the system clock but the SQL timezone may be “SYSTEM” or an explicit zone. Ensure sessions resolve to Europe/Brussels.

```bash
# Restart database to take the latest system values
sudo systemctl restart mariadb
# Connect to database and verify timezone and date
mysql -u root -p
select  @@global.time_zone, SYSDATE();
```

### 3 - Enable Frappe schedulers

Loxone app is using a schedule task to activate Loxone User and auto-assign Loxone Groups based on room reservations in ERPNext

Ensure Frappe scheduler is enable.

```bash
cd $PATH_TO_YOUR_BENCH
# Verify status
bench --site test.dokos.local doctor
# Enable the scheduler services
bench --site test.dokos.local enable-scheduler
# If schedulers are paused, resumed them
bench --site test.dokos.local scheduler resume
````

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/d34df4c3/loxone --branch develop
bench --site $NAME_OF_YOUR_SITE install-app loxone
```

## Configuration

### In Desk → Loxone Miniserver

1. Add a new Miniserver
2. Setup the Connection Settings
   - URL: protocol://hostname:port of the Miniserver endpoint (example: http://213.211.136.162:8080)
   - User: Technical Loxone user with followings rights:
     - Loxone Config
     - User Management
     - Web Interface/Apps
   - Password: password of the technical user
3. Click "Check Connection"
   - You should get a message like "Connection to Miniserver is OK. (Running 100/sec)". In case of failure, review your connection settigns.
   - Note that during the connection check, the Structured File of the Miniserver is loaded in tab "Loxone Config"
4. Setup the Dokos Integration options:
   - Automatically create user
   - Automatically assign keycode
   - Enable user by default
5. Save

Once saved, new actions are avaiable:

6. Loxone Actions → Load User Groups
7. Loxone Actions → Load Users

Note that "Connections" section provides shortcuts to "Loxone User Group" and "Loxone User" linked to your Miniserver.
