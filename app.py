from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# Initialize Firebase with credentials from environment variables
firebase_credentials = {
    "type": "service_account",
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL'),
    "universe_domain": "googleapis.com"
}

# Initialize Firebase Admin
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def home():
    return render_template('splash_screen.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/main')
def main():
    return render_template('index.html')

@app.route('/billing-form', methods=['GET', 'POST'])
def billing_form():
    if request.method == 'POST':
        try:
            customer_id = request.form['customer_id']
            name = request.form['name']
            phone_number = request.form['phone_number']
            tree_id = request.form['tree_id']
            tree_measurement = request.form['tree_measurement']
            tree_quantity = int(request.form.get('tree_quantity', 1))
            amount = float(request.form['amount'])
            amount_paid = float(request.form.get('amount_paid', 0))

            # Add customer data
            customer_ref = db.collection('customers')
            customer_ref.add({
                'customerId': customer_id,
                'name': name,
                'phoneNumber': phone_number,
                'timestamp': firestore.SERVER_TIMESTAMP
            })

            # Add tree data
            tree_ref = db.collection('trees')
            tree_ref.add({
                'treeId': tree_id,
                'treeMeasurement': tree_measurement,
                'timestamp': firestore.SERVER_TIMESTAMP
            })

            # Add bill data
            bill_ref = db.collection('bills')
            bill_ref.add({
                'name': name,
                'amount': amount,
                'amountPaid': amount_paid,
                'customerId': customer_id,
                'phoneNumber': phone_number,
                'treeId': tree_id,
                'treeMeasurement': tree_measurement,
                'treeQuantity': tree_quantity,
                'timestamp': firestore.SERVER_TIMESTAMP
            })

            flash('Bill data saved successfully!', 'success')
            return redirect(url_for('billing_form'))

        except Exception as e:
            flash(f'Error saving data: {str(e)}', 'error')
            return redirect(url_for('billing_form'))

    return render_template('billing_form.html')

@app.route('/bills')
def bills_view():
    bills = [doc.to_dict() for doc in db.collection('bills').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()]
    return render_template('bills_view.html', bills=bills)

@app.route('/customers')
def customer_details():
    customers = [doc.to_dict() for doc in db.collection('customers').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()]
    return render_template('customer_details.html', customers=customers)

@app.route('/trees', methods=['GET'])
def tree_details():
    trees = [doc.to_dict() for doc in db.collection('trees').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()]
    return render_template('tree_details.html', trees=trees)

@app.route('/add-tree', methods=['POST'])
def add_tree():
    try:
        tree_id = request.form['tree_id']
        tree_measurement = request.form['tree_measurement']
        tree_quantity = int(request.form.get('tree_quantity', 1))

        # Add tree data
        tree_ref = db.collection('trees')
        tree_ref.add({
            'treeId': tree_id,
            'treeMeasurement': tree_measurement,
            'treeQuantity': tree_quantity,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        flash('Tree added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding tree: {str(e)}', 'error')
    
    return redirect(url_for('tree_details'))

@app.route('/api/search-customer/<customer_id>')
def search_customer(customer_id):
    customer = db.collection('customers').where('customerId', '==', customer_id).limit(1).get()
    if len(customer) > 0:
        customer_data = customer[0].to_dict()
        return jsonify(customer_data)
    return jsonify({})

@app.route('/api/search-tree/<tree_id>')
def search_tree(tree_id):
    tree = db.collection('trees').where('treeId', '==', tree_id).limit(1).get()
    if len(tree) > 0:
        tree_data = tree[0].to_dict()
        return jsonify(tree_data)
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True) 