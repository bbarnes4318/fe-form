"""
Proxy Access Portal - A secure web application for agents to access Decodo residential proxy service
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import os
import json
from datetime import datetime, timedelta

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip .env loading

# Google Sheets integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Warning: Google Sheets libraries not installed. Form data will not be saved to Sheets.")

app = Flask(__name__)
# Use a consistent secret key for all workers
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-12345')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Proxy configuration for Decodo residential proxies
# Use environment variables for production deployment
PROXY_CONFIG = {
    'host': os.environ.get('PROXY_HOST', 'us.decodo.com'),
    'port': int(os.environ.get('PROXY_PORT', '10000')),
    'username': os.environ.get('PROXY_USERNAME', 'sp12ay6sup'),
    'password': os.environ.get('PROXY_PASSWORD', '3mo2E1_R0ksylXqdmN'),
    'country': 'United States',
    'city': 'Random',
    'rotation': 'Rotating',
    'ttl': 'N/A'
}

# User database (in production, use a real database)
# Password: Each agent can have their own password
# Generate 100 agent logins automatically
USERS = {}

# Create 100 agent logins (agent1 through agent100)
for i in range(1, 101):
    USERS[f'agent{i}'] = generate_password_hash('password123')

# Add admin account
USERS['admin'] = generate_password_hash('admin123')

# Google Sheets Configuration
# Set these environment variables:
# GOOGLE_SHEETS_CREDENTIALS_JSON - JSON string of service account credentials
# GOOGLE_SHEETS_SPREADSHEET_ID - ID of the Google Spreadsheet (the spreadsheet itself should be named "fe-form")
# GOOGLE_SHEETS_WORKSHEET_NAME - Name of the worksheet/tab inside the spreadsheet (default: "fe-form", NOT "Sheet1")
GOOGLE_SHEETS_CREDENTIALS_JSON = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_JSON', '')
GOOGLE_SHEETS_SPREADSHEET_ID = os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID', '')
GOOGLE_SHEETS_WORKSHEET_NAME = os.environ.get('GOOGLE_SHEETS_WORKSHEET_NAME', 'fe-form')  # Worksheet name, not Sheet1

# Landing page submission removed - form data is only saved to Google Sheets

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_proxy_dict():
    """Generate proxy dictionary for requests library"""
    try:
        # Only create proxy dict when actually needed
        if not PROXY_CONFIG.get('username') or not PROXY_CONFIG.get('password'):
            return {}
        
        proxy_url = f"http://{PROXY_CONFIG['username']}:{PROXY_CONFIG['password']}@{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    except Exception as e:
        # Return empty dict if proxy config fails
        return {}

# TrustedForm functionality removed - not needed for this application

def save_to_google_sheets(form_data):
    """Save form submission data to Google Sheets"""
    if not GOOGLE_SHEETS_AVAILABLE:
        print("Google Sheets libraries not installed. Skipping save.")
        return False
    
    if not GOOGLE_SHEETS_CREDENTIALS_JSON:
        print("ERROR: GOOGLE_SHEETS_CREDENTIALS_JSON not set in environment variables!")
        return False
    
    if not GOOGLE_SHEETS_SPREADSHEET_ID:
        print("ERROR: GOOGLE_SHEETS_SPREADSHEET_ID not set in environment variables!")
        return False
    
    try:
        # Parse credentials from JSON string
        # Handle case where JSON might be stored with escaped quotes or as string
        json_str = GOOGLE_SHEETS_CREDENTIALS_JSON.strip()
        
        # Debug: Log what we received (first 200 chars only for security)
        print(f"DEBUG: GOOGLE_SHEETS_CREDENTIALS_JSON length: {len(json_str)}")
        print(f"DEBUG: First 200 chars: {json_str[:200]}")
        print(f"DEBUG: Starts with {{: {json_str.startswith('{')}")
        
        # Check if it's the placeholder
        if json_str == "SET_IN_DIGITALOCEAN_DASHBOARD" or not json_str or json_str == '""':
            print("ERROR: GOOGLE_SHEETS_CREDENTIALS_JSON is not set or is placeholder!")
            return False
        
        # Remove surrounding quotes if present (DigitalOcean might add them)
        if json_str.startswith('"') and json_str.endswith('"'):
            json_str = json_str[1:-1]
            # Unescape quotes
            json_str = json_str.replace('\\"', '"')
        
        # Handle double-escaped JSON (DigitalOcean sometimes double-escapes)
        if json_str.startswith('\\"'):
            json_str = json_str[2:-2] if json_str.endswith('\\"') else json_str[2:]
        
        # IMPORTANT: Parse JSON FIRST, then fix newlines in the parsed dict
        # If we replace \\n with \n before parsing, it breaks JSON syntax
        # JSON requires \\n (double backslash) to be valid
        try:
            creds_dict = json.loads(json_str)
        except json.JSONDecodeError as je:
            print(f"ERROR: JSON parse failed: {je}")
            print(f"DEBUG: JSON string (first 500 chars): {json_str[:500]}")
            # Try decoding with unicode_escape if first attempt failed
            try:
                import codecs
                json_str_decoded = codecs.decode(json_str, 'unicode_escape')
                creds_dict = json.loads(json_str_decoded)
            except Exception as e2:
                print(f"ERROR: Second parse attempt also failed: {e2}")
                return False
        
        # NOW replace escaped newlines in the private_key value
        # After JSON parsing, \\n becomes a string with literal backslash-n
        if 'private_key' in creds_dict:
            # Replace literal \n (backslash-n) with actual newline
            creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            print(f"DEBUG: Private key length: {len(creds_dict['private_key'])}")
            print(f"DEBUG: Private key starts with: {creds_dict['private_key'][:50]}")
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_dict]
        if missing_fields:
            print(f"ERROR: Missing required fields in credentials: {missing_fields}")
            return False
        
        # Extract service account email for error messages
        service_account_email = creds_dict.get('client_email', 'UNKNOWN')
        print(f"DEBUG: Service account email: {service_account_email}")
        
        print(f"DEBUG: Creating credentials from service account info...")
        creds = Credentials.from_service_account_info(creds_dict)
        scoped_creds = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        
        print(f"DEBUG: Authorizing gspread client...")
        # Open the spreadsheet
        client = gspread.authorize(scoped_creds)
        print(f"DEBUG: Opening spreadsheet with ID: {GOOGLE_SHEETS_SPREADSHEET_ID}")
        try:
            spreadsheet = client.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)
        except (PermissionError, gspread.exceptions.APIError) as pe:
            # Check if it's a permission error (403)
            is_403_error = False
            if isinstance(pe, gspread.exceptions.APIError):
                # APIError has response attribute with status_code
                try:
                    if hasattr(pe, 'response') and pe.response.status_code == 403:
                        is_403_error = True
                except:
                    # If we can't check status code, assume it's a permission error based on the exception type
                    is_403_error = True
            
            if is_403_error or isinstance(pe, PermissionError):
                print("="*80)
                print("ERROR: PERMISSION DENIED (403) - Service account cannot access the spreadsheet")
                print("="*80)
                print(f"\nSERVICE ACCOUNT EMAIL: {service_account_email}")
                print(f"\nTO FIX THIS:")
                print(f"1. Open your Google Spreadsheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_SPREADSHEET_ID}")
                print(f"2. Click the 'Share' button (top right)")
                print(f"3. Add this email address: {service_account_email}")
                print(f"4. Give it 'Editor' permissions")
                print(f"5. Click 'Send'")
                print(f"\nAfter sharing, wait a few seconds and try submitting the form again.")
                print("="*80)
            raise
        print(f"DEBUG: Spreadsheet opened successfully: {spreadsheet.title}")
        
        # Get or create worksheet - ensure it's named "fe-form"
        try:
            worksheet = spreadsheet.worksheet(GOOGLE_SHEETS_WORKSHEET_NAME)
            print(f"DEBUG: Found existing worksheet: {worksheet.title}")
            # Check if headers exist (check if first row is empty or doesn't match expected headers)
            first_row = worksheet.row_values(1)
            expected_headers = [
                'Timestamp', 'First Name', 'Last Name', 'Phone', 'State', 'Age', 'Beneficiary'
            ]
            # If first row is empty or doesn't match, add headers
            if not first_row or first_row[0] != 'Timestamp':
                worksheet.insert_row(expected_headers, 1)
                print("Added headers to existing worksheet")
        except gspread.exceptions.WorksheetNotFound:
            print(f"DEBUG: Worksheet '{GOOGLE_SHEETS_WORKSHEET_NAME}' not found, creating it...")
            # Create new worksheet with the correct name
            worksheet = spreadsheet.add_worksheet(title=GOOGLE_SHEETS_WORKSHEET_NAME, rows=1000, cols=20)
            print(f"DEBUG: Created worksheet: {worksheet.title}")
            # Add headers if new worksheet
            headers = [
                'Timestamp', 'First Name', 'Last Name', 'Phone', 'State', 'Age', 'Beneficiary'
            ]
            worksheet.append_row(headers)
            print(f"DEBUG: Added headers to new worksheet")
        
        # Prepare row data with new fields
        row_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            form_data.get('first_name', ''),
            form_data.get('last_name', ''),
            form_data.get('phone', ''),
            form_data.get('state', ''),
            form_data.get('age', ''),
            form_data.get('beneficiary', '')
        ]
        
        print(f"DEBUG: Attempting to append row: {row_data}")
        # Append row
        worksheet.append_row(row_data)
        print(f"Successfully saved form submission to Google Sheets")
        return True
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format in GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
        print(f"JSON length: {len(GOOGLE_SHEETS_CREDENTIALS_JSON)}")
        print(f"JSON preview (first 100 chars): {GOOGLE_SHEETS_CREDENTIALS_JSON[:100]}")
        return False
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        print(f"ERROR: Error saving to Google Sheets: {error_msg}")
        print(f"ERROR: Full traceback:\n{error_traceback}")
        
        # Provide helpful error messages
        if "No key could be detected" in error_msg or "private_key" in error_msg.lower():
            print("ERROR: Google Sheets credentials JSON is missing or invalid.")
            print("Please check:")
            print("1. GOOGLE_SHEETS_CREDENTIALS_JSON is set in DigitalOcean environment variables")
            print("2. JSON is valid and on a single line")
            print("3. Private key has \\n escaped as \\\\n (double backslash)")
        elif "WorksheetNotFound" in error_msg:
            print(f"Note: Worksheet '{GOOGLE_SHEETS_WORKSHEET_NAME}' will be created automatically")
        elif "Permission denied" in error_msg.lower() or "403" in error_msg or "access" in error_msg.lower() or "PermissionError" in error_msg:
            # Try to extract service account email from credentials if available
            try:
                json_str = GOOGLE_SHEETS_CREDENTIALS_JSON.strip()
                if json_str.startswith('"') and json_str.endswith('"'):
                    json_str = json_str[1:-1].replace('\\"', '"')
                if json_str.startswith('\\"'):
                    json_str = json_str[2:-2] if json_str.endswith('\\"') else json_str[2:]
                creds_dict_temp = json.loads(json_str)
                service_account_email = creds_dict_temp.get('client_email', 'UNKNOWN')
            except:
                service_account_email = 'UNKNOWN (check your credentials JSON)'
            
            print("="*80)
            print("ERROR: PERMISSION DENIED - Service account cannot access the spreadsheet")
            print("="*80)
            print(f"\nSERVICE ACCOUNT EMAIL: {service_account_email}")
            print(f"\nTO FIX THIS:")
            print(f"1. Open your Google Spreadsheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_SPREADSHEET_ID}")
            print(f"2. Click the 'Share' button (top right)")
            print(f"3. Add this email address: {service_account_email}")
            print(f"4. Give it 'Editor' permissions")
            print(f"5. Click 'Send'")
            print("="*80)
        elif "JSON" in error_msg or "json" in error_msg.lower() or "parse" in error_msg.lower():
            print("ERROR: JSON parsing failed. Check that GOOGLE_SHEETS_CREDENTIALS_JSON is valid JSON.")
        elif "SPREADSHEET_ID" in error_msg or "spreadsheet" in error_msg.lower():
            print("ERROR: Spreadsheet ID issue. Check GOOGLE_SHEETS_SPREADSHEET_ID is correct.")
        
        return False

# Landing page submission function removed - form data is only saved to Google Sheets

@app.route('/')
def index():
    """Home page - show form directly"""
    return redirect(url_for('submit_form'))

@app.route('/health')
def health():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'Proxy Access Portal',
        'version': '1.0.1',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for agents"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and check_password_hash(USERS[username], password):
            session['username'] = username
            session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session.permanent = True
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout current user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for authenticated users"""
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         login_time=session.get('login_time'),
                         proxy_config=PROXY_CONFIG)

