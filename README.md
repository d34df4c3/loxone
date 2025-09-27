# Loxone

ERPNext app to integrate with Loxone Miniservers:

- Auto‑provision Loxone users when a ERPNext user is created
- Auto‑assign Loxone Groups based on room reservations in ERPNext

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

### Forewords about Loxone DocTypes

#### Loxone Miniserver

#### Loxone User Group

#### Loxone User

### Desk → Loxone Miniserver

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
