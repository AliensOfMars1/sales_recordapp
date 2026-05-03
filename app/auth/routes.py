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
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if not admin and form.username.data == Config.ADMIN_USERNAME:
            admin = Admin(username=Config.ADMIN_USERNAME)
            admin.set_password(Config.ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
        
        if admin and admin.check_password(form.password.data):
            login_user(admin, remember=True)
            next_page = request.args.get('next')
            flash('Welcome back, Admin!', 'success')
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