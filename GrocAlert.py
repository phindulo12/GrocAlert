from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from datetime import datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

NUTRITIONIX_APP_ID = '6519ad8d'  # Replace with your Nutritionix App ID
NUTRITIONIX_API_KEY = 'd4af496650cab7aa27bea88c6cf732a2'

CATEGORY_EXPIRY_DAYS = {
    "fruit": 5,
    "vegetable": 7,
    "opened": 3,
    "dairy": 7,
    "canned": 180,
    "other": 30
}

users = {}
user_groceries = {}  # key = username, value = dict of groceries


class User(UserMixin):
    def __init__(self, id, username, password, age=None, gender=None, image=None):
        self.id = id
        self.username = username
        self.password = password
        self.age = age
        self.gender = gender
        self.image = image

    def check_password(self, password):
        return check_password_hash(self.password, password)


@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
@login_required
def index():
    return render_template('index.html', categories=CATEGORY_EXPIRY_DAYS)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password!', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        age = request.form['age']
        gender = request.form['gender']

        if username in users:
            flash('Username already exists!', 'danger')
        else:
            new_user = User(username, username, hashed_password, age, gender)
            users[username] = new_user
            user_groceries[username] = {}
            login_user(new_user)
            return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Function to call Nutritionix API for product information
def get_nutrition_data(item_name):
    url = f"https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_API_KEY,
    }
    payload = {'query': item_name}

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        # Check if the API response is valid and return nutritional details
        if 'foods' in data and len(data['foods']) > 0:
            food_data = data['foods'][0]
            return food_data  # Return the first match
        return None  # No data found for the item
    except Exception as e:
        print(f"Error fetching nutrition data: {e}")
        return None


def get_shelf_life_adjustment(age, gender, category, item_name):
    # Default shelf life from the CATEGORY_EXPIRY_DAYS mapping
    base_shelf_life = CATEGORY_EXPIRY_DAYS.get(category, 30)

    # Fetch nutritional information from Nutritionix
    food_data = get_nutrition_data(item_name)

    if food_data:
        # Example of adjusting shelf life based on calories (a placeholder for your own logic)
        calories = food_data.get('nf_calories', 0)
        if calories > 300:  # If it's a high-calorie item, it might last longer
            base_shelf_life += 5

    # Further adjust based on user profile (age and gender)
    if age > 50:
        base_shelf_life += 2  # Older users might need slightly adjusted shelf lives for some reason
    if gender == "male":
        base_shelf_life += 1  # Gender can have a small influence

    return base_shelf_life


@app.route('/add', methods=['POST'])
@login_required
def add_item():
    try:
        # Ensure request is JSON
        if not request.is_json:
            return jsonify(success=False, error="Request must be JSON"), 400

        data = request.get_json()

        # Validate inputs
        item = data.get('item')
        qty = data.get('qty')
        size = data.get('size')
        category = data.get('category')

        if not all([item, qty, size, category]):
            return jsonify(success=False, error="Missing required fields"), 400

        try:
            qty = int(qty)
        except ValueError:
            return jsonify(success=False, error="Quantity must be an integer"), 400

        # Adjust shelf life based on user profile and nutrition data
        adjusted_shelf_life = get_shelf_life_adjustment(
            int(current_user.age) if current_user.age else 30,
            current_user.gender or "other",
            category,
            item
        )
        date_added = datetime.now().strftime("%Y-%m-%d")

        # Add item to the user's groceries
        groceries = user_groceries.get(current_user.username, {})
        groceries[item] = {
            "qty": qty,
            "size": size,
            "category": category,
            "date_added": date_added,
            "shelf_life": adjusted_shelf_life
        }
        user_groceries[current_user.username] = groceries

        return jsonify(success=True)

    except Exception as e:
        print(f"Error in /add: {e}")
        return jsonify(success=False, error="Server error"), 500


# Alerts route
@app.route('/alerts')
@login_required
def check_alerts():
    today = datetime.now()
    alerts = []
    groceries = user_groceries.get(current_user.username, {})

    for item, data in groceries.items():
        added_date = datetime.strptime(data['date_added'], "%Y-%m-%d")
        expiry_date = added_date + timedelta(days=int(data['shelf_life']))
        days_left = (expiry_date - today).days

        if data['qty'] <= 2 or days_left <= 2:  # Low quantity or expiring soon
            alerts.append({
                'item': item,
                'qty': data['qty'],
                'days_left': days_left
            })

    return jsonify(alerts=alerts)


@app.route('/delete/<item>', methods=['DELETE'])
@login_required
def delete_item(item):
    groceries = user_groceries.get(current_user.username, {})
    if item in groceries:
        del groceries[item]
        return jsonify(success=True)
    return jsonify(error="Item not found"), 404


@app.route('/update/<item>', methods=['PUT'])
@login_required
def update_item(item):
    groceries = user_groceries.get(current_user.username, {})
    data = request.json
    if item in groceries:
        groceries[item].update(data)
        return jsonify(success=True)
    return jsonify(error="Item not found"), 404


@app.route('/list')
@login_required
def list_items():
    groceries = user_groceries.get(current_user.username, {})
    return jsonify(groceries)


@app.route('/barcode/<code>')
@login_required
def fetch_barcode(code):
    url = f"https://world.openfoodfacts.org/api/v0/product/{code}.json"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") == 1:
            product = data["product"]
            return jsonify(
                name=product.get("product_name", ""),
                quantity=product.get("quantity", ""),
                categories=product.get("categories_tags", [])
            )
        return jsonify(error="Product not found"), 404
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        age = request.form['age']
        gender = request.form['gender']
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.image = filename
        current_user.age = age
        current_user.gender = gender
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


if __name__ == '__main__':
    app.run(debug=True)
