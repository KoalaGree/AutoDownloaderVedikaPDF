# This file is part of AutoDownloaderVedikaPDF.
# Copyright (C) 2025 Andy Cahyono Putra
# This program is distributed under the Aladdin Free Public License.
# See LICENSE file for more information.

import os
import requests
import re
from bs4 import BeautifulSoup
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
from playwright.sync_api import sync_playwright



cfg = Config()

def render_pdf_with_playwright(html_content, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until='networkidle')
        page.pdf(path=output_path, format='A4', print_background=True)
        browser.close()

def get_epochtimes():
    return int(datetime.now().timestamp())

def login_guest(session, usernameJKN, passwordJKN, headers):
    epoch = get_epochtimes()
    endpoint = f"{cfg.Url.jkn}/core/loginguest?time={epoch}"
    payload = f"userid={usernameJKN}&password={passwordJKN}&passwordType=password&g-recaptcha-response=&tfa=1"
    response = session.post(endpoint, headers=headers, data=payload)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            message = root.find('.//message')
            return message.text if message is not None else None
        except ET.ParseError as e:
            print(f"[XML ERROR] {e}")
    else:
        print(f"[HTTP ERROR] {response.status_code}")
    return None

def login_2fa(session, usernameJKN, token_message, token_2fa, headers):
    epoch = get_epochtimes()
    endpoint = f"{cfg.Url.jkn}/core/2falogin?time={epoch}"
    payload = f"userid={usernameJKN}&code={token_2fa}&token={token_message}&tfa=1"
    response = session.post(endpoint, headers=headers, data=payload)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            result = root.find('.//result')
            return result.text == '1'
        except ET.ParseError as e:
            print(f"[XML ERROR] {e}")
    else:
        print(f"[HTTP ERROR] {response.status_code}")
    return False

def get_sharedfolder(session, path, headers):
    epoch = get_epochtimes()
    endpoint = f"{cfg.Url.jkn}/core/getfilelist?time={epoch}"
    payload = f"path={path}&start=0&limit=100"
    response = session.post(endpoint, headers=headers, data=payload)
    entries = []
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            for entry in root.findall('.//entry'):
                if entry.find('type').text == 'dir':
                    entries.append({
                        'name': entry.find('name').text,
                        'path': entry.find('path').text
                    })
        except ET.ParseError as e:
            print(f"[XML ERROR] {e}")
    return entries


def create_folder(session, headers, parent_path, new_folder_name):
    try:
        epoch = get_epochtimes()
        endpoint = f"{cfg.Url.jkn}/core/createfolder?time={epoch}"
        
        payload = {
            "name": new_folder_name,
            "path": parent_path,
            "date": datetime.now().isoformat()
        }

        response = session.post(endpoint, headers=headers, data=payload)
        
        if response.status_code == 200:
            print(f"[INFO] Folder '{new_folder_name}' berhasil dibuat di {parent_path}")
            return True
        else:
            print(f"[ERROR] Gagal membuat folder '{new_folder_name}' - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan saat membuat folder: {e}")
        return False


def select_remote_folder(session, headers, base_path=cfg.Paths.base_path):
    def on_select(event):
        selected_index = listbox.curselection()
        if selected_index:
            selected = folder_entries[selected_index[0]]
            new_path = selected['path']
            refresh_folder(new_path)

    def refresh_folder(current_path_val):
        nonlocal current_path, folder_entries
        folder_entries = get_sharedfolder(session, current_path_val, headers)
        current_path = current_path_val
        listbox.delete(0, 'end')
        for folder in folder_entries:
            listbox.insert('end', folder['name'])

    def create_new_folder():
        new_folder_name = simpledialog.askstring("Nama Folder", "Masukkan nama folder baru:")
        if new_folder_name:
            if create_folder(session, headers, current_path, new_folder_name):
                refresh_folder(current_path)

    selected_path = None
    current_path = base_path
    folder_entries = []
    win = Toplevel(app)
    win.title("Pilih Folder Upload")

    def go_back():
        nonlocal current_path
        if current_path.strip('/') != base_path.strip('/'):
            parent = '/'.join(current_path.strip('/').split('/')[:-1])
            parent_path = f'/{parent}/' if parent else base_path
            refresh_folder(parent_path)

    def choose_folder():
        nonlocal selected_path
        selected_path = current_path
        win.destroy()
    Button(win, text="Kembali", command=go_back).pack(pady=5)
    scrollbar = Scrollbar(win)
    scrollbar.pack(side='right', fill='y')
    listbox = Listbox(win, yscrollcommand=scrollbar.set, width=50)
    listbox.pack()
    scrollbar.config(command=listbox.yview)
    listbox.bind("<Double-1>", on_select)
    Button(win, text="Pilih Folder Ini", command=choose_folder).pack(pady=5)
    Button(win, text="Buat Folder Baru", command=create_new_folder).pack(pady=5)
    refresh_folder(current_path)
    win.wait_window()
    return selected_path


