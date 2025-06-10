# This file is part of AutoDownloaderVedikaPDF.
# Copyright (C) 2025 Andy Cahyono Putra
# This program is distributed under the Aladdin Free Public License.
# See LICENSE file for more information.

import os
import re
import subprocess
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox
from bs4 import BeautifulSoup
from config_loader import Config
from Scripts import auth
import mysql.connector
import pyttsx3
import requests
from playwright.sync_api import sync_playwright
import sys
import threading

cfg = Config()

def fetch_identifiers(tanggal1):
    conn = mysql.connector.connect(host=cfg.Database.host, user=cfg.Database.user, password=cfg.Database.password, database=cfg.Database.database)
    cursor = conn.cursor()
    query = f"""
        SELECT no_rawat FROM mlite_vedika WHERE status = 'Pengajuan' 
        AND jenis = '2' AND (no_rkm_medis OR no_rawat OR nosep ) 
        AND tgl_registrasi BETWEEN '{tanggal1}' AND '{tanggal1}
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def render_pdf_with_playwright(html_content, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until='networkidle')
        page.pdf(path=output_path, format='A4', print_background=True)
        browser.close()

def generate_pdf(username, password, no_rawat, cookies, path_folder):
    try:
        modified_string = no_rawat.replace("/", "")
        url = f'{cfg.Url.mlite}/admin/vedika/pdf/{modified_string}'

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
        payload = f'username={username}&password={password}&login='

        response = requests.post(url, headers=headers, data=payload)
        html = response.text

        with open(f"debug_{modified_string}.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, 'html.parser')
        no_sep_value = None
        no_sep_text = soup.find(text=re.compile(r'No[.\s]?SEP[:：]?'))
        if no_sep_text:
            match = re.search(r'No\.SEP:\s*(\S+)', no_sep_text)
            if match:
                no_sep_value = match.group(1).replace('"', '')

        if not no_sep_value:
            return f"No.SEP tidak ditemukan untuk {no_rawat}"

        filename = f"{no_sep_value}.pdf"
        final_pdf = os.path.join(path_folder, filename)
        temp_filename = filename.replace(".pdf", "_temp.pdf")
        temp_pdf = os.path.join(path_folder, temp_filename)

        render_pdf_with_playwright(html, temp_pdf)

        result = subprocess.run(['qpdf', '--decode-level=generalized', temp_pdf, final_pdf], capture_output=True, text=True)
        os.remove(temp_pdf)

        if result.returncode != 0:
            return f"qpdf error untuk {no_sep_value}: {result.stderr}"

        return f"PDF siap: {final_pdf}"
    except Exception as e:
        return f'Error generate PDF {no_rawat}: {e}'

def worker(username, password, cookies, path_folder, results):
    for result in results:
        no_rawat = result[0]
        message = generate_pdf(username, password, no_rawat, cookies, path_folder)
        print(message)
    play_voice_until_close()
    messagebox.showinfo("Info", "Semua file telah diproses.")

def play_voice_until_close():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say("All job is done")
    engine.runAndWait()
    engine.stop()

def kembali_ke_menu():
    app.destroy()
    subprocess.Popen([sys.executable, "main.py"])

def process_files():
    tanggal1 = entry_tanggal1.get()
    cookies = entry_cookies.get()
    username = entry_username.get()
    password = entry_password.get()
    folder_name = entry_folder.get()
    path_folder = os.path.join(os.getcwd(), folder_name)

    if cookies and os.path.isfile(cookies):
        try:
            with open(cookies, 'r') as File:
                cookies_content = File.read().strip()
                entry_cookies.delete(0, 'end')
                entry_cookies.insert(0, cookies_content)
                cookies = cookies_content
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca cookies: {e}")
            return

    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    results = fetch_identifiers(tanggal1)

    if not results:
        messagebox.showinfo("Info", "Tidak ada data untuk tanggal tersebut.")
        return
    threading.Thread(target=worker, args=(username, password, cookies, path_folder, results)).start()

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

app = Tk()
app.title("Downloader PDF Ralan Non Upload")
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
