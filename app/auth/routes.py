from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.auth.utils import validate_login, get_user_role
from app.utils.database import get_db_connection
from app.auth.utils import get_session
import bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate credentials
        db = get_db_connection(db_name="cims")
        user = validate_login(db, username, password)
        
        if user:
            # Set session variables
            session_data = get_session(db, user['MemberID'], username, user['Role'])
            if session_data:
                session['user_id'] = session_data['user_id']
                session['username'] = session_data['username']
                session['role'] = session_data['role']
                session['token'] = session_data['token']
                
                # Redirect based on role
                if user['Role'] == 'doctor':
                    return redirect(url_for('doctor.dashboard'))
                elif user['Role'] == 'staff':
                    return redirect(url_for('staff.dashboard'))
                else:  # student/user
                    return redirect(url_for('student.dashboard'))
            else:
                flash('Error creating session. Please try again.', 'danger')
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('login.html')

@auth.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
