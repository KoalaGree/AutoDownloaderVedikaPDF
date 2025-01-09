import requests
import re
import time
import threading
import tkinter as tk
from tkinter import messagebox, filedialog

def send_whatsapp_message(nomorhp, pesan):
    url = "http://192.168.1.50/admin/api/kirimwa?t=9fd16f7bb528"
    payload = f'api_key=8de61ad3a426e272c123171e883f2090&sender=6285749008191&number={nomorhp}&message={pesan}'
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded',
        'Cookie': 'mlite=b3783d92d5d9e6d46e519285afe437cb',
        'DNT': '1',
        'Origin': 'http://192.168.1.50',
        'Referer': 'http://192.168.1.50/admin/pasien/manage?t=9fd16f7bb528',
        'User -Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"Pesan berhasil dikirim ke {nomorhp}: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat mengirim pesan ke {nomorhp}: {e}")
        return False

def send_messages_from_file(file_path, pesan, result_text):
    success_count = 0
    invalid_numbers = []

    with open(file_path, 'r') as file:
        nomorhp_list = file.readlines()
    
    for nomorhp in nomorhp_list:
        nomorhp = nomorhp.strip()  # Menghapus spasi dan karakter newline
        if re.match(r'^\d+$', nomorhp):  # Validasi nomor telepon (hanya angka)
            if send_whatsapp_message(nomorhp, pesan):
                success_count += 1
            time.sleep(5)  # Sleep to avoid hitting rate limits
        else:
            invalid_numbers.append(nomorhp)

    # Log invalid numbers to Failed.txt
    if invalid_numbers:
        with open("Failed.txt", "a") as failed_file:
            for number in invalid_numbers:
                failed_file.write(f"{number}\n")

    result_text.insert(tk.END, f"Pesan berhasil dikirim ke {success_count} nomor.\n")
    if invalid_numbers:
        result_text.insert(tk.END, f"Nomor tidak valid telah dicatat di 'Failed.txt'.\n")

def threaded_send_messages(file_path, pesan, result_text):
    if pesan:
        send_messages_from_file(file_path, pesan, result_text)
    else:
        messagebox.showerror("Error", "Pesan tidak boleh kosong.")

def browse_file(entry):
    file_path = filedialog.askopenfilename()
    entry.delete(0, tk.END)  # Clear the entry
    entry.insert(0, file_path)  # Insert the selected file path

def main():
    root = tk.Tk()
    root.title("WhatsApp Message Sender")

    tk.Label(root, text="Path File Nomor HP:").pack(pady=5)
    file_entry = tk.Entry(root, width=50)
    file_entry.pack(pady=5)

    tk.Button(root, text="Browse", command=lambda: browse_file(file_entry)).pack(pady=5)

    tk.Label(root, text="Pesan:").pack(pady=5)
    message_entry = tk.Entry(root, width=50)
    message_entry.pack(pady=5)

    result_text = tk.Text(root, height=10, width=60)
    result_text.pack(pady=5)

    def send_messages():
        file_path = file_entry.get()
        pesan = message_entry.get().strip()
        result_text.delete(1.0, tk.END)  # Clear previous results
        threading.Thread(target=threaded_send_messages, args=(file_path, pesan, result_text)).start()

    tk.Button(root, text="Kirim Pesan", command=send_messages).pack(pady=5)
    tk.Button(root, text="Keluar", command=root.quit).pack(pady=5)

    # Start the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()