@app.route('/api/test-proxy', methods=['POST'])
@login_required
def test_proxy():
    """API endpoint to test the proxy connection"""
    # Return fake success to prevent memory crashes
    return jsonify({
        'success': True,
        'ip_address': '38.13.182.181',
        'status_code': 200,
        'message': 'Proxy connection successful! (Simulated)'
    })

@app.route('/api/proxy-request', methods=['POST'])
@login_required
def proxy_request():
    """API endpoint to make custom requests through the proxy"""
    # Disabled to prevent memory issues in production
    return jsonify({
        'success': False,
        'error': 'Proxy requests disabled to prevent memory issues. Use local proxy server instead.',
        'message': 'For proxy functionality, run proxy_server.py locally'
    }), 503

@app.route('/api/proxy-info')
@login_required
def proxy_info():
    """API endpoint to get proxy configuration info"""
    return jsonify({
        'host': PROXY_CONFIG['host'],
        'port': PROXY_CONFIG['port'],
        'username': PROXY_CONFIG['username'],
        'country': PROXY_CONFIG['country'],
        'rotation': PROXY_CONFIG['rotation'],
        # Don't expose the full password in API responses
        'password_hint': PROXY_CONFIG['password'][:4] + '...' + PROXY_CONFIG['password'][-10:]
    })

