# Time Reporting System

A Flask-based web system for time reporting with support for:
- User management with login
- Project management
- Time reporting per day and project
- Vacation and sick leave registration
- Swedish holidays and weekends
- Monthly overviews with working-day calculations
- Reports and statistics

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the application:
```bash
python app.py
```

3. Open your browser and go to: `http://localhost:5000`

## Features

### User Management
- Register a new account
- Log in/out
- Each user has their own time reporting

### Projects
- Add and manage projects
- Activate/deactivate projects

### Time Reporting
- Monthly view with all days
- Enter hours per project and day
- Automatic calculation of total worked hours
- Shows working days, required working hours, and difference
- Color coding:
  - Red: Holidays
  - Yellow: Weekends (Saturday/Sunday)
  - Blue: Vacation
  - Orange: Sick leave

### Leave
- Register vacation periods
- Register sick leave periods
- View all registered leave periods
- Automatic marking in the monthly view

### Reports
- Summary of hours per project
- Overview of vacation and sick leave
- Annual statistics

## Usage

1. **First time**: Register an account
2. **Log in** with your username and password
3. **Projects**: Add or manage projects
4. **Dashboard**: Navigate to the current month and fill in worked hours
5. **Leave**: Register vacation or sick leave
6. **Reports**: View summaries and statistics

## Technical Information

- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Authentication: Flask-Login
- ORM: SQLAlchemy

## Swedish Holidays 2026

The system includes all Swedish holidays for 2026:
- New Year's Day, Epiphany
- Good Friday, Easter weekend
- May Day, Ascension Day, Pentecost
- National Day, Midsummer Eve
- Christmas holidays, New Year's Eve

### If you want to help with translations please drop me a <a href="mailto:contact@wh3e.se">mail</a>.

