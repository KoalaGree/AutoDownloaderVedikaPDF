import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import os
from urllib.parse import quote_plus
from requests_toolbelt.multipart.encoder import MultipartEncoder
import pickle
from queue import Queue
import threading

url = "https://jkn-drive.bpjs-kesehatan.go.id"

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
            f"{url}/core/getfilelist?time={get_epochtimes()}",
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
    endpoint = f"{url}/core/loginguest?time={epoch}"
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
    endpoint = f"{url}/core/2falogin?time={epoch}"
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
    endpoint = f"{url}/core/getfilelist?time={epoch}"
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
    endpoint = f"{url}/core/createfolder?time={epoch}&path={encoded_path}&name={encoded_name}"

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
                f"{url}/core/upload"
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
