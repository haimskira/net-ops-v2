from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def main_page():
    return render_template('main.html')

# כל שאר הדפים הסטטיים
@main_bp.route('/palo-manager')
def palo_manager_app(): return render_template('rule_manager.html')

@main_bp.route('/object-creator')
def object_creator_page(): return render_template('object_creator.html')

@main_bp.route('/log-viewer')
def log_viewer_page(): return render_template('log_viewer.html')

@main_bp.route('/policy-match-tool')
def policy_match_page(): return render_template('policy_match.html')

@main_bp.route('/admin-approval-tool')
def admin_approval_page():
    if not session.get('is_admin'): return redirect(url_for('main.main_page'))
    return render_template('admin_approval.html')

@main_bp.route('/object-approval-tool')
def object_approval_page():
    if not session.get('is_admin'): return redirect(url_for('main.main_page'))
    return render_template('object_approval.html')

@main_bp.route('/my-requests-tool')
def my_requests_page(): return render_template('my_requests.html')

@main_bp.route('/my-objects-tool')
def my_objects_page(): return render_template('my_objects.html')