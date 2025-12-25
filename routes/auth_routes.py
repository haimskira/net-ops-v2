from flask import Blueprint, render_template, request, redirect, url_for, session
from auth import authenticate_ldap  # <--- הנה הייבוא של הקובץ שלך

# הגדרת ה-Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # קריאה לפונקציה המקורית שלך שנמצאת ב-auth.py
        success, is_admin = authenticate_ldap(username, password)
        
        if success:
            session['user'] = username 
            session['is_admin'] = is_admin
            # הפניה לדף הראשי (שים לב לנקודה: main.main_page)
            return redirect(url_for('main.main_page'))
        else:
            error = "שם משתמש או סיסמה שגויים"
            
    return render_template('login.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.clear()
    # הפניה חזרה ללוגין
    return redirect(url_for('auth.login'))