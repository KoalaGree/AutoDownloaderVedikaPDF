import requests
import os
import threading
import re
from bs4 import BeautifulSoup
import pdfkit
from tkinter import Tk, Label, Entry, Button, messagebox
from tkinter import filedialog  # Import filedialog for folder selection
import mysql.connector

# Database connection parameters
DB_HOST = ''
DB_USER = ''
DB_PASSWORD = ''
DB_NAME = ''

# PDF configuration
path_wkthmltopdf = b'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)

def fetch_identifiers(tanggal1, tanggal2):
    # Connect to the database
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()

    # Fetch identifiers from the database
    query = f"""
        SELECT
        no_rawat 
    FROM
        mlite_vedika 
    WHERE
        STATUS = 'Pengajuan' 
        AND jenis = '1' 
        AND (
            no_rkm_medis 
            OR no_rawat
        OR nosep ) 
        AND no_rawat IN (
        SELECT
            no_rawat 
        FROM
            kamar_inap 
        WHERE
            tgl_keluar BETWEEN '{tanggal1}' 
        AND '{tanggal2}' 
        AND kamar_inap.stts_pulang LIKE '%%')
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def generate_pdf(username, password, no_rawat, cookies, path_folder):
    try:
        modified_string = no_rawat.replace("/", "")
        url = "http://192.168.1.50/admin/vedika/pdf/{}".format(modified_string)

        payload = f'username={username}&password={password}&login='
        headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': cookies,
                'DNT': '1',
                'Origin': 'http://192.168.1.50',
                'Referer': 'http://192.168.1.50/',
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
                    pdf_path = os.path.join(path_folder, pdf_filename)

                    # Generate PDF
                    pdfkit.from_string(response.text, pdf_path, configuration=config)
                    return f'File {pdf_filename} berhasil diunduh'
                else:
                    return f"No.SEP tidak ditemukan di {url}"
            else:
                return 'Element <tr class="isi-norawat"> tidak ditemukan'
        else:
            return f'Error: Received status code {response.status_code} for URL: {url}'
    except Exception as e:
        return f'An error occurred: {e}'

def process_data():
    tanggal1 = entry_tanggal1.get()
    tanggal2 = entry_tanggal2.get()
    username = entry_username.get()
    password = entry_password.get()
    cookies = entry_cookies.get()
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

    results = fetch_identifiers(tanggal1, tanggal2)

    if not results:
        messagebox.showinfo("Info", "No records found for the given date range.")
        return

    def worker():
        for result in results:
            no_rawat = result[0]
            message = generate_pdf(username, password, no_rawat, cookies, path_folder)
            print(message)

        messagebox.showinfo("Info", "All PDFs have been processed.")

    threading.Thread(target=worker).start()

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry_folder.delete(0, 'end')
        entry_folder.insert(0, folder_selected)
def select_cookies():
    file_selected = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_selected:
        entry_cookies.delete(0, 'end')
        entry_cookies.insert(0, file_selected)

app = Tk()
app.title("PDF Generator")
app.geometry("400x400")

# Create and place labels and entry fields
Label(app, text="Input Tanggal Awal:").grid(row=0, column=0, pady=5, sticky='e')
entry_tanggal1 = Entry(app)
entry_tanggal1.grid(row=0, column=1, pady=5)

Label(app, text="Input Tanggal Akhir:").grid(row=1, column=0, pady=5, sticky='e')
entry_tanggal2 = Entry(app)
entry_tanggal2.grid(row=1, column=1, pady=5)


Label(app, text="Pastekan Cookies:").grid(row=2, column=0, pady=5, sticky='e')
entry_cookies = Entry(app)
entry_cookies.grid(row=2, column=1, pady=5)

button_select_folder2 = Button(app, text="Browse", command=select_cookies)
button_select_folder2.grid(row=2, column=2, padx=5)


Label(app, text="Pilih Folder:").grid(row=3, column=0, pady=5, sticky='e')
entry_folder = Entry(app)
entry_folder.grid(row=3, column=1, pady=5)

button_select_folder = Button(app, text="Browse", command=select_folder)
button_select_folder.grid(row=3, column=2, padx=5)

Label(app, text="Username:").grid(row=4, column=0, pady=5, sticky='e')
entry_username = Entry(app)
entry_username.grid(row=4, column=1, pady=5)

Label(app, text="Password:").grid(row=5, column=0, pady=5, sticky='e')
entry_password = Entry(app, show='*')
entry_password.grid(row=5, column=1, pady=5,)

button_submit = Button(app, text="Generate PDFs", command=process_data)
button_submit.grid(row=6, column=0, columnspan=3, pady=20)

app.mainloop()