# This file is part of AutoDownloaderVedikaPDF.
# Copyright (C) 2025 Andy Cahyono Putra
# This program is distributed under the Aladdin Free Public License.
# See LICENSE file for more information.

import os
import tkinter as tk
from tkinter import messagebox

def run_ranap():
    try:
        root.destroy()
        from Scripts import ranap
    except ImportError:
        messagebox.showerror("Error", "Failed to import ranap. Please check if the module exists.")
def run_ralan():
    try:
        root.destroy()
        from Scripts import ralan
    except ImportError:
        messagebox.showerror("Error", "Failed to import ralan. Please check if the module exists.")


root = tk.Tk()
root.title("JOBS EASIER")
root.geometry("300x200")

label = tk.Label(root, text="Another Tools To Make Your Jobs Easier Python Version", wraplength=250)
label.pack(pady=10)

button_ranap = tk.Button(root, text="Ranap", command=run_ranap)
button_ranap.pack(pady=5)

button_ralan = tk.Button(root, text="Ralan", command=run_ralan)
button_ralan.pack(pady=5)


root.mainloop()