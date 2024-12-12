import requests
import os
import threading
import re
from bs4 import BeautifulSoup
import pdfkit
from tkinter import Tk, Label, Entry, Button, messagebox
from tkinter import filedialog
import mysql.connector

# Database connection parameters
DB_HOST = 'your_db_host'
DB_USER = 'your_db_user'
DB_PASSWORD = 'your_db_password'
DB_NAME = 'your_db_name'

# PDF configuration
path_wkthmltopdf = 'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)

def fetch_identifiers(tanggal1):
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
            mlite_vedika.no_rawat 
        FROM
            mlite_vedika
            JOIN kamar_inap ON mlite_vedika.no_rawat = kamar_inap.no_rawat 
        WHERE
            mlite_vedika.jenis = '1' 
            AND mlite_vedika.`status` = 'Pengajuan' 
            AND kamar_inap.tgl_keluar LIKE '{tanggal1}' 
            AND kamar_inap.stts_pulang NOT LIKE '%Pindah%'
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def generate_pdf(no_rawat, cookies, path_folder):
    try:
        modified_string = no_rawat.replace("/", "")
        url = f"http://url.com/admin/vedika/pdf/{modified_string}"

        payload = 'username=&password=&login='
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookies,
            'DNT': '1',
            'Origin': 'http://url.com',
            'Referer': 'http://url.com/',
            'Upgrade-Insecure-Requests': '1',
            'User -Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
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
    cookies = entry_cookies.get()
    folder_name = entry_folder.get()

    path_folder = os.path.join(os.getcwd(), folder_name)

    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    results = fetch_identifiers(tanggal1)

    if not results:
        messagebox.showinfo("Info", "No records found for the given date range.")
        return

    def worker():
        for result in results:
            no_rawat = result[0]
            message = generate_pdf(no_rawat, cookies, path_folder)
            print(message)  # You can also show this in the GUI if needed

        messagebox.showinfo("Info", "All PDFs have been processed.")

    # Start the processing in a separate thread
    threading.Thread(target=worker).start()

def select_folder():
    folder_selected = filedialog.askdirectory()  # Open a dialog to select a folder
    if folder_selected:  # If a folder is selected
        entry_folder.delete(0, 'end')  # Clear the current entry
        entry_folder.insert(0, folder_selected)  # Insert the selected folder path

def open_file_dialog():
    file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'r') as file:
            content = file.read()
            entry_cookies.insert(0, content)

# Create the main application window
app = Tk()
app.title("PDF Generator")
app.geometry("400x400")

# Create and place labels and entry fields
Label(app, text="Input Tanggal :").pack(pady=5)
entry_tanggal1 = Entry(app)
entry_tanggal1.pack(pady=5)

Label(app, text="Masukkan Cookies:").pack(pady=5)
entry_cookies = Entry(app)
entry_cookies.pack(pady=5)
button_select_file = Button(app, text="Load Cookies", command=open_file_dialog)
button_select_file.pack(pady=5)

Label(app, text="Pilih Folder:").pack(pady=5)
entry_folder = Entry(app)
entry_folder.pack(pady=5)

# Create a button to select the folder
button_select_folder = Button(app, text="Browse", command=select_folder)
button_select_folder.pack(pady=5)

# Create and place the submit button
button_submit = Button(app, text="Generate PDFs", command=process_data)
button_submit.pack(pady=20)

# Start the Tkinter event loop
app.mainloop()