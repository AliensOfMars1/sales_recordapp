from flask import render_template, request, jsonify
from flask_login import login_required
from app.main import main_bp
from app.models import Sale, Expense, Barber, BarberAdvance
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db

# ===== PUBLIC PAGES =====
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')
# ========================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Today's sales
    today_sales = Sale.query.filter(func.date(Sale.sale_date) == today).all()
    today_total = sum(s.amount for s in today_sales)
    today_cash = sum(s.amount for s in today_sales if s.payment_method == 'cash')
    today_momo = sum(s.amount for s in today_sales if s.payment_method == 'momo')
    
    # Weekly sales
    week_sales = Sale.query.filter(Sale.sale_date >= week_start, Sale.sale_date <= week_end).all()
    week_total = sum(s.amount for s in week_sales)
    week_momo = sum(s.amount for s in week_sales if s.payment_method == 'momo')
    
    # Weekly expenses
    week_expenses = Expense.query.filter(Expense.expense_date >= week_start, Expense.expense_date <= week_end).all()
    week_expenses_total = sum(e.amount for e in week_expenses)
    
    # Weekly advances (unsettled)
    week_advances = db.session.query(func.sum(BarberAdvance.amount)).filter(
        BarberAdvance.advance_date >= week_start,
        BarberAdvance.advance_date <= week_end,
        BarberAdvance.settled == False
    ).scalar() or 0
    
    # Barber performance
    barbers = Barber.query.filter_by(active=True).all()
    barber_performance = []
    for barber in barbers:
        barber_week_sales = barber.total_sales(week_start, week_end)
        commission = barber_week_sales / 3
        advances = barber.total_advances(week_start, week_end)
        barber_performance.append({
            'name': barber.name,
            'sales': barber_week_sales,
            'commission': commission,
            'advances': advances,
            'payout': commission - advances
        })
    
    # Recent sales - order by creation time (most recent first)
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
    
    # Get week days for the dropdown (for Daily Sales by Barber)
    week_days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        week_days.append({
            'name': day_date.strftime('%A'),
            'date': day_date.strftime('%Y-%m-%d')
        })
    
    selected_day = week_days[0]  # Monday as default
    
    return render_template('dashboard.html',
                         today_total=today_total,
                         today_cash=today_cash,
                         today_momo=today_momo,
                         week_total=week_total,
                         week_expenses=week_expenses_total,
                         week_momo=week_momo,
                         week_advances=week_advances,
                         barber_performance=barber_performance,
                         recent_sales=recent_sales,
                         week_days=week_days,
                         selected_day_name=selected_day['name'],
                         selected_day_date=selected_day['date'])


@main_bp.route('/dashboard/daily-sales')
@login_required
def daily_sales_by_barber():
    """API endpoint to get daily sales grouped by barber for a specific date"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify([])
    
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Get all active barbers
    barbers = Barber.query.filter_by(active=True).all()
    
    result = []
    for barber in barbers:
        # Get sales for the specific date
        sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date == target_date
        ).all()
        
        total = sum(s.amount for s in sales)
        cash = sum(s.amount for s in sales if s.payment_method == 'cash')
        momo = sum(s.amount for s in sales if s.payment_method == 'momo')
        
        result.append({
            'name': barber.name,
            'total': total,
            'cash': cash,
            'momo': momo
        })
    
    return jsonify(result)