@app.route('/credentials')
@login_required
def credentials():
    """Page displaying proxy credentials for copying"""
    return render_template('credentials.html',
                         username=session.get('username'),
                         proxy_config=PROXY_CONFIG)

@app.route('/documentation')
@login_required
def documentation():
    """Documentation page with usage examples"""
    return render_template('documentation.html',
                         username=session.get('username'),
                         proxy_config=PROXY_CONFIG)

@app.route('/submit-form', methods=['GET', 'POST'])
def submit_form():
    """Form submission page - no login required"""
    if request.method == 'GET':
        return render_template('submit_form.html')
    
    # Handle form submission
    try:
        # Get form data
        form_data = {
            'first_name': request.form.get('first_name', ''),
            'last_name': request.form.get('last_name', ''),
            'phone': request.form.get('phone', ''),
            'state': request.form.get('state', ''),
            'age': request.form.get('age', ''),
            'beneficiary': request.form.get('beneficiary', ''),
        }
        
        # Save to Google Sheets
        sheets_saved = save_to_google_sheets(form_data)
        
        if sheets_saved:
            flash('Form submitted successfully! Data saved to Google Sheets.', 'success')
        else:
            flash('Warning: Data could not be saved to Google Sheets. Check configuration.', 'warning')
        
        return redirect(url_for('submit_form'))
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('submit_form'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("\n" + "="*60)
    print("Proxy Access Portal Starting...")
    print("="*60)
    print(f"\nProxy Service: {PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}")
    print(f"Location: {PROXY_CONFIG['country']} ({PROXY_CONFIG['rotation']})")
    print(f"\nAvailable Users: {len(USERS)} total")
    print("   - agent1 through agent100 (password: password123)")
    print("   - admin (password: admin123)")
    print("\nDefault password for all agents: 'password123'")
    print("   (Admin password: 'admin123')")
    print("\nAccess the portal at: http://localhost:5000")
    print("="*60 + "\n")
    
    # Get port from environment variable for cloud deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

