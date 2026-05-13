from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.ceo import ceo_bp
from app.models import Sale, Expense, Barber, Service, BarberAdvance, Admin
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from dateutil.relativedelta import relativedelta

# CEO access decorator
def ceo_required(f):
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in.', 'danger')
            return redirect(url_for('auth.login'))
        if not hasattr(current_user, 'role') or current_user.role != 'ceo':
            flash('Access denied. CEO only.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


@ceo_bp.route('/dashboard')
@ceo_required
def dashboard():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Current week stats
    week_sales = Sale.query.filter(
        Sale.sale_date >= week_start,
        Sale.sale_date <= week_end,
        Sale.status.in_(['active', 'updated'])
    ).all()
    week_total = sum(s.amount for s in week_sales)
    
    week_expenses = Expense.query.filter(
        Expense.expense_date >= week_start,
        Expense.expense_date <= week_end
    ).all()
    week_expenses_total = sum(e.amount for e in week_expenses)
    
    total_commission = week_total / 3
    week_net_profit = week_total - week_expenses_total - total_commission
    
    # Year-to-Date Net Profit
    year_start = today.replace(month=1, day=1)
    ytd_sales = Sale.query.filter(
        Sale.sale_date >= year_start,
        Sale.sale_date <= today,
        Sale.status.in_(['active', 'updated'])
    ).all()
    ytd_total = sum(s.amount for s in ytd_sales)
    
    ytd_expenses = Expense.query.filter(
        Expense.expense_date >= year_start,
        Expense.expense_date <= today
    ).all()
    ytd_expenses_total = sum(e.amount for e in ytd_expenses)
    
    ytd_commission = ytd_total / 3
    ytd_net_profit = ytd_total - ytd_expenses_total - ytd_commission
    
    # Monthly Net Profit data for chart (last 12 months)
    months_labels = []
    monthly_net_profit = []
    
    for i in range(11, -1, -1):
        month_date = today.replace(day=1) - relativedelta(months=i)
        month_start = month_date
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year+1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month+1, day=1) - timedelta(days=1)
        
        month_sales = Sale.query.filter(
            Sale.sale_date >= month_start,
            Sale.sale_date <= month_end,
            Sale.status.in_(['active', 'updated'])
        ).all()
        month_total = sum(s.amount for s in month_sales)
        
        month_expenses = Expense.query.filter(
            Expense.expense_date >= month_start,
            Expense.expense_date <= month_end
        ).all()
        month_exp_total = sum(e.amount for e in month_expenses)
        
        month_commission = month_total / 3
        month_net = month_total - month_exp_total - month_commission
        
        months_labels.append(month_start.strftime('%b %Y'))
        monthly_net_profit.append(month_net)
    
    return render_template('ceo/dashboard.html',
                         week_total=week_total,
                         week_expenses=week_expenses_total,
                         week_net_profit=week_net_profit,
                         ytd_net_profit=ytd_net_profit,
                         months_labels=months_labels,
                         monthly_net_profit=monthly_net_profit)


