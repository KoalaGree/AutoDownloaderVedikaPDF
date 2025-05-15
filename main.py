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
def upload():
    try:
        from Scripts.massupload import JKNApp
        root.destroy()  # Ini penting agar jendela utama ditutup sebelum buka GUI baru
        app = JKNApp()
        app.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Gagal menjalankan Mass Upload:\n{str(e)}")
def run_ralan_noupload():
    try:
        root.destroy()
        from Scripts import ralannoupload
    except ImportError:
        messagebox.showerror("Error", "Failed to import ralannoupload. Please check if module exists.")
def run_ranap_noupload():
    try:
        root.destroy()
        from Scripts import ranapnoupload
    except ImportError:
        messagebox.showerror("Error", "Failed to import ranapnoupload. Please check if module exists.")


root = tk.Tk()
root.title("JOBS EASIER")
root.geometry("500x300")

label = tk.Label(root, text="Another Tools To Make Your Jobs Easier Python Version", wraplength=250)
label.pack(pady=10)

button_ranap = tk.Button(root, text="Ranap (Dengan Upload JKN)", command=run_ranap)
button_ranap.pack(pady=5)

button_ralan = tk.Button(root, text="Ralan (Dengan Upload JKN)", command=run_ralan)
button_ralan.pack(pady=5)

button_mass_upload = tk.Button(root, text="Mass Upload", command=upload)
button_mass_upload.pack(pady=5)

button_ralan_noupload = tk.Button(root, text="Ralan (Tanpa Upload)", command=run_ralan_noupload)
button_ralan_noupload.pack(pady=5)

button_ranap_noupload = tk.Button(root, text="Ranap (Tanpa Upload)", command=run_ranap_noupload)
button_ranap_noupload.pack(pady=5)
root.mainloop()