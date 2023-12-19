import sys
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import os


class PharmacyManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Pharmacy Management System")

        # Database
        self.connection = sqlite3.connect("pharmacy.db")
        self.create_tables()

        # User authentication
        self.current_user = None

        # Medication data
        self.medication_list = []
        self.load_medication_data()

        # Create GUI components
        self.create_widgets()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY,
                medication_id TEXT,
                medication_name TEXT,
                quantity INTEGER,
                price REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                medication_id TEXT,
                quantity INTEGER,
                total_price REAL,
                sale_date TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                role TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                customer_id TEXT,
                customer_name TEXT,
                email TEXT,
                phone TEXT
            )
        ''')

        # Inserting sample user data
        cursor.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', 'adminpass', 'admin'))
        cursor.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', ('cashier', 'cashierpass', 'cashier'))

        self.connection.commit()

    def load_medication_data(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM medications')
        rows = cursor.fetchall()
        for row in rows:
            self.medication_list.append(row)

    def authenticate_user(self):
        username = simpledialog.askstring("Login", "Enter username:")
        password = simpledialog.askstring("Login", "Enter password:", show='*')

        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user_data = cursor.fetchone()

        if user_data:
            self.current_user = user_data[3]  # Role
            messagebox.showinfo("Login", f"Logged in as {username} ({self.current_user} role)")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            self.root.destroy()

    def check_authentication(self, required_role):
        if self.current_user != required_role:
            messagebox.showerror("Access Denied", "You do not have permission to perform this action.")
            return False
        return True

    def create_widgets(self):
        # Authenticate user
        self.authenticate_user()

        # Medication List Treeview
        columns = ("ID", "Medication ID", "Medication Name", "Quantity", "Price")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(pady=10, padx=10)
        self.update_treeview()

        # Add Medication Button
        add_button = ttk.Button(self.root, text="Add Medication", command=self.add_medication)
        add_button.pack(pady=5)

        # Remove Medication Button
        remove_button = ttk.Button(self.root, text="Remove Medication", command=self.remove_medication)
        remove_button.pack(pady=5)

        # Sell Medication Button
        sell_button = ttk.Button(self.root, text="Sell Medication", command=self.sell_medication)
        sell_button.pack(pady=5)

        # Update Medication Button
        update_button = ttk.Button(self.root, text="Update Medication", command=self.update_medication)
        update_button.pack(pady=5)

        # Generate Invoice Button
        invoice_button = ttk.Button(self.root, text="Generate Invoice", command=self.generate_invoice)
        invoice_button.pack(pady=5)

        # Generate Reports Button
        reports_button = ttk.Button(self.root, text="Generate Reports", command=self.generate_reports)
        reports_button.pack(pady=5)

        # Barcode Scanner Integration (assuming this part remains unchanged)

        # Customer Information (assuming this part remains unchanged)
        customer_button = ttk.Button(self.root, text="Manage Customers", command=self.manage_customers)
        customer_button.pack(pady=5)

        # Notifications (assuming this part remains unchanged)
        notification_button = ttk.Button(self.root, text="Check Notifications", command=self.check_notifications)
        notification_button.pack(pady=5)

    def add_medication(self):
        if not self.check_authentication('admin'):
            return

        # Dummy data for testing
        medication_data = ("M001", "Paracetamol", 100, 1.50)

        # Add medication to the database
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO medications (medication_id, medication_name, quantity, price)
            VALUES (?, ?, ?, ?)
        ''', medication_data)
        self.connection.commit()

        # Reload medication data
        self.medication_list = []
        self.load_medication_data()

        # Update the Treeview
        self.update_treeview()

    def remove_medication(self):
        if not self.check_authentication('admin'):
            return

        # Get selected item
        selected_item = self.tree.selection()

        if selected_item:
            # Remove medication from the database
            selected_medication_id = self.tree.item(selected_item, 'values')[1]
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM medications WHERE medication_id = ?', (selected_medication_id,))
            self.connection.commit()

            # Reload medication data
            self.medication_list = []
            self.load_medication_data()

            # Update the Treeview
            self.update_treeview()

    def update_treeview(self):
        # Clear the Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate the Treeview with updated data
        for medication in self.medication_list:
            self.tree.insert("", "end", values=medication)

    def sell_medication(self):
        if not self.check_authentication('cashier'):
            return

        # Get selected item
        selected_item = self.tree.selection()

        if selected_item:
            # Get medication details
            medication_details = self.tree.item(selected_item, 'values')
            medication_id, medication_name, quantity, price = medication_details[1:]

            # Prompt user for quantity to sell
            sell_quantity = simpledialog.askinteger("Sell Medication", "Enter quantity to sell:")

            if sell_quantity is not None:

                sell_quantity = int(sell_quantity)
                if sell_quantity <= quantity:
                    # Update quantity in the database
                    new_quantity = quantity - sell_quantity
                    cursor = self.connection.cursor()
                    cursor.execute('UPDATE medications SET quantity = ? WHERE medication_id = ?', (new_quantity, medication_id))
                    self.connection.commit()

                    # Record sale in the database
                    sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    total_price = sell_quantity * price
                    sale_data = (medication_id, sell_quantity, total_price, sale_date)
                    cursor.execute('INSERT INTO sales (medication_id, quantity, total_price, sale_date) VALUES (?, ?, ?, ?)', sale_data)
                    self.connection.commit()

                    # Reload medication data
                    self.medication_list = []
                    self.load_medication_data()

                    # Update the Treeview
                    self.update_treeview()
                else:
                    messagebox.showwarning("Error", "Not enough stock available.")
        else:
            messagebox.showwarning("Error", "Please select a medication to sell.")

    def update_medication(self):
        if not self.check_authentication('admin'):
            return

        # Get selected item
        selected_item = self.tree.selection()

        if selected_item:
            # Get medication details
            medication_details = self.tree.item(selected_item, 'values')
            medication_id, medication_name, quantity, price = medication_details[1:]

            # Prompt user for new quantity and price
            new_quantity = simpledialog.askinteger("Update Medication", "Enter new quantity:")
            new_price = simpledialog.askfloat("Update Medication", "Enter new price:")

            if new_quantity is not None and new_price is not None:
                new_quantity = int(new_quantity)

                # Update medication in the database
                cursor = self.connection.cursor()
                cursor.execute('UPDATE medications SET quantity = ?, price = ? WHERE medication_id = ?', (new_quantity, new_price, medication_id))
                self.connection.commit()

                # Reload medication data
                self.medication_list = []
                self.load_medication_data()

                # Update the Treeview
                self.update_treeview()
        else:
            messagebox.showwarning("Error", "Please select a medication to update.")

    def generate_invoice(self):
        if not self.check_authentication('cashier'):
            return

        # Get selected item
        selected_item = self.tree.selection()

        if selected_item:
            # Get medication details
            medication_details = self.tree.item(selected_item, 'values')
            medication_id, medication_name, quantity, price = medication_details[1:]

            # Prompt user for quantity sold
            sold_quantity = simpledialog.askinteger("Generate Invoice", "Enter quantity sold:")
            if sold_quantity is not None:
                sold_quantity = int(sold_quantity)
                total_amount = sold_quantity * price

                # Display the invoice
                invoice_text = f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                invoice_text += f"Medication ID: {medication_id}\n"
                invoice_text += f"Medication Name: {medication_name}\n"
                invoice_text += f"Quantity Sold: {sold_quantity}\n"
                invoice_text += f"Total Amount: ${total_amount:.2f}"

                messagebox.showinfo("Invoice", invoice_text)
        else:
            messagebox.showwarning("Error", "Please select a medication to generate an invoice.")

    def generate_reports(self):
        if not self.check_authentication('admin'):
            return

        # Generate sample data for reports (replace with actual data)
        sales_data = [(datetime(2023, 1, i).strftime('%Y-%m-%d'), random.randint(50, 200)) for i in range(1, 11)]

        # Create a simple line chart
        dates, quantities = zip(*sales_data)
        plt.plot(dates, quantities)
        plt.xlabel('Date')
        plt.ylabel('Quantity Sold')
        plt.title('Sales Trend Report')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Display the chart in a new window
        plt.show()

    def scan_barcode(self):
        if not self.check_authentication('cashier'):
            return

        messagebox.showinfo("Barcode Scanner", "Scan successful (placeholder message)")

    def manage_customers(self):
        if not self.check_authentication('admin'):
            return

        # Placeholder for customer management
        messagebox.showinfo("Customer Management", "Customer management feature is under construction (placeholder message)")

    def check_notifications(self):
        if not self.check_authentication('admin'):
            return

        # Placeholder for notifications
        messagebox.showinfo("Notifications", "No new notifications (placeholder message)")


if __name__ == "__main__":

    root = tk.Tk()
    app = PharmacyManagementSystem(root)
    root.mainloop()


