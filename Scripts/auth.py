import requests
import json
from tkinter import Tk, Label, Entry, Button, messagebox

def get_site_cookie(session):
    # Fungsi ini harus mengembalikan cookie awal yang diperlukan untuk autentikasi
    try:
        response = session.get("http://192.168.1.50/admin/")
        return response.cookies.get_dict()  # Mengembalikan cookie sebagai dictionary
    except Exception as e:
        return str(e)

def auth(username, password):
    try:
        url = "http://192.168.1.50/admin/"
        payload = {
            'username': username,
            'password': password,
            'login': ''
        }
        
        with requests.Session() as session:
            initial_cookies = get_site_cookie(session)
            if isinstance(initial_cookies, dict):
                response = session.post(url, data=payload)
                if response.ok:  # Memeriksa apakah permintaan berhasil
                    cookies = session.cookies.get_dict()
                    return cookies
                else:
                    return f"Authentication failed: {response.status_code} {response.reason}"
            else:
                return initial_cookies 
    except Exception as e:
        return str(e)

def save_cookies_to_file(cookies):
    try:
        cookie_list = []
        for key, value in cookies.items():
            cookie_dict = {
                "domain": "192.168.1.50",  # Ganti dengan domain yang sesuai
                "hostOnly": True,
                "httpOnly": False,
                "name": key,
                "path": "/",
                "sameSite": "unspecified",
                "secure": False,
                "session": True,
                "storeId": "0",
                "value": value
            }
            cookie_list.append(cookie_dict)

        # Menyimpan dalam format JSON
        with open("cookie.txt", "w") as file:
            json.dump(cookie_list, file, indent=4)
        
        messagebox.showinfo("Success", "Cookies saved to cookie.txt")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def process():
    try:
        username = entry_username.get()
        password = entry_password.get()
        cookies = auth(username, password)
        
        if isinstance(cookies, dict):
            save_cookies_to_file(cookies)
        else:
            messagebox.showerror("Error", cookies)
    except Exception as e:
        messagebox.showerror("Error", str(e))