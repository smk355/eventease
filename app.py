from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for sessions

# MongoDB connection
uri = "mongodb+srv://smitkothari2023:BX492rFPjCPLkVXg@eventease.mf080.mongodb.net/?retryWrites=true&w=majority&appName=EventEase"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['EventEaseDB']
events_collection = db['events']
clubs_collection = db['clubs']
users_collection = db['users']
rsvp_collection = db['rsvp']

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = request.form
        user = users_collection.find_one({
            'email': user_data['email'],
            'password': user_data['password']  # For production, use proper password hashing
        })
        if user:
            session['user_id'] = str(user['_id'])
            session['user_type'] = user['user_type']  # 'student' or 'club'
            return redirect(url_for('home'))
        return render_template('login.html', message="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = {
            'email': request.form['email'],
            'password': request.form['password'],
            'user_type': request.form['user_type']
        }
        if users_collection.find_one({'email': user_data['email']}):
            return render_template('register.html', message="Email already registered")

        # Ensure user_type is valid ('student' or 'club')
        if user_data['user_type'] not in ['student', 'club']:
            return render_template('register.html', message="Invalid user type")

        users_collection.insert_one(user_data)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Home route
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'user_type' not in session:
        return redirect(url_for('login'))

    # Display different events based on user type
    events = None
    if session['user_type'] == 'student':
        events = list(events_collection.find({
            'date': {'$gte': datetime.now().strftime('%Y-%m-%d')}
        }))
    elif session['user_type'] == 'club':
        events = list(events_collection.find({'created_by': session['user_id']}))
    
    return render_template('event.html', events=events)

# Event details route
@app.route('/event/<event_id>', methods=['GET', 'POST'])
def event_details(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if not event:
        return "Event not found", 404

    if session['user_type'] == 'student':
        if request.method == 'POST':
            rsvp_data = {
                'event_id': event_id,
                'student_id': session['user_id'],
                'name': request.form['name'],
                'email': request.form['email'],
                'mobile': request.form['mobile'],
                'timestamp': datetime.now()
            }
            rsvp_collection.insert_one(rsvp_data)
            return render_template('event_details.html', event=event, message="RSVP successful!")
        return render_template('event_details.html', event=event)
    elif session['user_type'] == 'club':
        participants = list(rsvp_collection.find({'event_id': event_id}))
        return render_template('event_participants.html', event=event, participants=participants)

# Create new event (only for clubs)
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session or session['user_type'] != 'club':
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'date': request.form['date'],
            'location': request.form['location'],
            'created_by': session['user_id'],
            'created_at': datetime.now()
        }
        events_collection.insert_one(event_data)
        return redirect(url_for('home'))

    return render_template('createevent.html')

if __name__ == '__main__':
    app.run(debug=True)