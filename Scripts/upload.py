import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import threading
import requests
import os
from jkn_drive_helper import (
    load_session, save_session, is_session_valid,
    login_guest, login_2fa, navigate_folder,
    upload_all_files, preload_js_assets, get_sharedfolder,
    create_remote_folder
)

USERNAME = 'andycahyonoputra@gmail.com'
PASSWORD = 'Rossidwi2404!@'
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

    def configure_headers(self):
        self.session.headers.update({
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

if __name__ == "__main__":
    app = JKNApp()
    app.mainloop()
