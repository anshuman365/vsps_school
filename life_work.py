from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import wordnet, stopwords
from nltk import ne_chunk, pos_tag
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import FreqDist
import numpy
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
import os
import json
import sqlite3
from datetime import timedelta
from authlib.integrations.flask_client import OAuth
import random

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_unique_secret_key'  # Replace with a secure key

# Initialize SocketIO
socketio = SocketIO(app)

# Folder configurations
UPLOAD_FOLDER = 'uploads'
UPLOAD_FOLDER1 = '/storage/emulated/0/ylog/static/music'
MUSIC_FOLDER = '/storage/emulated/0/VidMate/download'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER1'] = UPLOAD_FOLDER1
# OAuth Configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'}
)
rooms={}
# SQLite database initialization
conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room TEXT,
    username TEXT,
    message TEXT
)
''')
conn.commit()

# JSON database file
USER_DB_FILE = 'users.json'

# Ensure the JSON file exists
if not os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, 'w') as f:
        json.dump({}, f)

# Helper functions to read/write user data
def load_users():
    with open(USER_DB_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f)

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users:
            flash("Username already exists. Try a different one.")
            return redirect(url_for('signup'))

        users[username] = password
        save_users(users)
        flash("Signup successful. Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

app.permanent_session_lifetime = timedelta(days=30)  # Session lasts for 30 days

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users and users[username] == password:
            session.permanent = True  # Make the session permanent
            session['username'] = username
            flash("Login successful!")
            return redirect(url_for('dashboard'))
        flash("Invalid username or password.")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please log in to access the dashboard.")
        return redirect(url_for('login'))
    return render_template('main.html', username=session['username'])

@app.route('/drive', methods=['GET', 'POST'])
def drive():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part in the request!")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No file selected for upload!")
            return redirect(request.url)
        
        # Validate file extension
        allowed_extensions = ('.mp3', '.wav', '.txt', '.pdf', '.jpg', '.png', '.mp4', '.mkv', '.avi','.py','.pptx','.docx','.html')
        if not file.filename.lower().endswith(allowed_extensions):
            flash("Invalid file type! Only specific formats are allowed.")
            return redirect(request.url)
        
        # Save file to UPLOAD_FOLDER
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        if file.filename.endswith(('.mp3', '.wav')) :
            print('Its reached')
            file.save(os.path.join(app.config['UPLOAD_FOLDER1'], file.filename))
        flash(f"File {file.filename} uploaded successfully!")

    # List files dynamically from UPLOAD_FOLDER
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    categorized_files = {
        'video': [f for f in files if f.lower().endswith(('.mp4', '.mkv', '.avi'))],
        'music': [f for f in files if f.lower().endswith(('.mp3', '.wav'))],
        'image': [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
        'pdf': [f for f in files if f.lower().endswith('.pdf')],
        'text': [f for f in files if f.lower().endswith('.txt')],
        'python': [f for f in files if f.lower().endswith('.py')],
        'html': [f for f in files if f.lower().endswith('.html')],
        'ppt': [f for f in files if f.lower().endswith('.pptx')],
        'doc': [f for f in files if f.lower().endswith('.docx')],
        'other': [f for f in files if not f.lower().endswith(('.mp4', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.pdf', '.txt',))]
    }


    return render_template('drive.html', categorized_files=categorized_files)

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/open/<filename>')
def open_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        flash(f"File {filename} not found.")
        return redirect(url_for('drive'))
        
        
#---------------------------------------music zone---------------------------------------#
"""
@app.route('/music/<path:filename>')
def serve_music(filename):
    file_path = os.path.join("/storage/emulated/0/VidMate/download/", filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return f"File {filename} not found.", 404 
        """

connected_users = []  # To store connected users

MUSIC_FOLDER = os.path.join(os.getcwd(), 'static', 'music')
roomsm = {}  # Store room details (player and listeners)

@app.route('/sync')
def index():
    return render_template('index.html')

@app.route('/room', methods=['POST'])
def room():
    username = request.form.get('username')
    role = request.form.get('role')
    room_name = request.form.get('room_name')

    if not username or not role or not room_name:
        flash('All fields are required!')
        return redirect(url_for('index'))

    # Initialize room if it doesn't exist
    if room_name not in roomsm:
        roomsm[room_name] = {'players': [], 'listeners': []}

    if role == 'Player' and len(roomsm[room_name]['players']) == 0:
        roomsm[room_name]['players'].append(username)
    elif role == 'Listener':
        roomsm[room_name]['listeners'].append(username)
    else:
        flash('Only one player allowed per room!')
        return redirect(url_for('index'))

    return render_template('room2.html', room_name=room_name, username=username, role=role, files=os.listdir(MUSIC_FOLDER))

@app.route('/music/<filename>')
def serve_music(filename):
    """Serve music files for playback"""
    return jsonify({'url': url_for('static', filename=f'music/{filename}')})

# Socket.IO Events
@socketio.on('join_room')
def handle_join(data):
    username = data['username']
    room_name = data['room']
    join_room(room_name)
    emit('user_joined', {'username': username}, room=room_name)

@socketio.on('play_music')
def play_music(data):
    """Broadcast music play event to all users in the room"""
    room_name = data['room']
    music_file = data['music_file']
    emit('play_music', {'music_file': music_file, 'action': 'play'}, room=room_name)

@socketio.on('pause_music')
def pause_music(data):
    """Broadcast music pause event to all users in the room"""
    room_name = data['room']
    emit('pause_music', {'action': 'pause'}, room=room_name)

@socketio.on('seek_music')
def seek_music(data):
    """Broadcast seek event to all users in the room"""
    room_name = data['room']
    seek_time = data['seek_time']
    emit('seek_music', {'seek_time': seek_time}, room=room_name)

@socketio.on('disconnect')
def handle_disconnect():
    print("User disconnected")
    
#---------------------------------------What'sChat---------------------------------------#
        
@app.route('/whatschat', methods=['GET', 'POST'])
def whatschat():
    return render_template('whatschat.html')

@socketio.on('join_room')
def handle_join(data):
    username = data.get('username')
    room = data.get('room')
    join_room(room)
    if room not in rooms:
        rooms[room] = []
    if username not in rooms[room]:
        rooms[room].append(username)
    emit('user_joined', {'room': room, 'users': rooms[room]}, room=room)

@socketio.on('send_message')
def handle_message(data):
    room = data.get('room')
    message = data.get('message')
    username = data.get('username')
    cursor.execute("INSERT INTO chat (room, username, message) VALUES (?, ?, ?)", (room, username, message))
    conn.commit()
    emit('new_message', {'username': username, 'message': message}, room=room)



# ---------------------------------------Need Feedback Page--------------------------#
@app.route("/need", methods=["GET", "POST"])
def need():
    if request.method == "POST":
        feedback = request.form.get("feedback")
        f=open('feedback.txt','a')
        feed=feedback+"\n"
        f.write(feed)
        print(feedback)
        f.close()
        return f"Thank you for your feedback: {feedback}"
        
    return render_template("need.html")
    
# Error Handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
    

    
#-----------------------------------------AI work Zone#-----------------------------------------#

# Initialize Flask app


# NLTK Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# NLTK functionalities
def word_tokenize_text(text):
    return word_tokenize(text)

def sentence_tokenize_text(text):
    return sent_tokenize(text)

def analyze_word_frequency(text):
    words = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.lower() not in stop_words]
    freq_dist = FreqDist(filtered_words)
    return dict(freq_dist)

def find_synonyms(word):
    synonyms = wordnet.synsets(word)
    return [syn.lemmas()[0].name() for syn in synonyms]

def named_entity_recognition(text):
    words = word_tokenize(text)
    tagged = pos_tag(words)
    named_entities = ne_chunk(tagged)
    return str(named_entities)

def sentiment_analysis(text):
    return sia.polarity_scores(text)

# AI Zone route
@app.route('/AI_Zone', methods=["GET", "POST"])
def ai_zone():
    if request.method == 'POST':
        data = request.json
        choice = data.get('choice')
        text = data.get('text', '')
        word = data.get('word', '')

        if choice == '1':
            result = word_tokenize_text(text)
        elif choice == '2':
            result = sentence_tokenize_text(text)
        elif choice == '3':
            result = analyze_word_frequency(text)
        elif choice == '4':
            result = find_synonyms(word)
        elif choice == '5':
            result = named_entity_recognition(text)
        elif choice == '6':
            result = sentiment_analysis(text)
        else:
            result = {"error": "Invalid choice"}

        return jsonify(result)  # Return JSON response for AJAX requests
    return render_template('AI_Zone.html')  # Render template for GET requests


#--------------------------------------AI work Zone End-------------------------------------#

games = {}
global_leaderboard = []

def check_winner(board):
    for i in range(3):
        if board[i*3] == board[i*3+1] == board[i*3+2] and board[i*3] != '':
            return board[i*3], [(i*3), (i*3+1), (i*3+2)]
        if board[i] == board[i+3] == board[i+6] and board[i] != '':
            return board[i], [i, i+3, i+6]
    if board[0] == board[4] == board[8] and board[0] != '':
        return board[0], [0, 4, 8]
    if board[2] == board[4] == board[6] and board[2] != '':
        return board[2], [2, 4, 6]
    return None, []

def ai_move(board):
    empty_cells = [i for i in range(len(board)) if board[i] == '']
    return random.choice(empty_cells) if empty_cells else None

@app.route('/game')
def game():
    return render_template('index13.html')

@socketio.on('join')
def on_join(data):
    room = data['room']
    mode = data['mode']
    join_room(room)
    if room not in games:
        games[room] = {
            'board': [''] * 9,
            'turn': 'X',
            'mode': mode,
            'players': [],
            'spectators': [],
            'scores': {'X': 0, 'O': 0}
        }
    if mode == 'single' or len(games[room]['players']) < 2:
        games[room]['players'].append(request.sid)
    else:
        games[room]['spectators'].append(request.sid)
    emit('update_board', games[room], room=request.sid)

@socketio.on('move')
def on_move(data):
    room = data['room']
    index = data['index']
    game = games[room]

    if game['board'][index] == '' and request.sid in game['players']:
        game['board'][index] = game['turn']
        winner, win_indices = check_winner(game['board'])

        if winner:
            game['scores'][winner] += 1
            update_global_leaderboard(room, game['players'], winner, game['scores'][winner])
            emit('winner', {'winner': winner, 'win_indices': win_indices}, room=room)
            game['board'] = [''] * 9
        elif '' not in game['board']:
            emit('draw', {}, room=room)
            update_global_leaderboard(room, game['players'], 'Draw', 0)
            game['board'] = [''] * 9
        else:
            game['turn'] = 'O' if game['turn'] == 'X' else 'X'

            if game['mode'] == 'single' and game['turn'] == 'O':
                ai_index = ai_move(game['board'])
                if ai_index is not None:
                    game['board'][ai_index] = 'O'
                    winner, win_indices = check_winner(game['board'])
                    if winner:
                        game['scores']['O'] += 1
                        update_global_leaderboard(room, game['players'], 'O', game['scores']['O'])
                        emit('winner', {'winner': winner, 'win_indices': win_indices}, room=room)
                        game['board'] = [''] * 9
                    elif '' not in game['board']:
                        emit('draw', {}, room=room)
                        update_global_leaderboard(room, game['players'], 'Draw', 0)
                        game['board'] = [''] * 9
                    else:
                        game['turn'] = 'X'
            emit('update_board', game, room=room)

@socketio.on('reset')
def on_reset(data):
    room = data['room']
    games[room]['board'] = [''] * 9
    emit('update_board', games[room], room=room)

@socketio.on('get_leaderboards')
def on_get_leaderboards(data):
    room = data['room']
    local_leaderboard = games[room]['scores']
    emit('leaderboards', {'local': local_leaderboard, 'global': global_leaderboard}, room=request.sid)

def update_global_leaderboard(room, players, player, score):
    # Check if the room exists in the global leaderboard
    global_index = next((index for (index, entry) in enumerate(global_leaderboard) if entry['Room'] == room), None)

    if global_index is not None:
        # Update the existing entry for that room
        global_leaderboard[global_index]['Player1'] = players[0]
        global_leaderboard[global_index]['Player2'] = players[1] if len(players) > 1 else 'AI'
        global_leaderboard[global_index]['Score1'] = score if player == 'X' else global_leaderboard[global_index]['Score1']
        global_leaderboard[global_index]['Score2'] = score if player == 'O' else global_leaderboard[global_index]['Score2']
    else:
        # Add a new entry for the room
        global_leaderboard.append({
            'Room': room,
            'Player1': players[0],
            'Player2': players[1] if len(players) > 1 else 'AI',
            'Score1': score if player == 'X' else 0,
            'Score2': score if player == 'O' else 0
        })
    
    # Sort the leaderboard by the highest score of Player 1 and Player 2 combined
    global_leaderboard.sort(key=lambda x: max(x['Score1'], x['Score2']), reverse=True)



# Main Execution
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)