def fetch_identifiers(tanggal1):
    conn = mysql.connector.connect(host=cfg.Database.host, user=cfg.Database.user, password=cfg.Database.password, database=cfg.Database.database)
    cursor = conn.cursor()
    query = f"""
        SELECT no_rawat FROM mlite_vedika WHERE status = 'Pengajuan' AND jenis = '1' 
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
        return f'An error occurred: {e}'

def upload_file(session, headers, pdf_path, remote_path):
    try:
        with open(pdf_path, 'rb') as f:
            filename = os.path.basename(pdf_path)
            size = os.path.getsize(pdf_path)
            print(size)
            encoded_path = quote_plus(str(remote_path))
            print 
            encoded_filename = quote_plus(str(filename))
            current_time_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

            endpoint = (
                f"{cfg.Url.jkn}/core/upload"
                f"?appname=explorer"
                f"&filesize={size}"
                f"&path={encoded_path}"
                f"&uploadpath="
                f"&offset=0"
                f"&date={current_time_iso}"
                f"&filename={encoded_filename}"
                f"&complete=1"
            )

            m = MultipartEncoder(
                fields={'filedata': (filename, f, "application/pdf")},
                boundary="----WebKitFormBoundarymZWe6678TZzxezEy"
            )

            upload_headers = headers.copy()
            upload_headers['Content-Type'] = m.content_type
            upload_headers['Referer'] = f'{cfg.Url.jkn}/ui/core/js/9858.2fe9443a.js'
            upload_headers['Accept'] = "application/json"

            response = session.post(endpoint, headers=upload_headers, data=m)
            if response.status_code == 200:
                print(f"[SUKSES] Upload: {filename}")
            else:
                print(f"[GAGAL] Upload: {filename} - Status: {response.status_code}")
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")


def select_cookies():
    file_selected = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_selected:
        entry_cookies.delete(0, 'end')
        entry_cookies.insert(0, file_selected)

def preload_js_assets(session):
    js1 = f'{cfg.Url.jkn}/ui/core/js/9858.2fe9443a.js'
    js2 = f'{cfg.Url.jkn}/ui/core/js/1971.022938ab.js'

    headers_js = {
        'Accept': '*/*',
        'User-Agent': session.headers['user-agent'],
        'Referer': js1,
    }

    try:
        r1 = session.get(js1, headers=headers_js)
        r2 = session.get(js2, headers=headers_js)
        print(f"[INFO] JS preload status: {r1.status_code}, {r2.status_code}")
    except Exception as e:
        print(f"[ERROR] Gagal preload JS: {e}")


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
    username = entry_username.get()
    password = entry_password.get()
    usernameJKN = entry_usernamejkn.get()
    passwordJKN = entry_passwordjkn.get()
    cookies = entry_cookies.get()
    folder_pdf = entry_folder.get()

    if not os.path.exists(folder_pdf):
        os.makedirs(folder_pdf)

    identifiers = fetch_identifiers(tanggal1)
    if not identifiers:
        messagebox.showerror("Error", "Tanggal awal dan tanggal akhir harus diisi.")
        return

    session = requests.Session()
    session.headers.update({
        'accept': 'application/x-www-form-urlencoded',
        'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://jkn-drive.bpjs-kesehatan.go.id',
        'referer': 'https://jkn-drive.bpjs-kesehatan.go.id/ui/core/index.html',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'X-XSRF-TOKEN': 'NONE'
    })


    token_message = login_guest(session, usernameJKN, passwordJKN, session.headers)
    token_2fa = simpledialog.askstring("2FA", "Masukkan kode 2FA:")
    if not login_2fa(session, usernameJKN, token_message, token_2fa, session.headers):
        messagebox.showerror("Error", "Login 2FA gagal.")
        return

    remote_folder = select_remote_folder(session, session.headers) 
    print(f"Processing {len(identifiers)}")
    for (no_rawat,) in identifiers:
        pdf_path = generate_pdf(username, password, no_rawat, cookies, folder_pdf)
        if pdf_path:
            preload_js_assets(session)
            upload_file(session, session.headers, pdf_path, remote_folder)
    play_voice_until_close()


app = Tk()
app.title("Downloader dan Uploader PDF JKN DRIVE ( Ranap )")
app.geometry("500x400")

Label(app, text="Tanggal Awal:").grid(row=0, column=0, sticky='e')
entry_tanggal1 = Entry(app)
entry_tanggal1.grid(row=0, column=1)

Label(app, text="Username RS: ").grid(row=1, column=0, sticky='e')
entry_username = Entry(app)
entry_username.grid(row=1, column=1)

Label(app, text="Password RS:").grid(row=2, column=0, sticky='e')
entry_password = Entry(app, show='*')
entry_password.grid(row=2, column=1)

Label(app, text="Username Drive:").grid(row=3, column=0, sticky='e')
entry_usernamejkn = Entry(app)
entry_usernamejkn.grid(row=3, column=1)

Label(app, text="Password Drive:").grid(row=4, column=0, sticky='e')
entry_passwordjkn = Entry(app, show='*')
entry_passwordjkn.grid(row=4, column=1)

Label(app, text="Folder Simpan PDF:").grid(row=5, column=0, sticky='e')
entry_folder = Entry(app)
entry_folder.grid(row=5, column=1)
Button(app, text="Pilih Folder", command=lambda: entry_folder.insert(0, filedialog.askdirectory())).grid(row=5, column=2)

Label(app, text="Cookies File:").grid(row=6, column=0, sticky='e')
entry_cookies = Entry(app)
entry_cookies.grid(row=6, column=1)
Button(app, text="Pilih Cookies", command=select_cookies).grid(row=6, column=2)
Button(app, text="Ambil Cookies", command=ambil_cookies).grid(row=6, column=3)

Button(app, text="Proses", command=process_files).grid(row=7, column=1, pady=20)
Button(app, text="⬅ Kembali ke Menu Utama", command=kembali_ke_menu).grid(row=7, column=2, pady=20)


app.mainloop()
