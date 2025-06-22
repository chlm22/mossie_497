"""Mossie extended features blueprint."""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
import temp.models as models
from functools import wraps
import datetime

# Create the blueprint
features = Blueprint('features', __name__, url_prefix='/features')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ======== Settings Routes ========

@features.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        # Update user settings
        dark_mode = 1 if request.form.get('dark_mode') else 0
        high_contrast = 1 if request.form.get('high_contrast') else 0
        font_size = request.form.get('font_size', 'medium')
        
        models.update_user_settings(user_id, dark_mode, high_contrast, font_size)
        flash('Settings updated successfully!', 'success')
        
    # Get current settings
    user_settings = models.get_user_settings(user_id)
    
    return render_template('features/settings.html', settings=user_settings)

# ======== Journal Routes ========

@features.route('/journal')
@login_required
def journal_list():
    """Journal entries list page."""
    user_id = session.get('user_id')
    entries = models.get_journal_entries(user_id)
    
    return render_template('features/journal_list.html', entries=entries)

@features.route('/journal/new', methods=['GET', 'POST'])
@login_required
def journal_new():
    """Create new journal entry."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required!', 'error')
        else:
            entry_id = models.create_journal_entry(user_id, title, content)
            flash('Journal entry created successfully!', 'success')
            return redirect(url_for('features.journal_view', entry_id=entry_id))
    
    return render_template('features/journal_edit.html', entry=None)

@features.route('/journal/<entry_id>')
@login_required
def journal_view(entry_id):
    """View a journal entry."""
    user_id = session.get('user_id')
    entry = models.get_journal_entry(user_id, entry_id)
    
    if not entry:
        flash('Journal entry not found!', 'error')
        return redirect(url_for('features.journal_list'))
    
    return render_template('features/journal_view.html', entry=entry)

@features.route('/journal/<entry_id>/edit', methods=['GET', 'POST'])
@login_required
def journal_edit(entry_id):
    """Edit a journal entry."""
    user_id = session.get('user_id')
    entry = models.get_journal_entry(user_id, entry_id)
    
    if not entry:
        flash('Journal entry not found!', 'error')
        return redirect(url_for('features.journal_list'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required!', 'error')
        else:
            models.update_journal_entry(entry_id, title, content)
            flash('Journal entry updated successfully!', 'success')
            return redirect(url_for('features.journal_view', entry_id=entry_id))
    
    return render_template('features/journal_edit.html', entry=entry)

@features.route('/journal/<entry_id>/delete', methods=['POST'])
@login_required
def journal_delete(entry_id):
    """Delete a journal entry."""
    user_id = session.get('user_id')
    
    if models.delete_journal_entry(user_id, entry_id):
        flash('Journal entry deleted successfully!', 'success')
    else:
        flash('Failed to delete journal entry!', 'error')
    
    return redirect(url_for('features.journal_list'))

# ======== Mood Tracking Routes ========

@features.route('/mood', methods=['GET', 'POST'])
@login_required
def mood_tracking():
    """Mood tracking page."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        mood_value = int(request.form.get('mood_value', 3))
        mood_note = request.form.get('mood_note', '')
        
        models.set_mood(user_id, mood_value, mood_note)
        flash('Mood recorded successfully!', 'success')
    
    # Get weekly moods for chart
    weekly_moods = models.get_weekly_moods(user_id)
    
    # Get monthly moods for calendar view
    today = datetime.datetime.now()
    monthly_moods = models.get_monthly_moods(user_id, today.year, today.month)
    
    return render_template('features/mood_tracking.html', 
                          weekly_moods=weekly_moods,
                          monthly_moods=monthly_moods,
                          today=today,
                          datetime=datetime)

# ======== Pet Routes ========

@features.route('/pet')
@login_required
def pet():
    """Virtual pet page."""
    user_id = session.get('user_id')
    pet_data = models.get_user_pet(user_id)
    accessories = models.get_pet_accessories(user_id)
    
    # Reset pet play mode if it was set
    play_mode = session.pop('pet_play_mode', False)
    
    return render_template('features/pet.html', pet=pet_data, accessories=accessories, play_mode=play_mode)

@features.route('/pet/interact', methods=['POST'])
@login_required
def pet_interact():
    """Interact with pet."""
    user_id = session.get('user_id')
    
    # Update pet engagement
    updated_pet = models.update_pet_engagement(user_id)
    
    # Toggle pet play mode in session
    session['pet_play_mode'] = True
    
    # Set a timer to reset play mode after 5 seconds
    # Since we can't use setTimeout in Flask, we'll use a redirect with a flash message
    flash('Your pet is happy to play with you!', 'success')
    
    return redirect(url_for('features.pet'))

@features.route('/pet/accessory/<accessory_id>', methods=['POST'])
@login_required
def toggle_accessory(accessory_id):
    """Toggle pet accessory."""
    user_id = session.get('user_id')
    
    models.toggle_pet_accessory(user_id, accessory_id)
    
    return redirect(url_for('features.pet'))
