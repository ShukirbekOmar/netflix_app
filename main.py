import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import os

DB_PATH = "netflix_app.db"
current_user_id = None

# --- DATABASE --- 

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre TEXT NOT NULL,
        year INTEGER,
        description TEXT,
        status TEXT,
        favorite INTEGER DEFAULT 0,
        image_path TEXT,
        user_id INTEGER,
        rating INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

def insert_movie(title, genre, year, description, status, image_path, rating):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user = None if status == "To Watch" else current_user_id
    c.execute("INSERT INTO movies (title, genre, year, description, status, image_path, user_id, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (title, genre, year, description, status, image_path, user, rating))
    conn.commit()
    conn.close()
    refresh_all_lists()

def update_movie(movie_id, title, genre, year, description, status, image_path, rating):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE movies SET title=?, genre=?, year=?, description=?, status=?, image_path=?, rating=? WHERE id=?",
              (title, genre, year, description, status, image_path, rating, movie_id))
    conn.commit()
    conn.close()
    refresh_all_lists()

def delete_movie(movie_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM movies WHERE id=?", (movie_id,))
    conn.commit()
    conn.close()
    refresh_all_lists()

def toggle_favorite(movie_id, fav):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE movies SET favorite=? WHERE id=?", (fav, movie_id))
    conn.commit()
    conn.close()
    refresh_all_lists()

def search_movies(query):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE title LIKE ?", (f"%{query}%",))
    result = c.fetchall()
    conn.close()
    return result

def get_movies_by_status(status=None, favorite=False, genre=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if favorite:
        if genre:
            c.execute("SELECT * FROM movies WHERE favorite=1 AND user_id=? AND genre=?", (current_user_id, genre))
        else:
            c.execute("SELECT * FROM movies WHERE favorite=1 AND user_id=?", (current_user_id,))
    elif status == "To Watch":
        if genre:
            c.execute("SELECT * FROM movies WHERE status=? AND genre=? AND user_id IS NULL", (status, genre))
        else:
            c.execute("SELECT * FROM movies WHERE status=? AND user_id IS NULL", (status,))
    else:
        if genre:
            c.execute("SELECT * FROM movies WHERE status=? AND user_id=? AND genre=?", (status, current_user_id, genre))
        else:
            c.execute("SELECT * FROM movies WHERE status=? AND user_id=?", (status, current_user_id))
    result = c.fetchall()
    conn.close()
    return result

def refresh_all_lists():
    selected_genre = genre_var.get() if genre_var.get() != "All" else None
    populate_movie_list(watched_frame, "Watched", genre=selected_genre)
    populate_movie_list(to_watch_frame, "To Watch", genre=selected_genre)
    populate_movie_list(favorites_frame, None, favorite=True, genre=selected_genre)

def populate_movie_list(container, status=None, favorite=False, genre=None):
    for widget in container.winfo_children():
        widget.destroy()

    movies = get_movies_by_status(status=status, favorite=favorite, genre=genre)

    for movie in movies:
        frame = tk.Frame(container, bg="gray20", bd=1, relief="solid", padx=5, pady=5)
        frame.pack(fill=tk.X, padx=5, pady=5)

        stars = "⭐" * movie[9] + "☆" * (5 - movie[9]) if movie[9] else "☆☆☆☆☆"
        info = f"{movie[1]} ({movie[2]}, {movie[3]}) {stars}"
        label = tk.Label(frame, text=info, fg="white", bg="gray20", cursor="hand2", font=("Arial", 12))
        label.pack(side=tk.LEFT, padx=5)
        label.bind("<Button-1>", lambda e, m=movie: show_description(m))

        if movie[7]:
            try:
                if os.path.exists(movie[7]):
                    image = Image.open(movie[7])
                    image = image.resize((80, 100), Image.LANCZOS)
                    img = ImageTk.PhotoImage(image)
                    img_label = tk.Label(frame, image=img)
                    img_label.image = img
                    img_label.pack(side=tk.LEFT, padx=5)
            except:
                pass

        tk.Button(frame, text="✏️", command=lambda m=movie: open_edit_window(m), bg="darkred", fg="white", relief="flat").pack(side=tk.RIGHT, padx=2)

        if status == "To Watch":
            tk.Button(frame, text="✅", command=lambda m=movie: update_movie(m[0], m[1], m[2], m[3], m[4], "Watched", m[7], m[9]), bg="green", fg="white", relief="flat").pack(side=tk.RIGHT, padx=2)
            tk.Button(frame, text="❌", command=lambda m=movie: move_to_watched_from_to_watch(m), bg="red", fg="white", relief="flat").pack(side=tk.RIGHT, padx=2)
        else:
            tk.Button(frame, text="❌", command=lambda m_id=movie[0]: delete_movie(m_id), bg="red", fg="white", relief="flat").pack(side=tk.RIGHT, padx=2)

        heart = "❤️" if movie[6] else "🤍"
        tk.Button(frame, text=heart, command=lambda m_id=movie[0], fav=1 - movie[6]: toggle_favorite(m_id, fav), bg="yellow", fg="black", relief="flat").pack(side=tk.RIGHT, padx=2)

def move_to_watched_from_to_watch(movie):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE movies SET status=?, user_id=? WHERE id=?", ("Watched", current_user_id, movie[0]))
    conn.commit()
    conn.close()
    refresh_all_lists()

def show_description(movie):
    description_window = tk.Toplevel(root)
    description_window.title(f"Description: {movie[1]}")
    description_window.geometry("500x400")
    description_window.configure(bg="black")

    tk.Label(description_window, text=movie[1], font=("Helvetica", 14, "bold"), fg="white", bg="black").pack(pady=10)

    if movie[7] and os.path.exists(movie[7]):
        try:
            image = Image.open(movie[7])
            image = image.resize((200, 250), Image.LANCZOS)
            img = ImageTk.PhotoImage(image)
            img_label = tk.Label(description_window, image=img, bg="black")
            img_label.image = img
            img_label.pack(pady=5)
        except:
            pass

    description_text = movie[4] if movie[4] else "No description available."
    tk.Label(description_window, text=description_text, wraplength=460, justify="left", fg="white", bg="black").pack(padx=10, pady=10)
    tk.Button(description_window, text="Close", command=description_window.destroy, bg="darkred", fg="white", relief="flat").pack(pady=10)

def open_add_window():
    open_movie_form()

def open_edit_window(movie):
    open_movie_form(movie)

def open_movie_form(movie=None):
    window = tk.Toplevel(root)
    window.title("Edit Movie" if movie else "Add Movie")

    tk.Label(window, text="Title", fg="white", bg="black").pack(pady=5)
    title_entry = tk.Entry(window)
    title_entry.pack()

    tk.Label(window, text="Genre", fg="white", bg="black").pack(pady=5)
    genre_entry = tk.Entry(window)
    genre_entry.pack()

    tk.Label(window, text="Year", fg="white", bg="black").pack(pady=5)
    year_entry = tk.Entry(window)
    year_entry.pack()

    tk.Label(window, text="Description", fg="white", bg="black").pack(pady=5)
    desc_entry = tk.Entry(window)
    desc_entry.pack()

    tk.Label(window, text="Image Path", fg="white", bg="black").pack(pady=5)
    image_path_var = tk.StringVar()
    image_entry = tk.Entry(window, textvariable=image_path_var)
    image_entry.pack(pady=5)
    image_preview = tk.Label(window)
    image_preview.pack(pady=5)

    def show_image(path):
        try:
            img = Image.open(path)
            img = img.resize((120, 160), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_preview.image = photo
            image_preview.configure(image=photo)
        except:
            image_preview.configure(text="Error loading image", fg="red")

    def browse_image():
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if path:
            image_path_var.set(path)
            show_image(path)

    tk.Button(window, text="Browse...", command=browse_image, bg="darkred", fg="white", relief="flat").pack(pady=5)

    status_var = tk.StringVar(value="Watched")
    tk.Label(window, text="Status", fg="white", bg="black").pack(pady=5)
    status_menu = ttk.Combobox(window, textvariable=status_var, values=["Watched", "To Watch"])
    status_menu.pack(pady=5)

    tk.Label(window, text="Rating (1-5 stars)", fg="white", bg="black").pack(pady=5)
    rating_var = tk.IntVar(value=1)
    rating_spin = tk.Spinbox(window, from_=1, to=5, textvariable=rating_var)
    rating_spin.pack(pady=5)

    if movie:
        title_entry.insert(0, movie[1])
        genre_entry.insert(0, movie[2])
        year_entry.insert(0, str(movie[3]))
        desc_entry.insert(0, movie[4] or "")
        image_path_var.set(movie[7] or "")
        status_var.set(movie[5])
        rating_var.set(movie[9] or 1)
        if movie[7]:
            show_image(movie[7])

    def save():
        title = title_entry.get()
        genre = genre_entry.get()
        year = year_entry.get()
        description = desc_entry.get()
        image_path = image_path_var.get()
        status = status_var.get()
        rating = rating_var.get()

        if not (title and genre and year.isdigit()):
            messagebox.showerror("Error", "Please fill out all fields correctly.")
            return

        if movie:
            update_movie(movie[0], title, genre, int(year), description, status, image_path, int(rating))
        else:
            insert_movie(title, genre, int(year), description, status, image_path, int(rating))
        window.destroy()

    tk.Button(window, text="Save", command=save, bg="green", fg="white", relief="flat").pack(pady=10)

def perform_search():
    query = search_entry.get()
    if not query:
        refresh_all_lists()
        return
    for widget in watched_frame.winfo_children():
        widget.destroy()
    results = search_movies(query)
    for movie in results:
        frame = tk.Frame(watched_frame, bg="gray20", bd=1, relief="solid", padx=5, pady=5)
        frame.pack(fill=tk.X, padx=5, pady=5)
        stars = "⭐" * movie[9] + "☆" * (5 - movie[9]) if movie[9] else "☆☆☆☆☆"
        info = f"{movie[1]} ({movie[2]}, {movie[3]}) {stars}"
        label = tk.Label(frame, text=info, fg="white", bg="gray20", cursor="hand2", font=("Arial", 12))
        label.pack(side=tk.LEFT, padx=5)
        label.bind("<Button-1>", lambda e, m=movie: show_description(m))
        tk.Button(frame, text="✏️", command=lambda m=movie: open_edit_window(m), bg="darkred", fg="white", relief="flat").pack(side=tk.RIGHT, padx=2)
        tk.Button(frame, text="❌", command=lambda m_id=movie[0]: delete_movie(m_id), bg="red", fg="white", relief="flat").pack(side=tk.RIGHT, padx=2)
        heart = "❤️" if movie[6] else "🤍"
        tk.Button(frame, text=heart, command=lambda m_id=movie[0], fav=1 - movie[6]: toggle_favorite(m_id, fav), bg="yellow", fg="black", relief="flat").pack(side=tk.RIGHT, padx=2)

# --- UI --- 

root = tk.Tk()
root.title("Netflix Manager")
root.geometry("700x600")
root.configure(bg="black")

init_db()

top_frame = tk.Frame(root, bg="black")
top_frame.pack(fill=tk.X)
search_entry = tk.Entry(top_frame)
search_entry.pack(side=tk.LEFT, padx=10, pady=10)
tk.Button(top_frame, text="Search", command=perform_search, bg="darkred", fg="white", relief="flat").pack(side=tk.LEFT)

tk.Button(top_frame, text="Add Movie", command=open_add_window, bg="darkred", fg="white", relief="flat").pack(side=tk.RIGHT, padx=10)
tk.Button(top_frame, text="Logout", command=lambda: logout(), bg="darkred", fg="white", relief="flat").pack(side=tk.RIGHT, padx=10)

genre_var = tk.StringVar(value="All")
genre_dropdown = ttk.Combobox(top_frame, textvariable=genre_var, values=["All", "Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance", "Thriller", "Adventure", "Fantasy", "Animation", "Mystery", "Crime",
    "Documentary", "Biography", "Historical", "Musical", "War", "Western", "Family" ])
genre_dropdown.pack(side=tk.LEFT, padx=10)
genre_dropdown.bind("<<ComboboxSelected>>", lambda e: refresh_all_lists())

tabs = ttk.Notebook(root)
tabs.pack(expand=1, fill="both", padx=10, pady=10)

watched_tab = tk.Frame(tabs, bg="black")
tabs.add(watched_tab, text="Watched")
watched_frame = tk.Frame(watched_tab, bg="black")
watched_frame.pack(fill=tk.BOTH, expand=True)

to_watch_tab = tk.Frame(tabs, bg="black")
tabs.add(to_watch_tab, text="To Watch")
to_watch_frame = tk.Frame(to_watch_tab, bg="black")
to_watch_frame.pack(fill=tk.BOTH, expand=True)

favorites_tab = tk.Frame(tabs, bg="black")
tabs.add(favorites_tab, text="Favorites")
favorites_frame = tk.Frame(favorites_tab, bg="black")
favorites_frame.pack(fill=tk.BOTH, expand=True)

def logout():
    global current_user_id
    current_user_id = None
    root.withdraw()
    show_login_window()

def show_login_window():
    login_window = tk.Tk()
    login_window.title("Netflix Login")
    login_window.geometry("500x350")
    login_window.configure(bg="black")

    current_lang = tk.StringVar(value="en")
    texts = {
        "en": {
            "username": "Username",
            "password": "Password",
            "login": "Login",
            "register": "Register",
            "language": "Language"
        },
        "kk": {
            "username": "Пайдаланушы аты",
            "password": "Құпиясөз",
            "login": "Кіру",
            "register": "Тіркелу",
            "language": "Тіл"
        }
    }

    def update_labels():
        lang = current_lang.get()
        username_label.config(text=texts[lang]["username"])
        password_label.config(text=texts[lang]["password"])
        login_btn.config(text=texts[lang]["login"])
        register_btn.config(text=texts[lang]["register"])
        lang_label.config(text=texts[lang]["language"])

    # Стильный фон (можно использовать изображение позже)
    form_frame = tk.Frame(login_window, bg="#141414")
    form_frame.place(relx=0.5, rely=0.5, anchor="center")

    username_label = tk.Label(form_frame, text="", fg="white", bg="#141414", font=("Arial", 12))
    username_label.grid(row=0, column=0, sticky="w", pady=(10, 2))
    username_entry = ttk.Entry(form_frame, width=30)
    username_entry.grid(row=1, column=0, pady=5)

    password_label = tk.Label(form_frame, text="", fg="white", bg="#141414", font=("Arial", 12))
    password_label.grid(row=2, column=0, sticky="w", pady=(10, 2))
    password_entry = ttk.Entry(form_frame, show="*", width=30)
    password_entry.grid(row=3, column=0, pady=5)

    login_btn = tk.Button(form_frame, text="", command=lambda: handle_login(), bg="darkred", fg="white", relief="flat", width=20)
    login_btn.grid(row=4, column=0, pady=10)

    register_btn = tk.Button(form_frame, text="", command=lambda: handle_register(), bg="gray30", fg="white", relief="flat", width=20)
    register_btn.grid(row=5, column=0, pady=5)

    # Переключение языка
    lang_label = tk.Label(form_frame, text="", fg="white", bg="#141414")
    lang_label.grid(row=6, column=0, pady=(15, 2))
    lang_menu = ttk.Combobox(form_frame, values=["English", "Қазақша"], state="readonly", width=28)
    lang_menu.grid(row=7, column=0, pady=5)
    lang_menu.current(0)

    def change_language(event):
        selected = lang_menu.get()
        current_lang.set("kk" if selected == "Қазақша" else "en")
        update_labels()

    lang_menu.bind("<<ComboboxSelected>>", change_language)

    update_labels()

    def handle_login():
        username = username_entry.get()
        password = password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both fields.")
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        result = c.fetchone()
        if result:
            global current_user_id
            current_user_id = result[0]
            login_window.destroy()
            root.deiconify()
            refresh_all_lists()
        else:
            messagebox.showerror("Error", "Invalid credentials.")
        conn.close()

    def handle_register():
        username = username_entry.get()
        password = password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both fields.")
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
        conn.close()

    root.withdraw()
    login_window.mainloop()

show_login_window()
