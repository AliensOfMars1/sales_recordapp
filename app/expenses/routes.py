from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.expenses import expenses_bp
from app.forms import ExpenseForm
from app.models import Expense
from datetime import datetime, timedelta

@expenses_bp.route('/', methods=['GET', 'POST'])
@login_required
def manage_expenses():
    form = ExpenseForm()
    
    if form.validate_on_submit():
        expense = Expense(
            title=form.title.data,
            amount=form.amount.data,
            category=form.category.data,
            expense_date=form.expense_date.data,
            notes=form.notes.data
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense recorded successfully!', 'success')
        return redirect(url_for('expenses.manage_expenses'))
    
    # Generate weeks for dropdown (last 12 weeks)
    weeks = []
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    
    for i in range(12):
        week_start = current_week_start - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        
        weeks.append({
            'start_date': week_start.strftime('%Y-%m-%d'),
            'end_date': week_end.strftime('%Y-%m-%d'),
            'label': f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"
        })
    
    selected_week = weeks[0]
    
    return render_template('expenses/expenses.html', 
                         form=form, 
                         weeks=weeks,
                         selected_week_label=selected_week['label'],
                         selected_week_start=selected_week['start_date'],
                         selected_week_end=selected_week['end_date'])


@expenses_bp.route('/get-by-week')
@login_required
def get_expenses_by_week():
    """API endpoint to get expenses for a specific week"""
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    if not start_date_str or not end_date_str:
        return jsonify({'expenses': [], 'total': 0})
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    expenses = Expense.query.filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).order_by(Expense.expense_date.desc()).all()
    
    result = []
    for expense in expenses:
        result.append({
            'id': expense.id,
            'title': expense.title,
            'amount': expense.amount,
            'category': expense.category.capitalize(),
            'date': expense.expense_date.strftime('%Y-%m-%d'),
            'notes': expense.notes
        })
    
    total = sum(e.amount for e in expenses)
    
    return jsonify({'expenses': result, 'total': total})


@expenses_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    if request.method == 'POST':
        expense.title = request.form.get('title')
        expense.amount = float(request.form.get('amount'))
        expense.category = request.form.get('category')
        expense.expense_date = datetime.strptime(request.form.get('expense_date'), '%Y-%m-%d').date()
        expense.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses.manage_expenses'))
    
    return render_template('expenses/edit_expense.html', expense=expense)


@expenses_bp.route('/delete/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses.manage_expenses'))