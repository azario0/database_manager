import customtkinter as ctk
import mysql.connector
from mysql.connector import Error
import pandas as pd
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk

class DatabaseManager:
    def __init__(self):
        self.connection = None
        
    def connect(self, host, user, password):
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )
            return True, "Connected successfully!"
        except Error as e:
            return False, f"Error: {e}"
    
    def create_database(self, db_name):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            return True, f"Database '{db_name}' created successfully!"
        except Error as e:
            return False, f"Error: {e}"
            
    def get_databases(self):
        cursor = self.connection.cursor()
        cursor.execute("SHOW DATABASES")
        return [db[0] for db in cursor.fetchall()]
        
    def get_tables(self, db_name):
        cursor = self.connection.cursor()
        cursor.execute(f"USE {db_name}")
        cursor.execute("SHOW TABLES")
        return [table[0] for table in cursor.fetchall()]
        
    def get_table_data(self, db_name, table_name):
        cursor = self.connection.cursor()
        cursor.execute(f"USE {db_name}")
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return columns, data
        
    def create_table(self, db_name, table_name, columns):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"USE {db_name}")
            columns_str = ", ".join([f"{name} {dtype}" for name, dtype in columns])
            cursor.execute(f"CREATE TABLE {table_name} ({columns_str})")
            return True, f"Table '{table_name}' created successfully!"
        except Error as e:
            return False, f"Error: {e}"
            
    def import_csv(self, db_name, table_name, csv_path):
        try:
            df = pd.read_csv(csv_path)
            cursor = self.connection.cursor()
            cursor.execute(f"USE {db_name}")
            
            # Create table if it doesn't exist
            columns = []
            for col in df.columns:
                dtype = "VARCHAR(255)"  # Default type
                columns.append(f"{col} {dtype}")
            columns_str = ", ".join(columns)
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")
            
            # Insert data
            for _, row in df.iterrows():
                values = tuple(str(value) for value in row)
                placeholders = ", ".join(["%s"] * len(values))
                query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                
            self.connection.commit()
            return True, f"CSV data imported successfully into '{table_name}'!"
        except Error as e:
            return False, f"Error: {e}"

    def update_row(self, db_name, table_name, column_values, where_clause):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"USE {db_name}")
            
            set_clause = ", ".join([f"{col} = %s" for col in column_values.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            cursor.execute(query, list(column_values.values()))
            self.connection.commit()
            return True, "Row updated successfully!"
        except Error as e:
            return False, f"Error: {e}"
    
    def delete_row(self, db_name, table_name, where_clause):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"USE {db_name}")
            
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            cursor.execute(query)
            self.connection.commit()
            return True, "Row deleted successfully!"
        except Error as e:
            return False, f"Error: {e}"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("MySQL Database Manager")
        self.geometry("1000x700")
        
        self.db_manager = DatabaseManager()
        
        # Create tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.tab_connect = self.tabview.add("Connect")
        self.tab_manage = self.tabview.add("Manage")
        self.tab_explorer = self.tabview.add("Explorer")
        self.tab_import = self.tabview.add("Import CSV")
        
        self.setup_connect_tab()
        self.setup_manage_tab()
        self.setup_explorer_tab()
        self.setup_import_tab()
        
    def setup_connect_tab(self):
        # Connection frame
        frame = ctk.CTkFrame(self.tab_connect)
        frame.pack(padx=10, pady=10, fill="both")
        
        ctk.CTkLabel(frame, text="Host:").pack(pady=5)
        self.host_entry = ctk.CTkEntry(frame)
        self.host_entry.pack(pady=5)
        self.host_entry.insert(0, "localhost")
        
        ctk.CTkLabel(frame, text="Username:").pack(pady=5)
        self.user_entry = ctk.CTkEntry(frame)
        self.user_entry.pack(pady=5)
        self.user_entry.insert(0, "root")
        
        ctk.CTkLabel(frame, text="Password:").pack(pady=5)
        self.pass_entry = ctk.CTkEntry(frame, show="*")
        self.pass_entry.pack(pady=5)
        
        ctk.CTkButton(frame, text="Connect", command=self.connect_to_db).pack(pady=10)
           
    def setup_manage_tab(self):
        frame = ctk.CTkFrame(self.tab_manage)
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create database section
        create_frame = ctk.CTkFrame(frame)
        create_frame.pack(padx=10, pady=10, fill="x")
        
        ctk.CTkLabel(create_frame, text="Create Database").pack(pady=5)
        self.new_db_entry = ctk.CTkEntry(create_frame)
        self.new_db_entry.pack(pady=5)
        ctk.CTkButton(create_frame, text="Create Database", 
                     command=self.create_new_database).pack(pady=5)

    def setup_explorer_tab(self):
        # Main container
        main_frame = ctk.CTkFrame(self.tab_explorer)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Top controls frame
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(padx=10, pady=5, fill="x")
        
        # Database and table selection
        select_frame = ctk.CTkFrame(controls_frame)
        select_frame.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkLabel(select_frame, text="Database:").pack(side="left", padx=5)
        self.db_listbox = ctk.CTkOptionMenu(select_frame, values=[], 
                                          command=self.on_database_select)
        self.db_listbox.pack(side="left", padx=5)
        
        ctk.CTkLabel(select_frame, text="Table:").pack(side="left", padx=5)
        self.table_listbox = ctk.CTkOptionMenu(select_frame, values=[], 
                                             command=self.show_table_data)
        self.table_listbox.pack(side="left", padx=5)
        
        # Refresh button
        ctk.CTkButton(controls_frame, text="🔄 Refresh", 
                     command=lambda: self.on_database_select(self.db_listbox.get())
                     ).pack(side="right", padx=5)
        
        # Create main content frame
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        
        self.tree = ttk.Treeview(content_frame)
        self.tree.pack(pady=10, fill="both", expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(content_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(content_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x')
        
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Edit/Delete buttons frame
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkButton(buttons_frame, text="Edit Selected", 
                     command=self.edit_selected_row).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Delete Selected", 
                     command=self.delete_selected_row).pack(side="left", padx=5)
        
    def setup_import_tab(self):
        frame = ctk.CTkFrame(self.tab_import)
        frame.pack(padx=10, pady=10, fill="both")
        
        ctk.CTkButton(frame, text="Select CSV File", 
                     command=self.select_csv).pack(pady=10)
        
        self.csv_label = ctk.CTkLabel(frame, text="No file selected")
        self.csv_label.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Select Database:").pack(pady=5)
        self.import_db_menu = ctk.CTkOptionMenu(frame, values=[])
        self.import_db_menu.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Table Name:").pack(pady=5)
        self.import_table_entry = ctk.CTkEntry(frame)
        self.import_table_entry.pack(pady=5)
        
        ctk.CTkButton(frame, text="Import CSV", 
                     command=self.import_csv_to_db).pack(pady=10)
        
    def edit_selected_row(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a row to edit")
            return
            
        # Get the current values
        current_values = self.tree.item(selected_item[0])['values']
        columns = self.tree["columns"]
        
        # Create edit dialog
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Row")
        edit_window.geometry("400x500")
        
        # Create entries for each column
        entries = {}
        for i, (col, val) in enumerate(zip(columns, current_values)):
            frame = ctk.CTkFrame(edit_window)
            frame.pack(padx=10, pady=5, fill="x")
            
            ctk.CTkLabel(frame, text=f"{col}:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame)
            entry.pack(side="left", padx=5, fill="x", expand=True)
            entry.insert(0, str(val))
            entries[col] = entry
        
        def save_changes():
            # Collect new values
            new_values = {col: entry.get() for col, entry in entries.items()}
            
            # Create WHERE clause using all columns for unique identification
            where_conditions = []
            for col, old_val in zip(columns, current_values):
                if isinstance(old_val, str):
                    where_conditions.append(f"{col} = '{old_val}'")
                else:
                    where_conditions.append(f"{col} = {old_val}")
            where_clause = " AND ".join(where_conditions)
            
            # Update the database
            success, message = self.db_manager.update_row(
                self.db_listbox.get(),
                self.table_listbox.get(),
                new_values,
                where_clause
            )
            
            if success:
                self.show_table_data(self.table_listbox.get())
                edit_window.destroy()
            messagebox.showinfo("Update Row", message)
        
        ctk.CTkButton(edit_window, text="Save Changes", 
                     command=save_changes).pack(pady=10)
        
    def delete_selected_row(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a row to delete")
            return
            
        if not messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this row?"):
            return
            
        # Get the current values and columns
        current_values = self.tree.item(selected_item[0])['values']
        columns = self.tree["columns"]
        
        # Create WHERE clause using all columns for unique identification
        where_conditions = []
        for col, val in zip(columns, current_values):
            if isinstance(val, str):
                where_conditions.append(f"{col} = '{val}'")
            else:
                where_conditions.append(f"{col} = {val}")
        where_clause = " AND ".join(where_conditions)
        
        # Delete from database
        success, message = self.db_manager.delete_row(
            self.db_listbox.get(),
            self.table_listbox.get(),
            where_clause
        )
        
        if success:
            self.show_table_data(self.table_listbox.get())
        messagebox.showinfo("Delete Row", message)
        
    def connect_to_db(self):
        success, message = self.db_manager.connect(
            self.host_entry.get(),
            self.user_entry.get(),
            self.pass_entry.get()
        )
        messagebox.showinfo("Connection", message)
        if success:
            self.refresh_database_list()
            
    def create_new_database(self):
        db_name = self.new_db_entry.get()
        if db_name:
            success, message = self.db_manager.create_database(db_name)
            messagebox.showinfo("Create Database", message)
            if success:
                self.refresh_database_list()
                
    def refresh_database_list(self):
        databases = self.db_manager.get_databases()
        self.db_listbox.configure(values=databases)
        self.import_db_menu.configure(values=databases)
        
    def on_database_select(self, db_name):
        tables = self.db_manager.get_tables(db_name)
        self.table_listbox.configure(values=tables)
        
    def show_table_data(self, table_name):
        if not table_name:
            return
            
        # Clear existing columns
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
        
        # Get and display new data
        columns, data = self.db_manager.get_table_data(
            self.db_listbox.get(),
            table_name
        )
        
        # Configure columns
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, minwidth=100, width=150)
            
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add data
        for row in data:
            self.tree.insert("", "end", values=row)
            
    def select_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            self.csv_label.configure(text=file_path)
            self.csv_path = file_path
            
    def import_csv_to_db(self):
        if not hasattr(self, 'csv_path'):
            messagebox.showerror("Error", "Please select a CSV file first!")
            return
            
        db_name = self.import_db_menu.get()
        table_name = self.import_table_entry.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and enter a table name!")
            return
            
        success, message = self.db_manager.import_csv(db_name, table_name, self.csv_path)
        messagebox.showinfo("Import CSV", message)
        if success:
            self.on_database_select(db_name)

if __name__ == "__main__":
    app = App()
    app.mainloop()