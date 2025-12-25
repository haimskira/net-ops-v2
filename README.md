# 🛡️ NetOps Portal - Palo Alto Automation & Monitoring

**NetOps Portal** is a comprehensive web-based platform designed to streamline operations for Palo Alto Networks Firewalls. It bridges the gap between end-users and network administrators by providing a self-service portal for rule requests, object management, and real-time traffic monitoring.

Built with **Python (Flask)**, **Docker**, and **SQLite**, it ensures persistence, security (via LDAP), and ease of deployment.

---

## 🚀 Key Features

* **🔐 Secure Authentication:** Integrated **LDAP/Active Directory** login with role-based access control (Admin vs. User).
* **📜 Rule Management Workflow:**
    * Users can submit firewall rule requests via a friendly UI.
    * Admins can view, approve, or reject requests.
    * **Auto-Push:** Approved rules are automatically pushed to the Firewall via API.
* **📦 Object Management:** Create and manage Address Objects directly from the portal.
* **📡 Live Traffic Logs:** Real-time Syslog listener (UDP 514) that captures and displays firewall traffic logs instantly in the browser.
* **🐳 Dockerized:** Fully containerized environment with persistent storage for the database.

---

## 🛠️ Architecture

* **Backend:** Python Flask (Web Server + API).
* **Database:** SQLite (Stored persistently via Docker Volumes).
* **Background Tasks:** Threaded Syslog Listener for handling UDP streams.
* **Frontend:** HTML5, TailwindCSS, JavaScript (Polling for live logs).
* **Integration:** `pan-os-python` SDK for Palo Alto communication.

---

## 📋 Prerequisites

Before running the system, ensure you have:

1.  **Docker & Docker Compose** installed on your server.
2.  A **Palo Alto Firewall** with API access enabled.
3.  An **Active Directory (LDAP)** server for user authentication.

---

## ⚙️ Configuration (.env)

Create a `.env` file in the root directory of the project. This file holds all your secrets and configurations.

**⚠️ Important:** Never commit this file to Git!

```ini
# --- Firewall Settings ---
FW_IP=YOUR_FW_IP_HERE
# Generate API Key on the FW using: https://<FW_IP>/api/?type=keygen&user=<user>&password=<pass>
PA_API_KEY="YOUR_LONG_API_KEY_HERE"

# --- Web App Settings ---
FLASK_SECRET_KEY="SuperSecretKey!@#"
SYSLOG_PORT=514

# --- LDAP / Active Directory Settings ---
LDAP_SERVER=LDAP_SERVER_IP
LDAP_DOMAIN=DOMAIN.NAME
LDAP_BASE_DN="DC=DOAMIN,DC=NAME"
# Group for Admins (Can approve rules)
LDAP_ADMIN_GROUP="CN=netadmin,CN=Users,DC=DOAMIN,DC=NAME"
# Group for Standard Users (Can request rules)
LDAP_USER_GROUP="CN=netlow,CN=Users,DC=DOAMIN,DC=NAME"

```

---

## 🚀 Installation & Deployment

### 1. Clone the Repository

```bash
git clone [https://github.com/haimskira/net-ops-v2.git](https://github.com/haimskira/net-ops-v2.git)
cd net-ops-v2

```

### 2. Prepare Data Directory

Create a directory to store the database persistently (so data survives restarts):

```bash
mkdir -p data

```

### 3. Setup Environment

Create your `.env` file (see Configuration section above) and paste your credentials.

### 4. Run with Docker

We have included a helper script to pull the latest changes, build, and run the container safely.

```bash
chmod +x docker/update.sh
./docker/update.sh

```

Alternatively, run manually via Docker Compose:

```bash
docker-compose -f docker/docker-compose.yml up -d --build

```

---

## 🔌 Palo Alto Configuration (For Live Logs)

To see **Live Traffic Logs**, you must configure your Palo Alto Firewall to send Syslogs to this server.

1. Go to **Device > Server Profiles > Syslog**.
2. Add a new server:
* **Name:** NetOps-Server
* **Server:** `<Your_Docker_Host_IP>`
* **Port:** `514`
* **Format:** BSD (Standard)
* **Transport:** UDP


3. Go to **Log Settings** and add this profile to "Traffic" logs.
4. **Commit** changes.

---

## 📂 Project Structure

```text
net-ops-v2/
├── app.py                 # Main application entry point
├── config.py              # Configuration loader
├── netops.db              # (Local Dev) Database file
├── .env                   # Environment variables (GitIgnored)
├── data/                  # (Production) Persistent DB storage
├── docker/                # Docker configuration files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── update.sh          # Deployment script
├── managers/              # Business logic (FW, Data, Models)
├── routes/                # Flask Blueprints (API endpoints)
└── templates/             # HTML Frontend

```

---

## 🛡️ Security Notes

* **Database:** In production (Docker), the `netops.db` is stored in the `./data` folder on the host machine. Ensure this folder is backed up regularly.
* **Git:** The `.gitignore` file is configured to exclude `*.db`, `.env`, and `data/` to prevent sensitive data leakage.

---

**Developed by NetOps Team & Gemini Pro ;) ** 🚀

---
