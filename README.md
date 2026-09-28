# CircleCareSG

CircleCareSG is a web-based community support platform designed to support seniors through wellbeing check-ins, support requests, volunteer assistance, scheduled visits, and guardian involvement.

This project was developed using Django as part of a university Final Year Project.

## Requirements

- Python 3
- pip

The required Python packages are listed in `requirements.txt`.

## Setup Instructions

### 1. Download the Project

Download the repository as a ZIP file from GitHub and extract it to a folder on your computer.

Alternatively, clone the repository using Git.

### 2. Open the Project Folder

Open a terminal inside the extracted `CircleCareSG` project folder.

The folder should contain files such as:

- `manage.py`
- `requirements.txt`
- `db.sqlite3`
- `DEMO_ACCOUNTS.txt`

### 3. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 4. Activate the Virtual Environment

On macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Check the Django Project

```bash
python manage.py check
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

### 8. Open CircleCareSG

Open the following address in a web browser:

```text
http://127.0.0.1:8000/
```

## Demo Accounts

Demo login credentials for the different CircleCareSG user roles are provided in:

```text
DEMO_ACCOUNTS.txt
```

The included `db.sqlite3` database contains the dummy data required for the demonstration accounts and prototype.

All accounts, profile information, images, documents, and other records included in the project are dummy/test data created for demonstration purposes.

## User Roles

CircleCareSG includes the following user portals:

- **Senior** – wellbeing check-ins, support requests, volunteer information, and related support features.
- **Volunteer** – assigned seniors, availability, scheduled visits, visit reports, and alerts.
- **Guardian** – linked senior information, check-in reports, alerts, and volunteer contact.
- **Administrator** – user management, volunteer assignments, support requests, visit scheduling, reports, and alerts.

## Running the Tests

The project test suite can be run using:

```bash
python manage.py test accounts seniorPortal volunteerPortal guardianPortal adminPortal
```

## Technology

- Django
- Python
- SQLite
- HTML
- CSS
- JavaScript