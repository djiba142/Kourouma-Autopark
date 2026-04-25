import psycopg2
import sys

try:
    conn = psycopg2.connect(
        dbname='bsg_autoparts_db',
        user='Auto-part-BSG',
        password='ldk142102@',
        host='127.0.0.1',
        port='5432'
    )
    print("SUCCESS: Connected to the database.")
    conn.close()
except Exception as e:
    print(f"FAILED: Connection error.")
    try:
        # Try to print the raw error bytes if possible, or just the repr
        print(f"Error repr: {repr(e)}")
    except:
        print("Could not even print the error repr due to encoding.")
