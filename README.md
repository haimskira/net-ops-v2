# 🛡️ NetOps Portal - Palo Alto Automation & Monitoring

**NetOps Portal** is a secure, web-based platform designed to bridge the gap between IT teams and Network Operations. It provides a self-service interface for managing Palo Alto Networks firewalls, allowing users to request rules and objects while giving admins full control over approval processes.

Built with **Python (Flask)**, **Docker**, and **SQLite**, it ensures persistence, security (via LDAP), and ease of deployment.

---

## 🚀 Key Features

* **🔐 Secure Authentication:** Integrated **LDAP/Active Directory** login with role-based access control (Admins vs. Standard Users).
* **📜 Rule Management Workflow:**
    * Users submit firewall rule requests via a friendly UI.
    * Admins view, filter, approve, or reject requests.
    * **Auto-Push:** Approved rules are automatically pushed to the Palo Alto Firewall via API.
* **📦 Object Management:** Create and manage Address Objects directly from the portal.
* **📡 Live Traffic Logs:** Real-time Syslog listener (UDP 514) that captures and displays firewall traffic logs instantly in the browser.
* **🐳 Dockerized:** Fully containerized environment with persistent data storage.

---

## 🛠️ System Architecture

* **Backend:** Python Flask (Web Server + API + Syslog Listener thread).
* **Database:** SQLite (Stored persistently in `./data` volume).
* **Frontend:** HTML5, TailwindCSS, JavaScript.
* **Integration:** `pan-os-python` SDK & XML API.

---

## 📋 Prerequisites

Before running the system, ensure you have:

1.  **Docker & Docker Compose** installed on the Linux server.
2.  A **Palo Alto Firewall** with API access enabled.
3.  An **Active Directory (LDAP)** server for user authentication.

---

## ⚙️ Configuration (.env)

**Crucial Step:** Create a file named `.env` in the root directory. This file holds all secrets and is **not** included in Git.

Copy and paste the example below, then update the values:

```ini
# --- Firewall Settings ---
# The IP address of your Management Interface
FW_IP=HERE YOUR PALO ALTO MGMT IP

# Your Palo Alto API Key.
# Generate it by running: https://<FW_IP>/api/?type=keygen&user=<user>&password=<pass>
PA_API_KEY="YOUR_LONG_GENERATED_KEY_HERE"

# --- Web App Settings ---
# Random string for Flask session security
FLASK_SECRET_KEY="ChangeThisToSomethingRandom!@#"
# The UDP port the server will listen on for Syslogs (Standard: 514)
SYSLOG_PORT=514

# --- LDAP / Active Directory Settings ---
LDAP_SERVER=LDAP SERVER IP HERE
LDAP_DOMAIN=DOMAIN.NAME
LDAP_BASE_DN="DC=DOMAIN,DC=NAME"

# Group for Admins (Can approve/reject rules)
LDAP_ADMIN_GROUP="CN=netadmin,CN=Users,DC=DOMAIN,DC=NAME"

# Group for Standard Users (Can only request rules)
LDAP_USER_GROUP="CN=netlow,CN=Users,DC=DOMAIN,DC=NAME"


## 🚀 Installation & Deployment

### 1. Clone the Repository
Start by cloning the project to your server:
```bash
git clone [https://github.com/haimskira/net-ops-v2.git](https://github.com/haimskira/net-ops-v2.git)
cd net-ops-v2

