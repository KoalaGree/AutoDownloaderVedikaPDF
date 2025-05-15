# === jkn_drive_helper.py (inline) ===
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import os
from urllib.parse import quote_plus
from requests_toolbelt.multipart.encoder import MultipartEncoder
import pickle
from queue import Queue
from config_loader import Config
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import threading
import subprocess
import sys



cfg = Config()

def get_epochtimes():
    return int(datetime.now().timestamp())

def save_session(session, filename='session.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(session.cookies.get_dict(), f)


def load_session(session, filename='session.pkl'):
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            try:
                cookies_dict = pickle.load(f)
                if isinstance(cookies_dict, dict):
                    session.cookies.update(cookies_dict)
                    return True
                else:
                    print("[ERROR] Data session bukan dictionary. Menghapus file session...")
            except Exception as e:
                print(f"[ERROR] Gagal memuat session: {e}. File akan dihapus.")
        try:
            os.remove(filename)
            print("[INFO] File session rusak telah dihapus.")
        except Exception as e:
            print(f"[ERROR] Gagal menghapus file session: {e}")
    return False


def is_session_valid(session, headers):
    try:
        response = session.post(
            f"{cfg.Url.jkn}/core/getfilelist?time={get_epochtimes()}",
            headers=headers,
            data="path=/SHARED&start=0&limit=1"
        )
        if response.status_code == 200 and "<entry>" in response.text:
            return True
    except Exception as e:
        print(f"[ERROR] Cek sesi gagal: {e}")
    return False

def login_guest(session, username, password, headers):
    epoch = get_epochtimes()
    endpoint = f"{cfg.Url.jkn}/core/loginguest?time={epoch}"
    payload = f"userid={username}&password={password}&passwordType=password&g-recaptcha-response=&tfa=1"
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

def login_2fa(session, username, token_message, token_2fa, headers):
    epoch = get_epochtimes()
    endpoint = f"{cfg.Url.jkn}/core/2falogin?time={epoch}"
    payload = f"userid={username}&code={token_2fa}&token={token_message}&tfa=1"
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
    payload = f"path={path}&start=0&limit=100&sendcommentinfo=1&sendmetadatasetinfo=1&search=&sortby=name&sortdir=1&sendfavinfo=1&sendaboutinfo=1"
    response = session.post(endpoint, headers=headers, data=payload)

    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            entries = []
            for entry in root.findall('.//entry'):
                entry_type = entry.find('type')
                name = entry.find('name')
                fullpath = entry.find('path')
                if entry_type is not None and entry_type.text == 'dir' and name is not None and fullpath is not None:
                    entries.append({'name': name.text, 'path': fullpath.text})
            return entries
        except ET.ParseError as e:
            print(f"[XML ERROR] {e}")
    else:
        print(f"[HTTP ERROR] {response.status_code}")
    return []

def navigate_folder(session, current_path, headers):
    while True:
        folders = get_sharedfolder(session, current_path, headers)
        if not folders:
            print(f"[INFO] Tidak ada folder di {current_path}")
            return current_path

        print(f"\n[ISI FOLDER: {current_path}]:")
        for idx, folder in enumerate(folders, 1):
            print(f"{idx}. {folder['name']}")
        print("0. Pilih folder ini")

        try:
            choice = int(input("Pilih nomor folder untuk masuk, atau 0 untuk pilih folder ini: "))
            if choice == 0:
                return current_path
            elif 1 <= choice <= len(folders):
                selected = folders[choice - 1]
                current_path = selected['path']
            else:
                print("[ERROR] Pilihan tidak valid.")
        except ValueError:
            print("[ERROR] Input harus berupa angka.")

def preload_js_assets(session):
    js1 = "https://jkn-drive.bpjs-kesehatan.go.id/ui/core/js/9858.2fe9443a.js"
    js2 = "https://jkn-drive.bpjs-kesehatan.go.id/ui/core/js/1971.022938ab.js"

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

def create_remote_folder(session, headers, parent_path, folder_name):
    epoch = get_epochtimes()
    encoded_path = quote_plus(parent_path)
    encoded_name = quote_plus(folder_name)
    endpoint = f"{cfg.Url.jkn}/core/createfolder?time={epoch}&path={encoded_path}&name={encoded_name}"

    response = session.post(endpoint, headers=headers)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            result = root.find(".//result")
            if result is not None and result.text == "1":
                print(f"[INFO] Folder dibuat: {parent_path}/{folder_name}")
                return True
        except ET.ParseError:
            pass
    return False

def upload_file(session, headers, local_file_path, remote_path):
    filename = os.path.basename(local_file_path)
    try:
        with open(local_file_path, 'rb') as f:
            size = os.path.getsize(local_file_path)
            encoded_path = quote_plus(remote_path)
            encoded_filename = quote_plus(filename)
            current_time_iso = datetime.utcnow().isoformat() + "Z"

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
            upload_headers['Referer'] = "https://jkn-drive.bpjs-kesehatan.go.id/ui/core/js/9858.2fe9443a.js"
            upload_headers['Accept'] = "application/json"

            response = session.post(endpoint, headers=upload_headers, data=m)

            if response.status_code == 200:
                print(f"[SUKSES] Upload: {filename} ke {remote_path}")
            else:
                print(f"[GAGAL] Upload: {filename} ke {remote_path} - Status: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"[ERROR] Gagal membuka atau upload file {filename} ke {remote_path}: {e}")

def upload_all_files(session, headers, root_path, base_remote_path):
    if not os.path.isdir(root_path):
        print(f"[ERROR] Folder lokal tidak ditemukan: {root_path}")
        return

    file_queue = Queue()
    created_folders = set()
    folder_lock = threading.Lock()

    # Step 1: Walk through all files and queue them
    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            if os.path.isfile(full_path):
                relative_folder = os.path.relpath(dirpath, root_path).replace("\\", "/").strip(".")
                if relative_folder == "":
                    target_remote_path = base_remote_path.rstrip('/')
                else:
                    target_remote_path = f"{base_remote_path}/{relative_folder}".rstrip('/')

                # Queue the file along with its intended remote path
                file_queue.put((full_path, target_remote_path))

    # Step 2: Worker function to upload files
    def worker():
        while not file_queue.empty():
            try:
                full_path, target_remote_path = file_queue.get_nowait()

                # Step 3: Cek dan buat folder jika belum ada
                with folder_lock:
                    parts = target_remote_path.replace(base_remote_path, "").strip("/").split("/")
                    current_path = base_remote_path
                    for part in parts:
                        check_path = f"{current_path}/{part}"
                        if check_path not in created_folders:
                            existing = get_sharedfolder(session, current_path, headers)
                            if not any(f['name'] == part for f in existing):
                                create_remote_folder(session, headers, current_path, part)
                            created_folders.add(check_path)
                        current_path = check_path

                print(f"[INFO] Uploading: {full_path} -> {target_remote_path}")
                upload_file(session, headers, full_path, target_remote_path)
            except Exception as e:
                print(f"[ERROR] Worker exception: {e}")
            finally:
                file_queue.task_done()

    # Step 4: Jalankan 10 thread
    threads = []
    for _ in range(50):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Tunggu semua thread selesai
    for t in threads:
        t.join()

    print("[INFO] Semua file selesai diupload.")


USERNAME = cfg.UserPass.username
PASSWORD = cfg.UserPass.password
SESSION_FILE = 'session.pkl'

class JKNApp(tk.Tk):
    def __init__(self):
        super().__init__()  # Hanya perlu memanggil super() untuk mendefinisikan root
        self.title("Uploader ke JKN Drive")
        self.geometry("500x300")

        self.session = requests.Session()
        self.configure_headers()

        self.remote_path = ""
        self.local_folder = ""

        self.status = tk.Label(self, text="Status: Siap", anchor="w")
        self.status.pack(fill=tk.X, pady=5)

        tk.Button(self, text="1. Pilih Folder Lokal", command=self.pilih_folder_lokal).pack(pady=5)
        tk.Button(self, text="2. Login & Pilih Folder Remote", command=self.login_dan_pilih_folder).pack(pady=5)
        tk.Button(self, text="3. Upload Semua File", command=self.upload_file).pack(pady=5)
        tk.Button(self, text="⬅ Kembali ke Menu Utama", command=self.kembali_ke_menu).pack(pady=10)
        
    def configure_headers(self):
        self.session.headers.update({
            'accept': 'application/x-www-form-cfg.Url.jknencoded',
            'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-cfg.Url.jknencoded',
            'origin': 'https://jkn-drive.bpjs-kesehatan.go.id',
            'referer': 'https://jkn-drive.bpjs-kesehatan.go.id/ui/core/index.html',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0',
            'x-requested-with': 'XMLHttpRequest',
            'X-XSRF-TOKEN': 'NONE'
        })

    def pilih_folder_lokal(self):
        folder = filedialog.askdirectory()
        if folder:
            self.local_folder = folder
            self.status.config(text=f"Folder Lokal: {folder}")

    def login_dan_pilih_folder(self):
        def run():
            self.status.config(text="Mengecek sesi lama...")
            if load_session(self.session, SESSION_FILE) and is_session_valid(self.session, self.session.headers):
                self.status.config(text="Sesi lama valid.")
                self.selesai_login()
            else:
                self.status.config(text="Login ulang diperlukan...")
                token = login_guest(self.session, USERNAME, PASSWORD, self.session.headers)
                if not token:
                    self.status.config(text="Login guest gagal.")
                    messagebox.showerror("Login Gagal", "Login guest gagal.")
                    return
                
                # minta 2FA di thread utama
                self.after(0, lambda: self.minta_token_2fa(token))

        threading.Thread(target=run).start()

    def minta_token_2fa(self, token_guest):
        kode = simpledialog.askstring("Token 2FA", "Masukkan kode 2FA dari email/WA:", parent=self)
        if not kode:
            messagebox.showinfo("Login dibatalkan", "Token 2FA tidak dimasukkan.")
            return

        def lanjutkan_login():
            if login_2fa(self.session, USERNAME, token_guest, kode, self.session.headers):
                save_session(self.session, SESSION_FILE)
                self.status.config(text="Login berhasil. Sesi disimpan.")
                self.selesai_login()
            else:
                self.status.config(text="Token 2FA salah.")
                messagebox.showerror("Login Gagal", "Token 2FA salah.")

        threading.Thread(target=lanjutkan_login).start()

    def selesai_login(self):
        selected_remote_base = navigate_folder(self.session, "/SHARED", self.session.headers)
        local_folder_name = os.path.basename(self.local_folder.rstrip("/\\"))

        # Cek apakah folder lokal sudah ada di remote
        existing_folders = get_sharedfolder(self.session, selected_remote_base, self.session.headers)
        target_folder_path = f"{selected_remote_base}/{local_folder_name}"

        if not any(f["name"] == local_folder_name for f in existing_folders):
            created = create_remote_folder(self.session, self.session.headers, selected_remote_base, local_folder_name)
            if not created:
                self.status.config(text=f"Gagal membuat folder remote: {target_folder_path}")
                messagebox.showerror("Gagal", f"Folder '{local_folder_name}' tidak bisa dibuat.")
                return
            else:
                print(f"[INFO] Folder remote dibuat: {target_folder_path}")
        else:
            print(f"[INFO] Folder remote sudah ada: {target_folder_path}")

        self.remote_path = target_folder_path
        self.status.config(text=f"Folder Remote: {self.remote_path}")


    def upload_file(self):
        if not self.local_folder or not self.remote_path:
            messagebox.showwarning("Peringatan", "Pilih folder lokal dan remote terlebih dahulu.")
            return

        def run():
            self.status.config(text="Mengunggah file...")
            upload_all_files(self.session, self.session.headers, self.local_folder, self.remote_path)
            self.status.config(text="Upload selesai.")

        threading.Thread(target=run).start()
    
    def kembali_ke_menu(self):
        self.destroy()  # Tutup jendela ini
        subprocess.Popen([sys.executable, "main.py"])  # Jalankan ulang main.py


if __name__ == "__main__":
    app = JKNApp()
    app.mainloop()