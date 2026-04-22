from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.expenses import expenses_bp
from app.forms import ExpenseForm
from app.models import Expense
from datetime import datetime

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
    
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    total_expenses = sum(e.amount for e in expenses)
    return render_template('expenses/expenses.html', form=form, expenses=expenses, total=total_expenses)

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