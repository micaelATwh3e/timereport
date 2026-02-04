from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_babel import Babel, gettext, lazy_gettext as _l, get_locale
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import calendar
import os
from pathlib import Path
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///timetracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'sv']
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)

def locale_selector():
    # Check if user has set a language preference in session
    if 'language' in session:
        return session['language']
    # Otherwise use browser preference or default to English
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES']) or 'en'

babel = Babel(app, locale_selector=locale_selector)

def compile_translations_if_needed():
    translations_dir = Path(app.root_path) / 'translations'
    if not translations_dir.exists():
        return

    po_files = list(translations_dir.rglob('messages.po'))
    if not po_files:
        return

    needs_compile = False
    for po_file in po_files:
        mo_file = po_file.with_suffix('.mo')
        if not mo_file.exists() or mo_file.stat().st_mtime < po_file.stat().st_mtime:
            needs_compile = True
            break

    if not needs_compile:
        return

    try:
        subprocess.run(['pybabel', 'compile', '-d', str(translations_dir)], check=True)
    except Exception as exc:
        print(f"Translation compile skipped: {exc}")

compile_translations_if_needed()

# Make get_locale available in templates
app.jinja_env.globals.update(get_locale=get_locale)
app.jinja_env.globals.update(_=gettext)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=365)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    time_entries = db.relationship('TimeEntry', backref='user', lazy=True)
    leave_entries = db.relationship('LeaveEntry', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_entries = db.relationship('TimeEntry', backref='project', lazy=True)
    owner = db.relationship('User', backref='projects', foreign_keys=[user_id])

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_restid = db.Column(db.Boolean, default=False)
    tracktamente = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaveEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)  # 'vacation', 'sickness'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    target_percentage = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project = db.relationship('Project', backref='targets')

