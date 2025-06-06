# Summer of AI - Viswam.ai Attendance System

This is a Streamlit-based attendance tracking system for the Summer of AI program by Viswam.ai. The system includes features for AI Developers, Regional POCs, and Administrators.

## Features

### AI Developers
- User registration and authentication
- QR code generation for attendance
- Manual attendance marking
- Location-based attendance tracking

### Regional POCs
- QR code scanning for attendance
- Location-based attendance viewing
- Attendance management for their region

### Administrators
- Live analytics dashboard
- User distribution statistics
- Location-wise attendance analysis
- Raw data access

## Setup Instructions

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

3. Access the application in your web browser at `http://localhost:8501`

## Usage

1. Register as a new user (AI Developer, Regional POC, or Admin)
2. Login with your credentials
3. Access your role-specific dashboard
4. Follow the on-screen instructions for attendance marking or management

## Database

The application uses SQLite for data storage. The database file (`viswam_ai.db`) will be created automatically when you first run the application.

## Security

- Passwords are hashed using bcrypt
- User authentication is required for all features
- Session management is implemented for secure access

## Note

Make sure to keep your credentials secure and do not share them with others. 