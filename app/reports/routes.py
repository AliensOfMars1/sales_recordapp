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
    # Get any date in the week from user, or default to today
    date_str = request.args.get('date')
    
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.now().date()
    
    # Calculate the Monday of the week containing selected_date
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Debug print
    print(f"Selected date: {selected_date}, Week: {week_start} to {week_end}")
    
    barbers = Barber.query.filter_by(active=True).all()
    weekly_data = []
    
    for barber in barbers:
        # Get sales for the full week (Monday to Sunday)
        weekly_sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date >= week_start,
            Sale.sale_date <= week_end
        ).all()
        total_sales = sum(s.amount for s in weekly_sales)
        
        commission = total_sales / 3
        
        # FIXED: Get advances using remaining_balance, not full amount
        weekly_advances = BarberAdvance.query.filter(
            BarberAdvance.barber_id == barber.id,
            BarberAdvance.settled == False,
            BarberAdvance.advance_date >= week_start,
            BarberAdvance.advance_date <= week_end
        ).all()
        
        # Use remaining_balance for each advance
        total_advances = sum(a.remaining_balance for a in weekly_advances)
        
        net_payout = commission - total_advances
        
        weekly_data.append({
            'barber': barber,
            'sales': total_sales,
            'commission': commission,
            'advances': total_advances,
            'net_payout': net_payout
        })
    
    # Sort by sales descending
    weekly_data.sort(key=lambda x: x['sales'], reverse=True)
    
    return render_template('reports/weekly_commission.html', 
                         weekly_data=weekly_data,
                         week_start=week_start,
                         week_end=week_end,
                         selected_date=selected_date)


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