# Svenska helgdagar 2026
HOLIDAYS_2026 = [
    datetime(2026, 1, 1),   # Nyårsdagen
    datetime(2026, 1, 6),   # Trettondedag jul
    datetime(2026, 4, 3),   # Långfredagen
    datetime(2026, 4, 5),   # Påskdagen
    datetime(2026, 4, 6),   # Annandag påsk
    datetime(2026, 5, 1),   # Första maj
    datetime(2026, 5, 14),  # Kristi himmelsfärdsdag
    datetime(2026, 5, 24),  # Pingstdagen
    datetime(2026, 6, 6),   # Nationaldagen
    datetime(2026, 6, 20),  # Midsommarafton
    datetime(2026, 12, 24), # Julafton
    datetime(2026, 12, 25), # Juldagen
    datetime(2026, 12, 26), # Annandag jul
    datetime(2026, 12, 31), # Nyårsafton
]

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Only allow registration if no users exist (first user setup)
    if User.query.count() > 0:
        flash('Kontakta en administratör för att skapa ett konto', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Första administratörskonto skapat! Logga in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Ogiltigt användarnamn eller lösenord', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    return redirect(url_for('month_view', year=current_year, month=current_month))

def build_month_context(year, month):
    # Get user's projects
    projects = Project.query.filter_by(user_id=current_user.id, active=True).all()
    
    # Get month data
    num_days = calendar.monthrange(year, month)[1]
    month_data = []
    
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    working_days = 0
    
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        weekday = date.weekday()
        
        # Get translated weekday name
        weekday_name = gettext(weekdays[weekday])
        
        # Check if holiday
        is_holiday = date in HOLIDAYS_2026
        is_weekend = weekday in [5, 6]
        
        # Get time entries for this day
        entries = TimeEntry.query.filter_by(
            user_id=current_user.id,
            date=date.date()
        ).all()
        
        restid_hours = 0
        restid_tracktamente = False
        project_entries = []
        
        for entry in entries:
            if entry.is_restid:
                restid_hours = entry.hours
                restid_tracktamente = entry.tracktamente
            else:
                project_entries.append(entry)
        
        # Get leave entries for this day
        leave = LeaveEntry.query.filter(
            LeaveEntry.user_id == current_user.id,
            LeaveEntry.start_date <= date.date(),
            LeaveEntry.end_date >= date.date()
        ).first()
        
        # Create project hours dict
        project_hours = {project.id: 0 for project in projects}
        for entry in project_entries:
            project_hours[entry.project_id] = entry.hours
        
        day_total = sum(project_hours.values()) + restid_hours
        
        if not is_holiday and not is_weekend and not leave:
            working_days += 1
        
        month_data.append({
            'date': date,
            'weekday': weekday_name,
            'is_holiday': is_holiday,
            'is_weekend': is_weekend,
            'leave': leave,
            'project_hours': project_hours,
            'restid_hours': restid_hours,
            'restid_tracktamente': restid_tracktamente,
            'total': day_total
        })
    
    # Calculate totals
    project_totals = {project.id: 0 for project in projects}
    for day in month_data:
        for project_id, hours in day['project_hours'].items():
            project_totals[project_id] += hours
    
    total_hours = sum(project_totals.values())
    required_hours = working_days * 8
    difference = total_hours - required_hours
    
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    month_name = gettext(months[month-1])
    
    return {
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_data': month_data,
        'projects': projects,
        'project_totals': project_totals,
        'total_hours': total_hours,
        'working_days': working_days,
        'required_hours': required_hours,
        'difference': difference
    }

@app.route('/month/<int:year>/<int:month>')
@login_required
def month_view(year, month):
    context = build_month_context(year, month)
    return render_template('month_view.html', **context)

@app.route('/month/<int:year>/<int:month>/print')
@login_required
def month_print(year, month):
    context = build_month_context(year, month)
    return render_template('print_timereport.html', **context)

@app.route('/add_time_entry', methods=['POST'])
@login_required
def add_time_entry():
    data = request.json
    project_id = data.get('project_id')
    date_str = data.get('date')
    hours = data.get('hours', 0)
    is_restid = data.get('is_restid', False)
    tracktamente = data.get('tracktamente', False)
    
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    if is_restid:
        # For restid, there's only one entry per day
        entry = TimeEntry.query.filter_by(
            user_id=current_user.id,
            date=date,
            is_restid=True
        ).first()
        
        if hours > 0:
            if entry:
                # Update existing entry
                entry.hours = hours
                entry.tracktamente = tracktamente
            else:
                # Create new entry
                entry = TimeEntry(
                    user_id=current_user.id,
                    date=date,
                    hours=hours,
                    is_restid=True,
                    tracktamente=tracktamente
                )
                db.session.add(entry)
        else:
            if tracktamente:
                # Keep or create entry even with 0 hours
                if entry:
                    entry.hours = 0
                    entry.tracktamente = True
                else:
                    entry = TimeEntry(
                        user_id=current_user.id,
                        date=date,
                        hours=0,
                        is_restid=True,
                        tracktamente=True
                    )
                    db.session.add(entry)
            else:
                # Delete entry if no hours and no travel allowance
                if entry:
                    db.session.delete(entry)
    else:
        # Check if entry exists for this project
        entry = TimeEntry.query.filter_by(
            user_id=current_user.id,
            project_id=project_id,
            date=date,
            is_restid=False
        ).first()
        
        if entry:
            entry.hours = hours
        else:
            entry = TimeEntry(
                user_id=current_user.id,
                project_id=project_id,
                date=date,
                hours=hours,
                is_restid=False
            )
            db.session.add(entry)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/add_project', methods=['POST'])
@login_required
def add_project():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if Project.query.filter_by(user_id=current_user.id, name=name).first():
        flash('Projektet finns redan', 'error')
        return redirect(url_for('projects'))
    
    project = Project(user_id=current_user.id, name=name, description=description)
    db.session.add(project)
    db.session.commit()
    
    flash('Projekt tillagt!', 'success')
    return redirect(url_for('projects'))

@app.route('/toggle_project/<int:project_id>')
@login_required
def toggle_project(project_id):
    project = db.get_or_404(Project, project_id)
    if project.user_id != current_user.id:
        flash('Åtkomst nekad', 'error')
        return redirect(url_for('projects'))
    project.active = not project.active
    db.session.commit()
    flash(f'Projekt {"aktiverat" if project.active else "inaktiverat"}', 'success')
    return redirect(url_for('projects'))

@app.route('/leave')
@login_required
def leave():
    leaves = LeaveEntry.query.filter_by(user_id=current_user.id).order_by(LeaveEntry.start_date.desc()).all()
    return render_template('leave.html', leaves=leaves)

@app.route('/add_leave', methods=['POST'])
@login_required
def add_leave():
    leave_type = request.form.get('leave_type')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    description = request.form.get('description', '')
    
    leave = LeaveEntry(
        user_id=current_user.id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        description=description
    )
    db.session.add(leave)
    db.session.commit()
    
    flash('Frånvaro tillagd!', 'success')
    return redirect(url_for('leave'))

@app.route('/delete_leave/<int:leave_id>')
@login_required
def delete_leave(leave_id):
    leave = db.get_or_404(LeaveEntry, leave_id)
    if leave.user_id != current_user.id:
        flash('Åtkomst nekad', 'error')
        return redirect(url_for('leave'))
    
    db.session.delete(leave)
    db.session.commit()
    flash('Frånvaro borttagen', 'success')
    return redirect(url_for('leave'))

@app.route('/project_targets', methods=['GET', 'POST'])
@login_required
def project_targets():
    current_date = datetime.now()
    year = request.args.get('year', current_date.year, type=int)
    month = request.args.get('month', current_date.month, type=int)
    
    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        target_percentage = request.form.get('target_percentage', type=float)
        
        # Check if project belongs to user
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
        
        # Find or create target
        target = ProjectTarget.query.filter_by(
            user_id=current_user.id,
            project_id=project_id,
            year=year,
            month=month
        ).first()
        
        if target:
            target.target_percentage = target_percentage
        else:
            target = ProjectTarget(
                user_id=current_user.id,
                project_id=project_id,
                year=year,
                month=month,
                target_percentage=target_percentage
            )
            db.session.add(target)
        
        db.session.commit()
        flash('Målprocent uppdaterad!', 'success')
        return redirect(url_for('project_targets', year=year, month=month))
    
    projects = Project.query.filter_by(user_id=current_user.id, active=True).all()
    targets = ProjectTarget.query.filter_by(
        user_id=current_user.id,
        year=year,
        month=month
    ).all()
    
    target_map = {t.project_id: {'percentage': t.target_percentage, 'id': t.id} for t in targets}
    
    return render_template('project_targets.html',
                         projects=projects,
                         target_map=target_map,
                         targets=targets,
                         year=year,
                         month=month)

@app.route('/delete_target/<int:target_id>')
@login_required
def delete_target(target_id):
    target = ProjectTarget.query.get_or_404(target_id)
    if target.user_id != current_user.id:
        flash('Åtkomst nekad', 'error')
        return redirect(url_for('project_targets'))
    
    year = target.year
    month = target.month
    db.session.delete(target)
    db.session.commit()
    flash('Målprocent borttagen', 'success')
    return redirect(url_for('project_targets', year=year, month=month))

@app.route('/reports')
@login_required
def reports():
    # Get summary for current year
    current_year = datetime.now().year
    
    # Total hours per project
    from sqlalchemy import func
    project_summary = db.session.query(
        Project.name,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(TimeEntry).filter(
        TimeEntry.user_id == current_user.id,
        func.strftime('%Y', TimeEntry.date) == str(current_year)
    ).group_by(Project.name).all()
    
    # Leave summary
    leave_summary = db.session.query(
        LeaveEntry.leave_type,
        func.count(LeaveEntry.id).label('count')
    ).filter(
        LeaveEntry.user_id == current_user.id,
        func.strftime('%Y', LeaveEntry.start_date) == str(current_year)
    ).group_by(LeaveEntry.leave_type).all()

    # Monthly totals for last 12 months
    today = datetime.now().date()
    start_month = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
    monthly_rows = db.session.query(
        func.strftime('%Y-%m', TimeEntry.date).label('month'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= start_month
    ).group_by('month').order_by('month').all()

    monthly_totals = {row.month: float(row.total_hours or 0) for row in monthly_rows}

    # Calculate monthly working days and vacation days
    monthly_working_days = {}
    monthly_vacation_days = {}
    
    for month_str in monthly_totals.keys():
        year_month = month_str.split('-')
        year_val = int(year_month[0])
        month_val = int(year_month[1])
        
        # Count working days in month (excluding weekends and holidays)
        working_days = 0
        vacation_days = 0
        num_days = calendar.monthrange(year_val, month_val)[1]
        
        for day in range(1, num_days + 1):
            date = datetime(year_val, month_val, day)
            weekday = date.weekday()
            is_holiday = date in HOLIDAYS_2026
            is_weekend = weekday in [5, 6]
            
            if not is_holiday and not is_weekend:
                # Check if it's a vacation day
                leave = LeaveEntry.query.filter(
                    LeaveEntry.user_id == current_user.id,
                    LeaveEntry.start_date <= date.date(),
                    LeaveEntry.end_date >= date.date()
                ).first()
                
                if leave:
                    vacation_days += 1
                else:
                    working_days += 1
        
        monthly_working_days[month_str] = working_days
        monthly_vacation_days[month_str] = vacation_days

    # Calculate monthly target hours (working days * 8)
    monthly_target_hours = {}
    for month_str in monthly_totals.keys():
        target = monthly_working_days.get(month_str, 0) * 8
        monthly_target_hours[month_str] = target

    # Calculate monthly percentages
    monthly_percentages = {}
    for month, hours in monthly_totals.items():
        target = monthly_target_hours.get(month, 160)
        percent = (hours / target * 100) if target > 0 else 0
        monthly_percentages[month] = round(percent, 1)

    # Monthly per project for last 12 months
    monthly_project_rows = db.session.query(
        func.strftime('%Y-%m', TimeEntry.date).label('month'),
        Project.name.label('project_name'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(Project, TimeEntry.project_id == Project.id).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= start_month
    ).group_by('month', 'project_name').order_by('month').all()

    monthly_project_map = {}
    for row in monthly_project_rows:
        monthly_project_map.setdefault(row.month, {})[row.project_name] = float(row.total_hours or 0)

    # Get project targets for each month
    monthly_targets = {}
    for month_str in monthly_totals.keys():
        year_month = month_str.split('-')
        year_val = int(year_month[0])
        month_val = int(year_month[1])
        
        targets = ProjectTarget.query.filter_by(
            user_id=current_user.id,
            year=year_val,
            month=month_val
        ).all()
        
        monthly_targets[month_str] = {t.project_id: t.target_percentage for t in targets}

    # Yearly totals for last 5 years
    start_year = today.year - 4
    yearly_rows = db.session.query(
        func.strftime('%Y', TimeEntry.date).label('year'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        TimeEntry.user_id == current_user.id,
        func.strftime('%Y', TimeEntry.date) >= str(start_year)
    ).group_by('year').order_by('year').all()

    yearly_totals = {row.year: float(row.total_hours or 0) for row in yearly_rows}

    # Project percentage current year
    project_percentages = []
    total_year_hours = sum([float(r.total_hours or 0) for r in project_summary])
    for project_name, total_hours in project_summary:
        hours = float(total_hours or 0)
        percent = (hours / total_year_hours * 100) if total_year_hours > 0 else 0
        project_percentages.append({
            'project': project_name,
            'hours': hours,
            'percent': round(percent, 1)
        })

    # Tracktamente days and travel time (restid)
    tracktamente_count = db.session.query(func.count(TimeEntry.id)).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.is_restid == True,
        TimeEntry.tracktamente == True,
        func.strftime('%Y', TimeEntry.date) == str(current_year)
    ).scalar() or 0

    travel_time = db.session.query(func.sum(TimeEntry.hours)).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.is_restid == True,
        func.strftime('%Y', TimeEntry.date) == str(current_year)
    ).scalar() or 0
    travel_time = float(travel_time)

    return render_template('reports.html',
                         project_summary=project_summary,
                         leave_summary=leave_summary,
                         year=current_year,
                         monthly_totals=monthly_totals,
                         monthly_percentages=monthly_percentages,
                         monthly_target_hours=monthly_target_hours,
                         monthly_working_days=monthly_working_days,
                         monthly_vacation_days=monthly_vacation_days,
                         monthly_project_map=monthly_project_map,
                         monthly_targets=monthly_targets,
                         yearly_totals=yearly_totals,
                         project_percentages=project_percentages,
                         tracktamente_count=tracktamente_count,
                         travel_time=travel_time,
                         projects=Project.query.filter_by(user_id=current_user.id, active=True).all())

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Du har inte behörighet att komma åt denna sida', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        flash('Du har inte behörighet att utföra denna åtgärd', 'error')
        return redirect(url_for('dashboard'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('Användarnamnet finns redan', 'error')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(email=email).first():
        flash('E-postadressen används redan', 'error')
        return redirect(url_for('admin_users'))
    
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash(f'Användare {username} tillagd!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/toggle_admin/<int:user_id>')
@login_required
def admin_toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Du har inte behörighet att utföra denna åtgärd', 'error')
        return redirect(url_for('dashboard'))
    
    user = db.get_or_404(User, user_id)
    
    if user.id == current_user.id:
        flash('Du kan inte ändra din egen administratörsstatus', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'{user.username} är nu {"administratör" if user.is_admin else "inte administratör"}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Du har inte behörighet att utföra denna åtgärd', 'error')
        return redirect(url_for('dashboard'))
    
    user = db.get_or_404(User, user_id)
    
    if user.id == current_user.id:
        flash('Du kan inte ta bort ditt eget konto', 'error')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Användare {user.username} borttagen', 'success')
    return redirect(url_for('admin_users'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['language'] = lang
        session.permanent = True
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Make user 'iwery' admin
        iwery = User.query.filter_by(username='iwery').first()
        if iwery:
            if not iwery.is_admin:
                iwery.is_admin = True
                db.session.commit()
                print("User 'iwery' is now an admin!")
            
            pass
    
    app.run(debug=True, port=8777, host="0.0.0.0")
