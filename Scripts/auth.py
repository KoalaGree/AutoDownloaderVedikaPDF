import requests
from tkinter import Tk, Label, Entry, Button, messagebox

def get_site_cookie(session):
    try:
        url = "https://mlite.rsubunda.com/admin/"
        response = session.get(url)
        return response.cookies.get_dict()  # Mengembalikan cookies sebagai dictionary
    except Exception as err:
        return str(err)

def auth(username, password):
    try:
        url = "https://mlite.rsubunda.com/admin/"
        payload = {
            'username': username,
            'password': password,
            'login': ''
        }
        
        # Menggunakan requests.Session untuk mengelola cookies
        with requests.Session() as session:
            # Mengambil cookies dari permintaan awal
            initial_cookies = get_site_cookie(session)
            if isinstance(initial_cookies, dict):
                # Mengirimkan permintaan login
                response = session.post(url, data=payload)
                print(response.text)  # Menampilkan respons untuk debugging

                # Mengambil cookies dari respons
                cookies = session.cookies.get_dict()
                return cookies
            else:
                return initial_cookies  # Mengembalikan error jika gagal mendapatkan cookies awal
    except Exception as e:
        return str(e)

def save_cookies_to_file(cookies):
    try:
        with open("cookie.txt", "w") as file:
            for key, value in cookies.items():
                file.write(f"{key}={value}\n")
        messagebox.showinfo("Success", "Cookies saved to cookie.txt")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def process():
    try:
        username = entry_username.get()
        password = entry_password.get()
        cookies = auth(username, password)
        
        if isinstance(cookies, dict):
            # Simpan cookies ke file
            save_cookies_to_file(cookies)
        else:
            # Tampilkan pesan error jika ada
            messagebox.showerror("Error", cookies)
    except Exception as e:
        messagebox.showerror("Error", str(e))

app = Tk()
app.title("Get Login Cookies")
app.geometry("400x400")

# Create and place labels and entry fields
Label(app, text="Username").pack(pady=5)
entry_username = Entry(app)
entry_username.pack(pady=5)

Label(app, text="Password").pack(pady=5)
entry_password = Entry(app, show='*')  # Menyembunyikan input password
entry_password.pack(pady=5)

# Create and place the submit button
button_submit = Button(app, text="Get Cookies", command=process)
button_submit.pack(pady=20)

# Start the Tkinter event loop
app.mainloop()