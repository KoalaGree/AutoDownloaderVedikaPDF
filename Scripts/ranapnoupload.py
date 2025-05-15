# This file is part of AutoDownloaderVedikaPDF.
# Copyright (C) 2025 Andy Cahyono Putra
# This program is distributed under the Aladdin Free Public License.
# See LICENSE file for more information.

import os
import requests
import re
from bs4 import BeautifulSoup
import pdfkit
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox, simpledialog, Listbox, Scrollbar, Toplevel
import mysql.connector
from urllib.parse import quote_plus
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from requests_toolbelt.multipart.encoder import MultipartEncoder
from Scripts import auth  
from config_loader import Config
import pyttsx3
import subprocess
import sys
import threading


cfg = Config()
config = pdfkit.configuration(wkhtmltopdf=cfg.Paths.wkhtmlfolder)

def fetch_identifiers(tanggal1):
    conn = mysql.connector.connect(host=cfg.Database.host, user=cfg.Database.user, password=cfg.Database.password, database=cfg.Database.database)
    cursor = conn.cursor()
    query = f"""
        SELECT * FROM mlite_vedika WHERE status = 'Pengajuan' AND jenis = '1' 
        AND (no_rkm_medis OR no_rawat OR nosep) 
        AND no_rawat IN (SELECT no_rawat FROM kamar_inap WHERE tgl_keluar BETWEEN '{tanggal1}' AND '{tanggal1}' AND kamar_inap.stts_pulang LIKE '%%')
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def generate_pdf(username, password, no_rawat, cookies, path_folder):
    try:
        modified_string = no_rawat.replace("/", "")
        url = f'{cfg.Url.mlite}/admin/vedika/pdf/{modified_string}'

        payload = f'username={username}&password={password}&login='
        headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': cookies,
                'DNT': '1',
                'Origin': cfg.Url.mlite,
                'Referer': cfg.Url.mlite,
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tr_element = soup.find('tr', class_='isi-norawat')

            if tr_element:
                script_elements = soup.find_all('script')
                no_sep_value = None

                for script in script_elements:
                    if 'No.SEP' in script.text:
                        match = re.search(r'No\.SEP:\s*(\S+)', script.text)
                        if match:
                            no_sep_value = match.group(1).replace('"', '')
                            break

                if no_sep_value:
                    pdf_filename = f'{no_sep_value}.pdf'
                    pdf_path = os.path.normpath(os.path.join(path_folder, pdf_filename))
                    path_new = pdf_path.replace("\\", "/")

                    # Generate PDF
                    pdfkit.from_string(response.text, pdf_path, configuration=config)
                    return path_new
                else:
                    return f"No.SEP tidak ditemukan di {url}"
            else:
                return 'Element <tr class="isi-norawat"> tidak ditemukan'
        else:
            return f'Error: Received status code {response.status_code} for URL: {url}'
    except Exception as e:
        return f'An error occurred: {e}'

def select_cookies():
    file_selected = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_selected:
        entry_cookies.delete(0, 'end')
        entry_cookies.insert(0, file_selected)

def ambil_cookies():
    username = entry_username.get()
    password = entry_password.get()
    cookies = auth.auth(username, password)
    if cookies:
        entry_cookies.delete(0, 'end')
        entry_cookies.insert(0, cookies)
        messagebox.showinfo("Cookies", f"Cookies berhasil diambil:\n{cookies}")
    else:
        messagebox.showerror("Gagal", "Gagal mengambil cookies.")

def play_voice_until_close():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150) 
    def on_end(name, completed):
        if completed:
            engine.stop()
    engine.connect('finished-utterance', on_end)
    while True:
        engine.say("All job is done")
        engine.runAndWait()
        if messagebox.askokcancel("Selesai", "Semua file telah diproses dan diupload. Klik OK untuk selesai."):
            break
    engine.stop()

def kembali_ke_menu():
    app.destroy()  # Tutup jendela ini
    subprocess.Popen([sys.executable, "main.py"])  # Jalankan ulang main.py

def process_files():
    tanggal1 = entry_tanggal1.get()
    cookies = entry_cookies.get()
    username = entry_username.get()
    password = entry_password.get()

    folder_name = entry_folder.get()

    path_folder = os.path.join(os.getcwd(), folder_name)
    if cookies:
        try:
            with open(cookies, 'r') as File:
                cookies_content = File.read
                if isinstance(cookies_content, str):
                    cookies_content = cookies_content.strip()
                    entry_cookies.delete(0, 'end')
                    entry_cookies.insert(0, cookies_content) 
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read the .txt file: {e}")
            return
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    results = fetch_identifiers(tanggal1)

    if not results:
        messagebox.showinfo("Info", "No records found for the given date range.")
        return

    def worker():
        for result in results:
            no_rawat = result[0]
            message = generate_pdf(username, password, no_rawat, cookies, path_folder)
            print(message)
        quit
        messagebox.showinfo("Info", "All PDFs have been processed.")
    threading.Thread(target=worker).start()
    play_voice_until_close()



app = Tk()
app.title("PDF Generator dan Upload")
app.geometry("500x400")

Label(app, text="Tanggal Awal:").grid(row=0, column=0, sticky='e')
entry_tanggal1 = Entry(app)
entry_tanggal1.grid(row=0, column=1)

Label(app, text="Username RS:").grid(row=2, column=0, sticky='e')
entry_username = Entry(app)
entry_username.grid(row=2, column=1)

Label(app, text="Password RS:").grid(row=3, column=0, sticky='e')
entry_password = Entry(app, show='*')
entry_password.grid(row=3, column=1)

Label(app, text="Folder Simpan PDF:").grid(row=4, column=0, sticky='e')
entry_folder = Entry(app)
entry_folder.grid(row=4, column=1)
Button(app, text="Pilih Folder", command=lambda: entry_folder.insert(0, filedialog.askdirectory())).grid(row=4, column=2)

Label(app, text="Cookies File:").grid(row=5, column=0, sticky='e')
entry_cookies = Entry(app)
entry_cookies.grid(row=5, column=1)
Button(app, text="Pilih Cookies", command=select_cookies).grid(row=5, column=2)
Button(app, text="Ambil Cookies", command=ambil_cookies).grid(row=5, column=3)


Button(app, text="Proses", command=process_files).grid(row=6, column=1, pady=20)
Button(app, text="⬅ Kembali ke Menu Utama", command=kembali_ke_menu).grid(row=6, column=2, pady=20)

app.mainloop()
