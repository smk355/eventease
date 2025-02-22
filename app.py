from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  

uri = "mongodb+srv://smitkothari2023:BX492rFPjCPLkVXg@eventease.mf080.mongodb.net/?retryWrites=true&w=majority&appName=EventEase"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['EventEaseDB']
events_collection = db['events']
clubs_collection = db['clubs']
users_collection = db['users']
rsvp_collection = db['rsvp']

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = request.form
        user = users_collection.find_one({
            'email': user_data['email'],
            'password': user_data['password']  
        })
        if user:
            session['user_id'] = str(user['_id'])
            session['user_type'] = user['user_type']  
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
    if 'user_id' not in session or 'user_type' not in session:
        return redirect(url_for('login'))

    events = None
    if session['user_type'] == 'student':
        events = list(events_collection.find({
            'date': {'$gte': datetime.now().strftime('%Y-%m-%d')}
        }).sort('date', 1))
    elif session['user_type'] == 'club':
        events = list(events_collection.find({'created_by': session['user_id']}).sort('date', 1))
  
    for event in events:
        if isinstance(event['date'], str):
            try:
                date_obj = datetime.strptime(event['date'], '%Y-%m-%d')
                event['date'] = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                pass  
                
        if 'event_time' in event and event['event_time']:
            try:
                if isinstance(event['event_time'], str) and ':' in event['event_time']:
                    time_obj = datetime.strptime(event['event_time'], '%H:%M')
                    event['event_time'] = time_obj.strftime('%I:%M %p')
            except ValueError:
                pass  
        
        event['_id'] = str(event['_id'])
    
    return render_template('event.html', events=events)

# Event details route with DELETE support
@app.route('/event/<event_id>', methods=['GET', 'POST', 'DELETE'])
def event_details(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        event = events_collection.find_one({'_id': ObjectId(event_id)})
    except Exception:
        return "Invalid Event ID", 400  

    if not event:
        return "Event not found", 404
    
    event['id'] = str(event['_id'])
    
    if request.method == 'DELETE' and session['user_type'] == 'club':
        if event['created_by'] != session['user_id']:
            return "Unauthorized", 403
            
        # Delete all RSVPs for this event
        rsvp_collection.delete_many({'event_id': event_id})
        # Delete the event
        events_collection.delete_one({'_id': ObjectId(event_id)})
        return jsonify({"message": "Event deleted successfully"}), 200

    # Format date for display
    if isinstance(event['date'], str):
        try:
            date_obj = datetime.strptime(event['date'], '%Y-%m-%d')
            event['date'] = date_obj.strftime('%d-%m-%Y')
        except ValueError:
            pass  
            
    # Format time for display
    if 'event_time' in event and event['event_time']:
        try:
            if isinstance(event['event_time'], str) and ':' in event['event_time']:
                time_obj = datetime.strptime(event['event_time'], '%H:%M')
                event['event_time'] = time_obj.strftime('%I:%M %p')
        except ValueError:
            pass  

    if session['user_type'] == 'student':
        if request.method == 'POST':
            vit_student = request.form.get('vit_student')
            if vit_student == 'yes':
                registration_number = request.form.get('registration_number')
                college_name = 'VIT'
            elif vit_student == 'no':
                registration_number = '---'
                college_name = request.form.get('college_name')
            else:
                registration_number = None
                college_name = None

            rsvp_data = {
                'event_id': event_id,
                'student_id': session['user_id'],
                'name': request.form['name'],
                'email': request.form['email'],
                'vit_student': vit_student,
                'registration_number': registration_number,
                'college_name': college_name,
                'mobile': request.form['mobile'],
                'timestamp': datetime.now()
            }
            rsvp_collection.insert_one(rsvp_data)
            return render_template('event_details.html', event=event, message="RSVP Successful!")
        return render_template('event_details.html', event=event)
    elif session['user_type'] == 'club':
        participants = []
        rsvps = list(rsvp_collection.find({'event_id': event_id}))
        
        for rsvp in rsvps:
            student = users_collection.find_one({'_id': ObjectId(rsvp['student_id'])})
            if student:
                rsvp['user_email'] = student.get('email', 'Unknown')
            participants.append(rsvp)
            
        return render_template('event_participants.html', event=event, participants=participants)

# Create new event (only for clubs)
@app.route('/create_events', methods=['GET', 'POST'])
def create_events():
    if 'user_id' not in session or session['user_type'] != 'club':
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'date': request.form['date'],
            'event_time': request.form.get('time', ''),
            'location': request.form['location'],
            'category': request.form.get('category', 'academic'),
            'created_by': session['user_id'],
            'created_at': datetime.now()
        }
        events_collection.insert_one(event_data)
        return redirect(url_for('home'))

    return render_template('create_events.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
