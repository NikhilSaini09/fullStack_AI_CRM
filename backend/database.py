# backend/database.py
import sqlite3

def init_db():
    # This creates a file named crm_data.db in your backend folder
    conn = sqlite3.connect('crm_data.db')
    cursor = conn.cursor()
    
    # Create a table for HCP Profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hcp_profiles (
            name TEXT PRIMARY KEY,
            specialty TEXT,
            preferences TEXT
        )
    ''')
    
    # Create a table for Saved Interactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hcp_name TEXT,
            date TEXT,
            topics TEXT,
            materials TEXT
        )
    ''')
    
    # Insert some starter data (only if the table is empty)
    cursor.execute("SELECT COUNT(*) FROM hcp_profiles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO hcp_profiles VALUES ('Dr. Smith', 'Cardiologist', 'Prefers morning meetings.')")
        cursor.execute("INSERT INTO hcp_profiles VALUES ('Dr. Sharma', 'Oncologist', 'Interested in Phase III trials.')")
        
    conn.commit()
    conn.close()

# Run this once when the file is imported
init_db()