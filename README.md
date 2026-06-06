# QS Marketplace
### E-Marketplace for Quantity Surveyors, Clients & Vendors

---

## HOW TO START

### Windows
Double-click **START_APP.bat**
The browser will open automatically.

### Mac / Linux
1. Open Terminal in this folder
2. Run: `chmod +x START_APP.sh && ./START_APP.sh`

---

## DEFAULT LOGIN CREDENTIALS

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@qsmarket.com       | Admin@123   |
| Client  | client1@example.com      | Client@123  |
| Client  | client2@example.com      | Client@123  |
| QS Pro  | qs1@example.com          | QS@12345    |
| QS Pro  | qs2@example.com          | QS@12345    |
| QS Pro  | qs3@example.com          | QS@12345    |
| Vendor  | vendor1@example.com      | Vendor@123  |
| Vendor  | vendor2@example.com      | Vendor@123  |

---

## SWITCHING TO MYSQL

1. Open `config.py` in any text editor
2. Set `USE_MYSQL = True`
3. Fill in your MySQL details:
   - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
4. Install PyMySQL: `pip install pymysql`
5. Create your MySQL database first, then restart the app

---

## ADMIN FEATURES

- **User Management**: Verify, activate, suspend or delete any account
- **Commission Tracker**: View all commissions, mark as paid/overdue/disputed
- **Database Management**: Re-seed data, reset everything, control seed flag
- **Settings**: Change commission rate platform-wide

---

## PROJECT STRUCTURE

```
QS_Marketplace/
├── START_APP.bat        ← Double-click (Windows)
├── START_APP.sh         ← Run in terminal (Mac/Linux)
├── app.py               ← Main Flask application
├── config.py            ← Database & settings config
├── requirements.txt     ← Python packages (auto-installed)
├── database/
│   ├── marketplace.db   ← SQLite database (auto-created)
│   └── .seeded          ← Seed control flag file
├── templates/           ← HTML pages
│   └── admin/           ← Admin panel pages
└── static/
    └── uploads/         ← User uploaded files
```

---

## REQUIREMENTS

- Python 3.8 or higher
- Internet connection on first run (to install packages)
- Windows 7+ or macOS 10.14+ or Linux

---

*Built with Flask + SQLite · © 2025 QS Marketplace*
