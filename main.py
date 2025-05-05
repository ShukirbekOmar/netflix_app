
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import os
DB_PATH = "netflix_app.db"



# DB_PATH = r"C:\Users\amirb\Downloads\NETFLIX\netflix_app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            year INTEGER,
            description TEXT,
            status TEXT,
            favorite INTEGER DEFAULT 0,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_movie(title, genre, year, description, status, image_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO movies (title, genre, year, description, status, image_path) VALUES (?, ?, ?, ?, ?, ?)",
              (title, genre, year, description, status, image_path))
    conn.commit()
    conn.close()
    refresh_all_lists()

def update_movie(movie_id, title, genre, year, description, status, image_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE movies SET title=?, genre=?, year=?, description=?, status=?, image_path=? WHERE id=?",
              (title, genre, year, description, status, image_path, movie_id))
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

def get_movies_by_status(status=None, favorite=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if favorite:
        c.execute("SELECT * FROM movies WHERE favorite=1")
    elif status:
        c.execute("SELECT * FROM movies WHERE status=?", (status,))
    else:
        c.execute("SELECT * FROM movies")
    result = c.fetchall()
    conn.close()
    return result

def refresh_all_lists():
    populate_movie_list(watched_frame, "Watched")
    populate_movie_list(to_watch_frame, "To Watch")
    populate_movie_list(favorites_frame, None, favorite=True)
def populate_movie_list(container, status=None, favorite=False):
    for widget in container.winfo_children():
        widget.destroy()

    movies = get_movies_by_status(status=status, favorite=favorite)

    for movie in movies:
        frame = tk.Frame(container, bg="gray20")
        frame.pack(fill=tk.X, padx=5, pady=5)

        info = f"{movie[1]} ({movie[2]}, {movie[3]})"
        label = tk.Label(frame, text=info, fg="white", bg="gray20", cursor="hand2")
        label.pack(side=tk.LEFT, padx=5)
        label.bind("<Button-1>", lambda e, m=movie: show_description(m))

        # Проверка пути изображения
        if movie[7]:
            print(f"Attempting to load image from: {movie[7]}")  # Отладочный вывод пути изображения
            try:
                if os.path.exists(movie[7]):
                    image = Image.open(movie[7])
                    image = image.resize((80, 100), Image.LANCZOS)
                    img = ImageTk.PhotoImage(image)
                    img_label = tk.Label(frame, image=img)
                    img_label.image = img
                    img_label.pack(side=tk.LEFT, padx=5)
                else:
                    print(f"Image file does not exist: {movie[7]}")  # Отладочный вывод ошибки
            except Exception as e:
                print(f"Error loading image: {e}")  # Вывод ошибки в консоль

        tk.Button(frame, text="✏️", command=lambda m=movie: open_edit_window(m)).pack(side=tk.RIGHT, padx=2)

        if status == "To Watch":
            tk.Button(frame, text="❌", command=lambda m=movie: update_movie(m[0], m[1], m[2], m[3], m[4], "Watched", m[7])).pack(side=tk.RIGHT, padx=2)
        else:
            tk.Button(frame, text="❌", command=lambda m_id=movie[0]: delete_movie(m_id)).pack(side=tk.RIGHT, padx=2)

        heart = "❤️" if movie[6] else "🤍"
        tk.Button(frame, text=heart, command=lambda m_id=movie[0], fav=1 - movie[6]: toggle_favorite(m_id, fav)).pack(side=tk.RIGHT, padx=2)

def show_description(movie):
    description_window = tk.Toplevel(root)
    description_window.title(f"Description: {movie[1]}")
    description_window.geometry("500x400")
    description_window.configure(bg="black")

    tk.Label(description_window, text=movie[1], font=("Helvetica", 14, "bold"), fg="white", bg="black").pack(pady=10)

    if movie[7]:
        try:
            print(f"Attempting to load image for description from: {movie[7]}")  # Отладочный вывод
            if os.path.exists(movie[7]):
                image = Image.open(movie[7])
                image = image.resize((200, 250), Image.LANCZOS)
                img = ImageTk.PhotoImage(image)
                img_label = tk.Label(description_window, image=img, bg="black")
                img_label.image = img
                img_label.pack(pady=5)
            else:
                tk.Label(description_window, text="⚠️ Image not found!", fg="red", bg="black").pack()
                print(f"Image file for description not found: {movie[7]}")  # Отладочный вывод
        except Exception as e:
            print(f"Error loading image for description: {e}")  # Логирование ошибки
            tk.Label(description_window, text=f"⚠️ Could not load image: {e}", fg="red", bg="black").pack()

    description_text = movie[4] if movie[4] else "No description available."
    desc_label = tk.Label(description_window, text=description_text, wraplength=460, justify="left", fg="white", bg="black")
    desc_label.pack(padx=10, pady=10)

    tk.Button(description_window, text="Close", command=description_window.destroy, bg="darkred", fg="white").pack(pady=10)

def open_add_window():
    open_movie_form()

def open_edit_window(movie):
    open_movie_form(movie)

def open_movie_form(movie=None):
    window = tk.Toplevel(root)
    window.title("Edit Movie" if movie else "Add Movie")

    tk.Label(window, text="Title").pack()
    title_entry = tk.Entry(window)
    title_entry.pack()

    tk.Label(window, text="Genre").pack()
    genre_entry = tk.Entry(window)
    genre_entry.pack()

    tk.Label(window, text="Year").pack()
    year_entry = tk.Entry(window)
    year_entry.pack()

    tk.Label(window, text="Description").pack()
    desc_entry = tk.Entry(window)
    desc_entry.pack()

    tk.Label(window, text="Image Path").pack()
    image_path_var = tk.StringVar()
    image_entry = tk.Entry(window, textvariable=image_path_var)
    image_entry.pack()

    # Label for image preview
    image_preview = tk.Label(window)
    image_preview.pack(pady=5)

    def show_image(path):
        try:
            img = Image.open(path)
            img = img.resize((120, 160), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_preview.image = photo
            image_preview.configure(image=photo)
        except Exception as e:
            image_preview.configure(text=f"Error loading image:\n{e}", image="", fg="red")

    def browse_image():
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if path:
            image_path_var.set(path)
            show_image(path)

    tk.Button(window, text="Browse...", command=browse_image).pack(pady=2)

    status_var = tk.StringVar(value="Watched")
    tk.Label(window, text="Status").pack()
    status_menu = ttk.Combobox(window, textvariable=status_var, values=["Watched", "To Watch"])
    status_menu.pack()

    if movie:
        title_entry.insert(0, movie[1])
        genre_entry.insert(0, movie[2])
        year_entry.insert(0, str(movie[3]))
        desc_entry.insert(0, movie[4] or "")
        image_path_var.set(movie[7] or "")
        status_var.set(movie[5])
        if movie[7]:
            show_image(movie[7])

    def save():
        title = title_entry.get()
        genre = genre_entry.get()
        year = year_entry.get()
        description = desc_entry.get()
        image_path = image_path_var.get()
        status = status_var.get()

        if not (title and genre and year.isdigit()):
            messagebox.showerror("Error", "Please fill out all fields correctly.")
            return

        if movie:
            update_movie(movie[0], title, genre, int(year), description, status, image_path)
        else:
            insert_movie(title, genre, int(year), description, status, image_path)
        window.destroy()

    tk.Button(window, text="Save", command=save).pack(pady=10)

def perform_search():
    query = search_entry.get()
    if not query:
        refresh_all_lists()
        return
    for widget in watched_frame.winfo_children():
        widget.destroy()
    results = search_movies(query)
    for movie in results:
        frame = tk.Frame(watched_frame, bg="gray20")
        frame.pack(fill=tk.X, padx=5, pady=5)
        info = f"{movie[1]} ({movie[2]}, {movie[3]})"
        label = tk.Label(frame, text=info, fg="white", bg="gray20", cursor="hand2")
        label.pack(side=tk.LEFT, padx=5)
        label.bind("<Button-1>", lambda e, m=movie: show_description(m))
        tk.Button(frame, text="✏️", command=lambda m=movie: open_edit_window(m)).pack(side=tk.RIGHT, padx=2)
        tk.Button(frame, text="❌", command=lambda m_id=movie[0]: delete_movie(m_id)).pack(side=tk.RIGHT, padx=2)
        heart = "❤️" if movie[6] else "🤍"
        tk.Button(frame, text=heart, command=lambda m_id=movie[0], fav=1 - movie[6]: toggle_favorite(m_id, fav)).pack(side=tk.RIGHT, padx=2)

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
tk.Button(top_frame, text="Search", command=perform_search, bg="darkred", fg="white").pack(side=tk.LEFT)

tk.Button(top_frame, text="Add Movie", command=open_add_window, bg="darkred", fg="white").pack(side=tk.RIGHT, padx=10)

tabs = ttk.Notebook(root)
tabs.pack(expand=1, fill="both")

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

refresh_all_lists()
root.mainloop()