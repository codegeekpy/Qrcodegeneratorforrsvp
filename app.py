import streamlit as st
import sqlite3
import qrcode
from PIL import Image
import io
import base64
import bcrypt
from datetime import datetime
import pandas as pd
import plotly.express as px
import time
# from pyzbar.pyzbar import decode # Comment out pyzbar import
import cv2 # Import opencv-python
import numpy as np # Import numpy for image conversion

DATABASE_FILE = 'scan_database.db'
USER_DATA_CSV = 'user_data.csv' # Assuming user data is in a CSV file

LOCATIONS = [
    "Hyderabad - Himalaya 105,205 IIIT Hyderabad",
    "Warangal - Chaitanya Deemed University",
    "Khammam - IT Hub",
    "Karimnagar - IT Tower",
    "Nizamabad - IT Towers"
]

st.set_page_config(page_title="Summer of AI - Viswam.ai", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%); /* Light purple to light blue gradient */
    }
    .stButton>button {
        background: linear-gradient(45deg, #6a11cb, #2575fc); /* Purple to blue gradient */
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #ccc;
        padding: 10px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #6a11cb; /* Purple */
        box-shadow: 0 0 5px rgba(106, 17, 203, 0.3);
    }
    .title-text {
        font-size: 3em;
        font-weight: bold;
        color: #4a148c; /* Darker purple */
        text-align: center;
        margin-bottom: 1em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .subtitle-text {
        font-size: 1.5em;
        color: #333; /* Dark gray */
        text-align: center;
        margin-bottom: 2em;
    }
    .card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .success-message {
        background: #00bfa5; /* Teal */
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        animation: fadeIn 0.5s;
    }
    .error-message {
        background: #d50000; /* Red */
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        animation: fadeIn 0.5s;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .qr-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 20px 0;
        animation: slideIn 0.5s;
    }
    @keyframes slideIn {
        from { transform: translateX(-100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password TEXT,
                  user_type TEXT,
                  created_at TIMESTAMP)''')
    
    # Create attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  location TEXT,
                  timestamp TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def register_user(username, email, password, user_type):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute('''INSERT INTO users (username, email, password, user_type, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (username, email, hashed_password, user_type, datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('SELECT password, user_type FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return result[1]
    return None

def show_loading_animation():
    with st.spinner('Loading...'):
        time.sleep(0.5)

def load_authorized_users(csv_file):
    try:
        df = pd.read_csv(csv_file)
        # Assuming the CSV has a column named 'username'
        return df['username'].tolist()
    except FileNotFoundError:
        st.error(f"Error: {csv_file} not found. Please create this file with a 'username' column.")
        return []
    except KeyError:
        st.error(f"Error: {csv_file} should contain a 'username' column.")
        return []

def main():
    # Welcome page
    if not st.session_state.authenticated:
        st.markdown('<div class="title-text">Welcome to Summer of AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle-text">Viswam.ai Attendance System</div>', unsafe_allow_html=True)
        
        # Add a decorative element
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login", key="login_btn"):
                show_loading_animation()
                user_type = verify_user(username, password)
                if user_type:
                    st.session_state.authenticated = True
                    st.session_state.user_type = user_type
                    st.session_state.username = username
                    st.experimental_rerun()
                else:
                    st.markdown('<div class="error-message">Invalid credentials</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Register")
            reg_username = st.text_input("Choose Username")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Choose Password", type="password")
            reg_user_type = st.selectbox("User Type", ["AI Developer", "Regional POC", "Admin"])
            
            if st.button("Register", key="register_btn"):
                show_loading_animation()
                if register_user(reg_username, reg_email, reg_password, reg_user_type):
                    st.markdown('<div class="success-message">Registration successful! Please login.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">Username or email already exists</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Authenticated pages
    else:
        if st.session_state.user_type == "AI Developer":
            show_ai_developer_page()
        elif st.session_state.user_type == "Regional POC":
            show_poc_page()
        elif st.session_state.user_type == "Admin":
            show_admin_page()
        
        if st.sidebar.button("Logout"):
            show_loading_animation()
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.session_state.username = None
            st.experimental_rerun()

def show_ai_developer_page():
    st.markdown('<div class="title-text">AI Developer Dashboard</div>', unsafe_allow_html=True)
    
    # Generate QR Code
    user_data = f"AI_DEV_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}"
    qr_img = generate_qr_code(user_data)
    
    # Convert QR code to base64 for display
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    st.markdown('<div class="qr-container">', unsafe_allow_html=True)
    st.subheader("Your QR Code")
    st.image(f"data:image/png;base64,{img_str}", width=200)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Attendance form
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Mark Attendance")
    location = st.selectbox("Select Location", LOCATIONS) # Use selectbox for locations
    if st.button("Mark Attendance"):
        show_loading_animation()
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ?', (st.session_state.username,))
        user_id = c.fetchone()[0]
        c.execute('''INSERT INTO attendance (user_id, location, timestamp)
                     VALUES (?, ?, ?)''', (user_id, location, datetime.now()))
        conn.commit()
        conn.close()
        st.markdown('<div class="success-message">Attendance marked successfully!</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_poc_page():
    st.markdown('<div class="title-text">Regional POC Dashboard</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Scan Attendance")
    uploaded_file = st.file_uploader("Upload QR Code Image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        try:
            # Read the image file
            img = Image.open(uploaded_file)
            
            # Convert PIL Image to OpenCV format (NumPy array, BGR)
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Initialize QR code detector
            qr_detector = cv2.QRCodeDetector()
            
            # Detect and decode QR code
            decoded_data, vertices, _ = qr_detector.detectAndDecode(img_cv)
            
            if decoded_data:
                st.write(f"Scanned QR Data: {decoded_data}")
                
                # Validate QR data (assuming it contains username)
                authorized_users = load_authorized_users(USER_DATA_CSV)
                
                # Extract username from QR data (assuming format 'AI_DEV_username_timestamp')
                if decoded_data.startswith("AI_DEV_"):
                    parts = decoded_data.split('_')
                    if len(parts) >= 2:
                        scanned_username = parts[1]
                        
                        if scanned_username in authorized_users:
                            # Record attendance
                            conn = sqlite3.connect(DATABASE_FILE)
                            c = conn.cursor()
                            c.execute('SELECT id FROM users WHERE username = ?', (scanned_username,))
                            user_id_row = c.fetchone()
                            
                            if user_id_row:
                                user_id = user_id_row[0]
                                
                                # POC selects location for the scan
                                scan_location = st.selectbox("Select Location for Scan", LOCATIONS)
                                
                                c.execute('''INSERT INTO attendance (user_id, location, timestamp)
                                             VALUES (?, ?, ?)''', (user_id, scan_location, datetime.now()))
                                conn.commit()
                                conn.close()
                                st.markdown(f'<div class="success-message">Attendance recorded for {scanned_username} at {scan_location}!</div>', unsafe_allow_html=True)
                                # Party celebration theme placeholder
                                st.balloons()
                            else:
                                st.markdown(f'<div class="error-message">User {scanned_username} not found in the database.</div>', unsafe_allow_html=True)
                                
                        else:
                            st.markdown(f'<div class="error-message">User {scanned_username} is not in the authorized users list ({USER_DATA_CSV}).</div>', unsafe_allow_html=True)
                    else:
                         st.markdown('<div class="error-message">Invalid QR code format.</div>', unsafe_allow_html=True)
                else:
                     st.markdown('<div class="error-message">QR code does not appear to be a valid attendance code.</div>', unsafe_allow_html=True)
            else:
                st.warning("No QR code found in the image.")
        except Exception as e:
            st.error(f"An error occurred during QR code processing: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Location Attendance")
    location = st.selectbox("Select Location to View", LOCATIONS) # Use selectbox for locations
    if st.button("View Attendance"):
        show_loading_animation()
        conn = sqlite3.connect(DATABASE_FILE)
        df = pd.read_sql_query('''
            SELECT u.username, a.timestamp 
            FROM attendance a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.location = ?
        ''', conn, params=(location,))
        conn.close()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No attendance records found for this location")
    st.markdown('</div>', unsafe_allow_html=True)

def show_admin_page():
    st.markdown('<div class="title-text">Admin Dashboard</div>', unsafe_allow_html=True)
    
    # Fetch data for analysis
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Location-wise attendance
    location_df = pd.read_sql_query('''
        SELECT location, COUNT(*) as count 
        FROM attendance 
        GROUP BY location
    ''', conn)
    
    # User type distribution
    user_df = pd.read_sql_query('''
        SELECT user_type, COUNT(*) as count 
        FROM users 
        GROUP BY user_type
    ''', conn)
    
    conn.close()
    
    # Display analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Location-wise Attendance")
        if not location_df.empty:
            fig = px.bar(location_df, x='location', y='count', title='Attendance by Location')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#666')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No attendance data available")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("User Distribution")
        if not user_df.empty:
            fig = px.pie(user_df, values='count', names='user_type', title='User Type Distribution')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#666')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Raw data view
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Raw Data")
    conn = sqlite3.connect(DATABASE_FILE)
    attendance_df = pd.read_sql_query('''
        SELECT u.username, u.user_type, a.location, a.timestamp 
        FROM attendance a 
        JOIN users u ON a.user_id = u.id
    ''', conn)
    conn.close()
    
    if not attendance_df.empty:
        st.dataframe(attendance_df, use_container_width=True)
    else:
        st.info("No attendance records found")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 