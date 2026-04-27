from flask import render_template, request
from flask_login import login_required
from app.reports import reports_bp
from app.models import Sale, Expense, Barber, BarberAdvance
from datetime import datetime, timedelta
from sqlalchemy import func

@reports_bp.route('/daily-sales')
@login_required
def daily_sales():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    sales = Sale.query.filter(func.date(Sale.sale_date) == report_date).all()
    total_sales = sum(s.amount for s in sales)
    cash_sales = sum(s.amount for s in sales if s.payment_method == 'cash')
    momo_sales = sum(s.amount for s in sales if s.payment_method == 'momo')
    
    return render_template('reports/daily_sales.html', 
                         sales=sales, 
                         date=report_date,
                         total=total_sales,
                         cash=cash_sales,
                         momo=momo_sales)

@reports_bp.route('/weekly-commission')
@login_required
def weekly_commission():
    # Get week start date or default to current week
    week_start_str = request.args.get('week_start')
    if week_start_str:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
    else:
        week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    
    week_end = week_start + timedelta(days=6)
    
    barbers = Barber.query.filter_by(active=True).all()
    weekly_data = []
    
    for barber in barbers:
        weekly_sales = barber.total_sales(week_start, week_end)
        commission = weekly_sales / 3
        advances = barber.total_advances(week_start, week_end)
        net_payout = commission - advances
        
        weekly_data.append({
            'barber': barber,
            'sales': weekly_sales,
            'commission': commission,
            'advances': advances,
            'net_payout': net_payout
        })
    
    return render_template('reports/weekly_commission.html', 
                         weekly_data=weekly_data,
                         week_start=week_start,
                         week_end=week_end)

@reports_bp.route('/expenses-report')
@login_required
def expenses_report():
    # Default to current week if no dates provided
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Expense.query
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Expense.expense_date >= start)
    else:
        # Default to start of current week
        start = week_start
        start_date = week_start.strftime('%Y-%m-%d')
        query = query.filter(Expense.expense_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Expense.expense_date <= end)
    else:
        # Default to end of current week
        end = week_end
        end_date = week_end.strftime('%Y-%m-%d')
        query = query.filter(Expense.expense_date <= end)
    
    expenses = query.order_by(Expense.expense_date.desc()).all()
    total = sum(e.amount for e in expenses)
    by_category = {}
    for expense in expenses:
        by_category[expense.category] = by_category.get(expense.category, 0) + expense.amount
    
    return render_template('reports/expenses_report.html', 
                         expenses=expenses,
                         total=total,
                         by_category=by_category,
                         start_date=start_date,
                         end_date=end_date)