@ceo_bp.route('/expense-analysis')
@ceo_required
def expense_analysis():
    # Get current year
    current_year = datetime.now().year
    selected_year = request.args.get('year', type=int, default=current_year)
    
    # Monthly expenses for selected year
    monthly_expenses = []
    months = []
    for month in range(1, 13):
        month_start = datetime(selected_year, month, 1).date()
        if month == 12:
            month_end = datetime(selected_year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(selected_year, month + 1, 1).date() - timedelta(days=1)
        
        month_exp = Expense.query.filter(
            Expense.expense_date >= month_start,
            Expense.expense_date <= month_end
        ).all()
        month_total = sum(e.amount for e in month_exp)
        monthly_expenses.append(month_total)
        months.append(datetime(selected_year, month, 1).strftime('%B'))
    
    # Expenses by category for current year
    category_totals = db.session.query(
        Expense.category, func.sum(Expense.amount)
    ).filter(
        func.strftime('%Y', Expense.expense_date) == str(selected_year)
    ).group_by(Expense.category).all()
    
    categories = [cat[0].capitalize() for cat in category_totals]
    category_amounts = [float(cat[1]) for cat in category_totals]
    
    # Yearly total expenses
    year_start = datetime(selected_year, 1, 1).date()
    year_end = datetime(selected_year, 12, 31).date()
    total_expenses = sum(e.amount for e in Expense.query.filter(
        Expense.expense_date >= year_start,
        Expense.expense_date <= year_end
    ).all())
    
    years = list(range(current_year - 2, current_year + 1))
    
    return render_template('ceo/expense_analysis.html',
                         monthly_expenses=monthly_expenses,
                         months=months,
                         categories=categories,
                         category_amounts=category_amounts,
                         total_expenses=total_expenses,
                         selected_year=selected_year,
                         years=years)


@ceo_bp.route('/barbers')
@ceo_required
def barbers():
    barbers = Barber.query.order_by(Barber.name).all()
    return render_template('ceo/barbers.html', barbers=barbers)


@ceo_bp.route('/add-barber', methods=['GET', 'POST'])
@ceo_required
def add_barber():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        active = request.form.get('active') == 'true'
        
        barber = Barber(name=name, phone=phone, email=email, active=active)
        db.session.add(barber)
        db.session.commit()
        flash(f'Barber "{name}" added successfully!', 'success')
        return redirect(url_for('ceo.barbers'))
    
    return render_template('ceo/add_barber.html')


@ceo_bp.route('/edit-barber/<int:barber_id>', methods=['GET', 'POST'])
@ceo_required
def edit_barber(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    
    if request.method == 'POST':
        barber.name = request.form.get('name')
        barber.phone = request.form.get('phone')
        barber.email = request.form.get('email')
        barber.active = request.form.get('active') == 'true'
        db.session.commit()
        flash('Barber updated successfully!', 'success')
        return redirect(url_for('ceo.barbers'))
    
    return render_template('ceo/edit_barber.html', barber=barber)


@ceo_bp.route('/delete-barber/<int:barber_id>')
@ceo_required
def delete_barber(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    db.session.delete(barber)
    db.session.commit()
    flash('Barber deleted successfully!', 'success')
    return redirect(url_for('ceo.barbers'))


@ceo_bp.route('/services')
@ceo_required
def services():
    services = Service.query.order_by(Service.name).all()
    return render_template('ceo/services.html', services=services)


@ceo_bp.route('/add-service', methods=['GET', 'POST'])
@ceo_required
def add_service():
    if request.method == 'POST':
        name = request.form.get('name')
        default_price = float(request.form.get('default_price'))
        description = request.form.get('description')
        active = request.form.get('active') == 'true'
        
        service = Service(name=name, default_price=default_price, description=description, active=active)
        db.session.add(service)
        db.session.commit()
        flash(f'Service "{name}" added successfully!', 'success')
        return redirect(url_for('ceo.services'))
    
    return render_template('ceo/add_service.html')


@ceo_bp.route('/edit-service/<int:service_id>', methods=['GET', 'POST'])
@ceo_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.default_price = float(request.form.get('default_price'))
        service.description = request.form.get('description')
        service.active = request.form.get('active') == 'true'
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('ceo.services'))
    
    return render_template('ceo/edit_service.html', service=service)


@ceo_bp.route('/delete-service/<int:service_id>')
@ceo_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('ceo.services'))


@ceo_bp.route('/yearly-profit')
@ceo_required
def yearly_profit():
    current_year = datetime.now().year
    years = []
    yearly_profits = []
    
    for year in range(current_year - 4, current_year + 1):
        year_start = datetime(year, 1, 1).date()
        year_end = datetime(year, 12, 31).date()
        
        year_sales = Sale.query.filter(
            Sale.sale_date >= year_start,
            Sale.sale_date <= year_end,
            Sale.status.in_(['active', 'updated'])
        ).all()
        year_total = sum(s.amount for s in year_sales)
        
        year_expenses = Expense.query.filter(
            Expense.expense_date >= year_start,
            Expense.expense_date <= year_end
        ).all()
        year_exp_total = sum(e.amount for e in year_expenses)
        
        year_commission = year_total / 3
        year_net = year_total - year_exp_total - year_commission
        
        years.append(year)
        yearly_profits.append(year_net)
    
    return render_template('ceo/yearly_profit.html',
                         years=years,
                         yearly_profits=yearly_profits,
                         current_year=current_year)