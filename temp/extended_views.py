"""Extended features module for the Mossie application."""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from functools import wraps
import datetime
import calendar
import json
import uuid
from . import models

# Create Blueprint
features = Blueprint('features', __name__, url_prefix='/features')

def login_required(view):
    """Decorator to verify a user is logged in."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

# ======== Settings Routes ========

@features.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        dark_mode = 'dark_mode' in request.form
        high_contrast = 'high_contrast' in request.form
        font_size = request.form.get('font_size', 'medium')
        
        # Update the user's settings
        models.update_user_settings(
            user_id, 
            dark_mode=dark_mode,
            high_contrast=high_contrast,
            font_size=font_size
        )
        
        # Update engagement points for customizing settings
        models.update_pet_engagement(user_id, 2)
        
        flash('Settings updated successfully!', 'success')
    
    # Get current settings
    settings = models.get_user_settings(user_id)
    
    return render_template('features/settings.html', settings=settings)

# ======== Journal Routes ========

@features.route('/journal')
@login_required
def journal_index():
    """Journal entries list page."""
    user_id = session.get('user_id')
    entries = models.get_journal_entries(user_id)
    return render_template('features/journal/index.html', entries=entries)

@features.route('/journal/create', methods=['GET', 'POST'])
@login_required
def journal_create():
    """Create new journal entry."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return render_template('features/journal/create.html')
            
        # Create journal entry
        entry_id = models.create_journal_entry(user_id, title, content)
        
        # Update engagement for creating a journal entry
        models.update_pet_engagement(user_id, 5)
        
        flash('Journal entry created successfully!', 'success')
        return redirect(url_for('features.journal_view', entry_id=entry_id))
    
    return render_template('features/journal/create.html')

@features.route('/journal/<entry_id>')
@login_required
def journal_view(entry_id):
    """View journal entry."""
    user_id = session.get('user_id')
    entry = models.get_journal_entry(user_id, entry_id)
    
    if not entry:
        abort(404)
    
    return render_template('features/journal/view.html', entry=entry)

@features.route('/journal/<entry_id>/edit', methods=['GET', 'POST'])
@login_required
def journal_edit(entry_id):
    """Edit journal entry."""
    user_id = session.get('user_id')
    entry = models.get_journal_entry(user_id, entry_id)
    
    if not entry:
        abort(404)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return render_template('features/journal/edit.html', entry=entry)
        
        # Update journal entry
        models.update_journal_entry(entry_id, title, content)
        
        # Update engagement for maintaining journal
        models.update_pet_engagement(user_id, 2)
        
        flash('Journal entry updated successfully!', 'success')
        return redirect(url_for('features.journal_view', entry_id=entry_id))
    
    return render_template('features/journal/edit.html', entry=entry)

@features.route('/journal/<entry_id>/delete', methods=['POST'])
@login_required
def journal_delete(entry_id):
    """Delete journal entry."""
    user_id = session.get('user_id')
    result = models.delete_journal_entry(user_id, entry_id)
    
    if result:
        flash('Journal entry deleted successfully!', 'success')
    else:
        flash('Error deleting journal entry', 'error')
    
    return redirect(url_for('features.journal_index'))

# ======== Pet Routes ========

@features.route('/pet')
@login_required
def pet_index():
    """Virtual pet page."""
    user_id = session.get('user_id')
    pet = models.get_user_pet(user_id)
    accessories = models.get_pet_accessories(user_id)
    
    return render_template('features/pet/index.html', 
                          pet=pet, 
                          accessories=accessories)

@features.route('/pet/interact', methods=['POST'])
@login_required
def pet_interact():
    """AJAX endpoint to interact with pet and increase engagement."""
    user_id = session.get('user_id')
    
    # Increase pet engagement points
    engagement = models.update_pet_engagement(user_id, 3)
    
    return jsonify({
        'success': True,
        'engagement': engagement
    })

@features.route('/pet/accessory/<accessory_id>', methods=['POST'])
@login_required
def toggle_accessory(accessory_id):
    """Toggle pet accessory equipped state."""
    user_id = session.get('user_id')
    
    # Toggle the accessory
    models.toggle_pet_accessory(user_id, accessory_id)
    
    # Update engagement for customizing pet
    models.update_pet_engagement(user_id, 1)
    
    return redirect(url_for('features.pet_index'))

# ======== Mood Routes ========

@features.route('/mood', methods=['GET', 'POST'])
@login_required
def mood_index():
    """Daily mood tracker page."""
    user_id = session.get('user_id')
    
    # Handle the mood submission
    if request.method == 'POST':
        mood = request.form.get('mood')
        date_str = request.form.get('date')
        
        if mood and date_str:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            models.set_mood(user_id, date, mood)
            
            # Update engagement for tracking mood
            models.update_pet_engagement(user_id, 3)
            
            flash('Mood recorded successfully!', 'success')
        else:
            flash('Please select a mood', 'error')
    
    # Get today's date and initialize weekly view dates
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=6)
    date_range = [(start_date + datetime.timedelta(days=i)) for i in range(7)]
    
    # Get user moods for the past week
    moods = models.get_weekly_moods(user_id, start_date, today)
    
    # Create a dict for easy lookup
    mood_dict = {mood['date']: mood['mood'] for mood in moods}
    
    return render_template('features/mood/index.html', 
                          today=today,
                          date_range=date_range,
                          moods=mood_dict)

@features.route('/mood/calendar')
@login_required
def mood_calendar():
    """Monthly mood calendar view."""
    user_id = session.get('user_id')
    
    # Get month and year from query params or use current month/year
    month = request.args.get('month', datetime.date.today().month, type=int)
    year = request.args.get('year', datetime.date.today().year, type=int)
    
    # Validate month and year
    if month < 1 or month > 12:
        month = datetime.date.today().month
    if year < 2000 or year > 2100:
        year = datetime.date.today().year
    
    # Create calendar for the month
    cal = calendar.monthcalendar(year, month)
    
    # Get month name and next/previous months
    month_name = calendar.month_name[month]
    
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
        
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1
    
    # Get all moods for the month
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
    monthly_moods = models.get_monthly_moods(user_id, start_date, end_date)
    
    # Create a dict for easy lookup
    mood_dict = {mood['date'].day: mood['mood'] for mood in monthly_moods}
    
    return render_template('features/mood/calendar.html',
                          year=year,
                          month=month,
                          month_name=month_name,
                          calendar=cal,
                          moods=mood_dict,
                          prev_month=prev_month,
                          prev_year=prev_year,
                          next_month=next_month,
                          next_year=next_year)
