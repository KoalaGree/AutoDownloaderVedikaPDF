import requests
from tkinter import Tk, Label, Entry, Button, messagebox

def get_site_cookie(session):
    try:
        url = "https://mlite.rsubunda.com/admin/"
        response = session.get(url)
        return response.cookies.get_dict()
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
        
        with requests.Session() as session:
            initial_cookies = get_site_cookie(session)
            if isinstance(initial_cookies, dict):
                response = session.post(url, data=payload)
                # print(response.text) 

                cookies = session.cookies.get_dict()
                return cookies
            else:
                return initial_cookies 
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
            save_cookies_to_file(cookies)
        else:
            messagebox.showerror("Error", cookies)
    except Exception as e:
        messagebox.showerror("Error", str(e))

app = Tk()
app.title("Get Login Cookies")
app.geometry("400x400")

Label(app, text="Username").pack(pady=5)
entry_username = Entry(app)
entry_username.pack(pady=5)

Label(app, text="Password").pack(pady=5)
entry_password = Entry(app, show='*')
entry_password.pack(pady=5)

button_submit = Button(app, text="Get Cookies", command=process)
button_submit.pack(pady=20)

app.mainloop()