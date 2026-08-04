import sqlite3
import bcrypt

DATABASE = 'house_predictor.db'

# ─── Helper Type Converters ───
def to_int(val):
    try:
        return int(str(val)) if val is not None else 0
    except:
        return 0

def to_float(val):
    try:
        return float(str(val)) if val is not None else 0.0
    except:
        return 0.0

# ─── Initialize Database ───
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            location        TEXT    NOT NULL,
            property_type   TEXT    NOT NULL,
            bedrooms        INTEGER NOT NULL,
            bathrooms       INTEGER NOT NULL,
            land_size       REAL    NOT NULL,
            house_size      REAL    NOT NULL,
            predicted_price REAL    NOT NULL,
            predicted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

# ─── Register New User ───
def register_user(username, email, password):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (username, email, hashed_password))

        conn.commit()
        conn.close()
        return True, "✅ Account created successfully!"

    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return False, "❌ Username already exists!"
        elif 'email' in str(e):
            return False, "❌ Email already registered!"
        return False, "❌ Registration failed!"

# ─── Login User ───
def login_user(username, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, password FROM users
        WHERE username = ?
    ''', (username,))

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False, None, "❌ Username not found!"

    if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
        return True, {'id': to_int(user[0]), 'username': str(user[1])}, "✅ Login successful!"
    else:
        return False, None, "❌ Incorrect password!"

# ─── Save Prediction ───
def save_prediction(user_id, location, property_type, bedrooms,
                    bathrooms, land_size, house_size, predicted_price):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO predictions (
            user_id, location, property_type, bedrooms,
            bathrooms, land_size, house_size, predicted_price
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        to_int(user_id),
        str(location),
        str(property_type),
        to_int(bedrooms),
        to_int(bathrooms),
        to_float(land_size),
        to_float(house_size),
        to_float(predicted_price)
    ))

    conn.commit()
    conn.close()

# ─── Get User Predictions ───
def get_user_predictions(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT location, property_type, bedrooms, bathrooms,
               land_size, house_size, predicted_price, predicted_at
        FROM predictions
        WHERE user_id = ?
        ORDER BY predicted_at DESC
    ''', (to_int(user_id),))

    rows = cursor.fetchall()
    conn.close()

    # Convert all values to correct types
    predictions = []
    for row in rows:
        predictions.append((
            str(row[0]),
            str(row[1]),
            to_int(row[2]),
            to_int(row[3]),
            to_float(row[4]),
            to_float(row[5]),
            to_float(row[6]),
            str(row[7])
        ))
    return predictions

# ─── Get User Stats ───
def get_user_stats(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*)             as total_predictions,
            AVG(predicted_price) as avg_price,
            MAX(predicted_price) as max_price,
            MIN(predicted_price) as min_price
        FROM predictions
        WHERE user_id = ?
    ''', (to_int(user_id),))

    row = cursor.fetchone()
    conn.close()

    return (
        to_int(row[0]),
        to_float(row[1]),
        to_float(row[2]),
        to_float(row[3])
    )

# ─── Admin: Get All Users ───
def get_all_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, email, created_at
        FROM users
        ORDER BY created_at DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    users = []
    for row in rows:
        users.append((
            to_int(row[0]),
            str(row[1]),
            str(row[2]),
            str(row[3])
        ))
    return users

# ─── Admin: Get All Predictions ───
def get_all_predictions():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.username, p.location, p.property_type,
               p.bedrooms, p.bathrooms, p.land_size,
               p.house_size, p.predicted_price, p.predicted_at
        FROM predictions p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.predicted_at DESC
    ''')

    rows = cursor.fetchall()
    conn.close()

    predictions = []
    for row in rows:
        predictions.append((
            str(row[0]),
            str(row[1]),
            str(row[2]),
            to_int(row[3]),
            to_int(row[4]),
            to_float(row[5]),
            to_float(row[6]),
            to_float(row[7]),
            str(row[8])
        ))
    return predictions

# ─── Admin: Get Overall Stats ───
def get_overall_stats():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM predictions')
    total_predictions = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(predicted_price) FROM predictions')
    avg_price = cursor.fetchone()[0]

    cursor.execute('SELECT MAX(predicted_price) FROM predictions')
    max_price = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(predicted_price) FROM predictions')
    min_price = cursor.fetchone()[0]

    conn.close()

    return {
        'total_users':       to_int(total_users),
        'total_predictions': to_int(total_predictions),
        'avg_price':         to_float(avg_price),
        'max_price':         to_float(max_price),
        'min_price':         to_float(min_price)
    }

# ─── Admin: Delete User ───
def delete_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM predictions WHERE user_id = ?', (to_int(user_id),))
    cursor.execute('DELETE FROM users WHERE id = ?', (to_int(user_id),))
    conn.commit()
    conn.close()