import os
import tkinter as tk
from tkinter import messagebox

def run_ranap():
    try:
        from Scripts import ranap
        # Call a function from ranap if needed
        # messagebox.showinfo("Success", "Ranap module imported successfully!")
    except ImportError:
        messagebox.showerror("Error", "Failed to import ranap. Please check if the module exists.")

def run_ralan():
    try:
        from Scripts import ralan
        # Call a function from ralan if needed
        # messagebox.showinfo("Success", "Ralan module imported successfully!")
    except ImportError:
        messagebox.showerror("Error", "Failed to import ralan. Please check if the module exists.")

def run_Auth():
    try:
        from Scripts import auth
    except ImportError:
        messagebox.showerror("Error", "Failed to import Auth. Please Check if the module exists")

# Create the main window
root = tk.Tk()
root.title("Job Tools")
root.geometry("300x200")

# Create a label for the title
label = tk.Label(root, text="Another Tools For Make Your Jobs Easier Python Version", wraplength=250)
label.pack(pady=10)

# Create buttons for each option
button_ranap = tk.Button(root, text="Ranap", command=run_ranap)
button_ranap.pack(pady=5)

button_ralan = tk.Button(root, text="Ralan", command=run_ralan)
button_ralan.pack(pady=5)

button_ralan = tk.Button(root, text="Get Cookies", command=run_Auth)
button_ralan.pack(pady=5)

# Start the GUI event loop
root.mainloop()