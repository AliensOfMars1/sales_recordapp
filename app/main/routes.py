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
    
    # Today's sales (exclude deleted)
    today_sales = Sale.query.filter(
        func.date(Sale.sale_date) == today,
        Sale.status.in_(['active', 'updated'])
    ).all()
    today_total = sum(s.amount for s in today_sales)
    today_cash = sum(s.amount for s in today_sales if s.payment_method == 'cash')
    today_momo = sum(s.amount for s in today_sales if s.payment_method == 'momo')
    
    # Weekly sales (exclude deleted)
    week_sales = Sale.query.filter(
        Sale.sale_date >= week_start,
        Sale.sale_date <= week_end,
        Sale.status.in_(['active', 'updated'])
    ).all()
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
    
    # Recent sales by barber (today, limit 5 per barber) - NEW
    recent_sales_by_barber = []
    for barber in barbers:
        barber_today_sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date == today,
            Sale.status != 'deleted'
        ).order_by(Sale.created_at.desc()).limit(5).all()
        
        recent_sales_by_barber.append({
            'barber': barber,
            'sales': barber_today_sales
        })
    
    # Get week days for the dropdown
    week_days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        week_days.append({
            'name': day_date.strftime('%A'),
            'date': day_date.strftime('%Y-%m-%d')
        })
    
    today_str = today.strftime('%Y-%m-%d')
    selected_day = next((day for day in week_days if day['date'] == today_str), week_days[0])
    
    return render_template('dashboard.html',
                         today_total=today_total,
                         today_cash=today_cash,
                         today_momo=today_momo,
                         week_total=week_total,
                         week_expenses=week_expenses_total,
                         week_momo=week_momo,
                         week_advances=week_advances,
                         barber_performance=barber_performance,
                         recent_sales_by_barber=recent_sales_by_barber,
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
    
    barbers = Barber.query.filter_by(active=True).all()
    
    result = []
    for barber in barbers:
        # Exclude deleted sales
        sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date == target_date,
            Sale.status.in_(['active', 'updated'])
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