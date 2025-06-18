import sqlite3
import pandas as pd
from tabulate import tabulate
import os
import csv

# Path to your database
db_path = os.path.join('instance', 'lms.db')

def view_all_tables():
    """View all tables and their data in the database"""
    if not os.path.exists(db_path):
        print("\n❌ Database not found! Please initialize the database first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\n📋 Table: {table_name}")
        print("-" * 40)
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Get table data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Print table using tabulate
        if rows:
            print(tabulate(rows, headers=columns, tablefmt='grid'))
        else:
            print("No data in table")

def export_to_csv():
    """Export all tables to CSV files"""
    if not os.path.exists(db_path):
        print("\n❌ Database not found! Please initialize the database first.")
        return
    
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        csv_file = os.path.join('data', f"{table_name}.csv")
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Get table data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Write to CSV
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
            
        print(f"✅ Exported: {csv_file}")
    
    conn.close()
    print("\n✨ All tables exported to 'data' folder!")

def view_specific_table(table_name):
    """View data from a specific table"""
    
    if not os.path.exists(db_path):
        print("Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        print(f"\n📊 TABLE: {table_name}")
        print("-" * 80)
        print(f"Total Records: {len(df)}")
        print("\nData:")
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
    except Exception as e:
        print(f"Error: Table '{table_name}' not found!")
        print("Available tables:")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
    
    conn.close()

if __name__ == "__main__":
    print("\nLMS Database Viewer")
    print("==================\n")
    print("1. View all tables")
    print("2. Export all tables to CSV")
    print("3. View specific table")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            view_all_tables()
        elif choice == '2':
            export_to_csv()
        elif choice == '3':
            table = input("Enter table name (e.g., user): ")
            view_specific_table(table)
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")