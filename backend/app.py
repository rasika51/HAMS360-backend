import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor  # Important fix
import bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hospital_inventory'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
mysql = MySQL(app)


# Routes
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        required_fields = ['firstName', 'lastName', 'dateOfBirth', 'email', 
                         'position', 'idNumber', 'phoneNumber', 'password']
        
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400

        cursor = mysql.connection.cursor()
        
        # Check if email or ID number already exists
        cursor.execute("SELECT * FROM userss WHERE email = %s OR id_number = %s", 
                     (data['email'], data['idNumber']))
        existing_user = cursor.fetchone()

        if existing_user:
            conflict = 'Email' if existing_user['email'] == data['email'] else 'ID Number'
            return jsonify({'message': f'{conflict} already exists!'}), 409

        # Hash password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        # Insert new user
        cursor.execute("""
            INSERT INTO userss 
            (first_name, last_name, date_of_birth, email, position, id_number, phone_number, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['firstName'],
            data['lastName'],
            data['dateOfBirth'],
            data['email'],
            data['position'],
            data['idNumber'],
            data['phoneNumber'],
            hashed_password
        ))

        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'User registered successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM userss WHERE email = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid username or password!'}), 401

        stored_password = user[2].encode('utf-8')  # Access by index
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return jsonify({'status': 'success', 'message': 'Login successful!'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password!'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

// Resource Management
@app.route('/api/resources', methods=['GET'])
def get_resources():
    cursor = mysql.connection.cursor(cursorclass=DictCursor)  # Fix here
    cursor.execute('SELECT * FROM resources')
    resources = cursor.fetchall()
    cursor.close()
    return jsonify(resources)


@app.route('/api/resources', methods=['POST'])
def add_resource():
    name = request.form.get('name')
    section = request.form.get('section')
    file = request.files.get('image')

    if not name or not section or not file:
        return jsonify({'error': 'Missing required fields'}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO resources (name, section, image_path) VALUES (%s, %s, %s)',
            (name, section, filename)
        )
        mysql.connection.commit()
        resource_id = cursor.lastrowid
        cursor.close()

        return jsonify({'id': resource_id, 'name': name, 'section': section, 'image_path': filename}), 201
    else:
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/resources/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    name = request.form.get('name')
    section = request.form.get('section')
    file = request.files.get('image')

    cursor = mysql.connection.cursor(cursorclass=DictCursor)  # Fix here
    cursor.execute('SELECT * FROM resources WHERE id = %s', (resource_id,))
    resource = cursor.fetchone()

    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    filename = resource['image_path']  # Now safe with DictCursor

    if file and allowed_file(file.filename):
        old_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(old_file):
            os.remove(old_file)

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    update_cursor = mysql.connection.cursor()
    update_cursor.execute(
        'UPDATE resources SET name = %s, section = %s, image_path = %s WHERE id = %s',
        (name or resource['name'], section or resource['section'], filename, resource_id)
    )
    mysql.connection.commit()
    update_cursor.close()

    return jsonify({'message': 'Resource updated successfully'})


@app.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)  # Fix here
    cursor.execute('SELECT * FROM resources WHERE id = %s', (resource_id,))
    resource = cursor.fetchone()

    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], resource['image_path'])
    if os.path.exists(file_path):
        os.remove(file_path)

    delete_cursor = mysql.connection.cursor()
    delete_cursor.execute('DELETE FROM resources WHERE id = %s', (resource_id,))
    mysql.connection.commit()
    delete_cursor.close()

    return jsonify({'message': 'Resource deleted successfully'})


# Asset Management Endpoints
@app.route('/api/resources/<int:resource_id>/assets', methods=['GET'])
def get_assets(resource_id):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)  # Fix here
    cursor.execute('SELECT * FROM assets WHERE resource_id = %s', (resource_id,))
    assets = cursor.fetchall()
    cursor.close()
    return jsonify(assets)


@app.route('/api/assets/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    data = request.get_json()
    name = data.get('name')
    stock_count = data.get('stockCount')
    deduction = data.get('deduction')
    date = data.get('date')

    if not all([name, stock_count, deduction, date]):
        return jsonify({'error': 'Missing required fields'}), 400

    cursor = mysql.connection.cursor()
    cursor.execute(
        'UPDATE assets SET name = %s, stock_count = %s, deduction = %s, date = %s WHERE id = %s',
        (name, stock_count, deduction, date, asset_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Asset updated successfully'})


@app.route('/api/resources/<int:resource_id>/assets', methods=['POST'])
def add_asset(resource_id):
    data = request.get_json()
    name = data.get('name')
    stock_count = data.get('stockCount')
    deduction = data.get('deduction')
    date = data.get('date')

    if not all([name, stock_count, deduction, date]):
        return jsonify({'error': 'Missing required fields'}), 400

    cursor = mysql.connection.cursor()
    cursor.execute(
        'INSERT INTO assets (resource_id, name, stock_count, deduction, date) VALUES (%s, %s, %s, %s, %s)',
        (resource_id, name, stock_count, deduction, date)
    )
    mysql.connection.commit()
    asset_id = cursor.lastrowid
    cursor.close()
    return jsonify(
        {'id': asset_id, 'resource_id': resource_id, 'name': name, 'stockCount': stock_count, 'deduction': deduction,
         'date': date}), 201


@app.route('/api/assets/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)  # Fix here
    cursor.execute('SELECT * FROM assets WHERE id = %s', (asset_id,))
    asset = cursor.fetchone()

    if not asset:
        return jsonify({'error': 'Asset not found'}), 404

    insert_cursor = mysql.connection.cursor()
    insert_cursor.execute(
        'INSERT INTO deleted_assets (id, resource_id, name, stock_count, deduction, date) VALUES (%s, %s, %s, %s, %s, %s)',
        (asset['id'], asset['resource_id'], asset['name'], asset['stock_count'], asset['deduction'], asset['date'])
    )

    delete_cursor = mysql.connection.cursor()
    delete_cursor.execute('DELETE FROM assets WHERE id = %s', (asset_id,))
    mysql.connection.commit()
    insert_cursor.close()
    delete_cursor.close()

    return jsonify({'message': 'Asset moved to deleted_assets table'})


if __name__ == '__main__':
    app.run(debug=True)
