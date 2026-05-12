from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.auth import auth_bp
from app.forms import LoginForm
from app.models import Admin, Barber
from config import Config

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Check if logged in user is barber, CEO, or admin
        if hasattr(current_user, 'name'):  # Barber has 'name' attribute
            return redirect(url_for('barbers.barber_dashboard'))
        elif hasattr(current_user, 'role') and current_user.role == 'ceo':
            return redirect(url_for('ceo.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        
        # Create default admin if not exists
        if not admin and form.username.data == Config.ADMIN_USERNAME:
            admin = Admin(username=Config.ADMIN_USERNAME, role='admin')
            admin.set_password(Config.ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
        
        # Create default CEO if not exists
        if not admin and form.username.data == 'ceo':
            admin = Admin(username='ceo', role='ceo')
            admin.set_password('ceo2024')
            db.session.add(admin)
            db.session.commit()
        
        if admin and admin.check_password(form.password.data):
            login_user(admin, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {admin.username}!', 'success')
            
            # Redirect based on role
            if admin.role == 'ceo':
                return redirect(next_page) if next_page else redirect(url_for('ceo.dashboard'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('admin_login.html', form=form)


@auth_bp.route('/barber-login', methods=['GET', 'POST'])
def barber_login():
    if current_user.is_authenticated:
        # If already logged in as barber, go to barber dashboard
        if hasattr(current_user, 'name'):  # Barber has 'name' attribute
            return redirect(url_for('barbers.barber_dashboard'))
        # If logged in as admin or CEO, redirect to respective dashboard
        elif hasattr(current_user, 'role') and current_user.role == 'ceo':
            return redirect(url_for('ceo.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find barber by email or name
        barber = Barber.query.filter_by(email=form.username.data).first()
        if not barber:
            barber = Barber.query.filter_by(name=form.username.data).first()
        
        if barber and barber.active and barber.check_password(form.password.data):
            login_user(barber, remember=True)
            flash(f'Welcome back, {barber.name}!', 'success')
            return redirect(url_for('barbers.barber_dashboard'))
        else:
            flash('Invalid credentials or account inactive', 'danger')
    
    return render_template('barber_login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))