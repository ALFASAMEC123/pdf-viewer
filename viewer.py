import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz

APP_NAME = "PDF Viewer"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pdf_viewer_config.json")
DEFAULT_ZOOM = 1.0

class PDFViewer:
    def __init__(self, root, pdf_path):
        self.root = root
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.current_page = 0
        self.zoom = DEFAULT_ZOOM
        self.dark_mode = True
        self.fullscreen = False
        self.search_results = []
        self.search_index = -1

        self.load_config()
        self.setup_ui()
        self.bind_keys()
        self.render_page()
        self.update_page_list()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                self.dark_mode = cfg.get('dark_mode', True)
                self.zoom = cfg.get('zoom', DEFAULT_ZOOM)
        except:
            pass

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'dark_mode': self.dark_mode, 'zoom': self.zoom}, f)
        except:
            pass

    def setup_ui(self):
        self.root.title(f"{APP_NAME} - {os.path.basename(self.pdf_path)}")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        self.apply_theme()

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.sidebar = ttk.Frame(main_frame, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.sidebar.pack_propagate(False)

        ttk.Label(self.sidebar, text="Pages", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))

        self.page_list_frame = ttk.Frame(self.sidebar)
        self.page_list_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas_scroll = tk.Scrollbar(self.page_list_frame, orient=tk.VERTICAL)
        self.page_canvas = tk.Canvas(self.page_list_frame, yscrollcommand=self.canvas_scroll.set, highlightthickness=0)
        self.canvas_scroll.config(command=self.page_canvas.yview)
        self.canvas_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.page_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.page_inner = ttk.Frame(self.page_canvas)
        self.page_canvas.create_window((0, 0), window=self.page_inner, anchor=tk.NW)
        self.page_inner.bind('<Configure>', lambda e: self.page_canvas.configure(scrollregion=self.page_canvas.bbox('all')))

        self.page_canvas.bind('<MouseWheel>', lambda e: self.page_canvas.yview_scroll(-1*(e.delta//120), 'units'))
        self.page_canvas.bind('<Button-4>', lambda e: self.page_canvas.yview_scroll(-1, 'units'))
        self.page_canvas.bind('<Button-5>', lambda e: self.page_canvas.yview_scroll(1, 'units'))

        self.page_buttons = []

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        toolbar = ttk.Frame(content_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        self.prev_btn = ttk.Button(toolbar, text="◀ Prev", command=self.prev_page, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.next_btn = ttk.Button(toolbar, text="Next ▶", command=self.next_page, width=10)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.page_label = ttk.Label(toolbar, text="Page 1 / 1", font=('', 9))
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.page_entry = ttk.Entry(toolbar, width=6)
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_entry.bind('<Return>', self.goto_page_entry)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.zoom_out_btn = ttk.Button(toolbar, text="−", command=self.zoom_out, width=3)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=1)

        self.zoom_label = ttk.Label(toolbar, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT)

        self.zoom_in_btn = ttk.Button(toolbar, text="+", command=self.zoom_in, width=3)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=1)

        self.fit_width_btn = ttk.Button(toolbar, text="Fit Width", command=self.fit_width, width=10)
        self.fit_width_btn.pack(side=tk.LEFT, padx=5)

        self.fit_page_btn = ttk.Button(toolbar, text="Fit Page", command=self.fit_page, width=10)
        self.fit_page_btn.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.dark_btn = ttk.Button(toolbar, text="☀ Light" if self.dark_mode else "🌙 Dark", command=self.toggle_dark, width=10)
        self.dark_btn.pack(side=tk.LEFT, padx=2)

        self.fullscreen_btn = ttk.Button(toolbar, text="⛶ Fullscreen", command=self.toggle_fullscreen, width=12)
        self.fullscreen_btn.pack(side=tk.LEFT, padx=2)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.RIGHT, padx=5)
        self.search_entry.bind('<Return>', self.search)
        self.search_entry.bind('<Escape>', lambda e: self.clear_search())

        ttk.Label(toolbar, text="Search:").pack(side=tk.RIGHT)

        self.search_prev_btn = ttk.Button(toolbar, text="▲", command=self.search_prev, width=3)
        self.search_prev_btn.pack(side=tk.RIGHT, padx=1)
        self.search_next_btn = ttk.Button(toolbar, text="▼", command=self.search_next, width=3)
        self.search_next_btn.pack(side=tk.RIGHT, padx=1)

        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(canvas_frame,
                                 yscrollcommand=self.v_scroll.set,
                                 xscrollcommand=self.h_scroll.set,
                                 highlightthickness=0,
                                 bg='#1e1e1e' if self.dark_mode else '#ffffff')
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-1, 'units'))
        self.canvas.bind('<Button-5>', lambda e: self.canvas.yview_scroll(1, 'units'))
        self.canvas.bind('<Shift-MouseWheel>', self.on_h_mousewheel)
        self.canvas.bind('<Shift-Button-4>', lambda e: self.canvas.xview_scroll(-1, 'units'))
        self.canvas.bind('<Shift-Button-5>', lambda e: self.canvas.xview_scroll(1, 'units'))
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

        self.drag_data = {'x': 0, 'y': 0, 'dragging': False}

        self.status_var = tk.StringVar(value=f"Ready - {len(self.doc)} pages")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def apply_theme(self):
        bg = '#1e1e1e' if self.dark_mode else '#f0f0f0'
        fg = '#ffffff' if self.dark_mode else '#000000'
        canvas_bg = '#1e1e1e' if self.dark_mode else '#ffffff'
        select_bg = '#3d3d3d' if self.dark_mode else '#cce8ff'

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=bg, foreground=fg)
        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg, foreground=fg)
        style.configure('TButton', background='#3d3d3d' if self.dark_mode else '#e0e0e0', foreground=fg)
        style.map('TButton', background=[('active', '#505050' if self.dark_mode else '#d0d0d0')])
        style.configure('TEntry', fieldbackground='#2d2d2d' if self.dark_mode else '#ffffff', foreground=fg)
        style.configure('TSeparator', background='#505050' if self.dark_mode else '#cccccc')

        self.root.configure(bg=bg)
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=canvas_bg)

        for btn in self.page_buttons:
            btn.configure(style='Selected.TButton' if btn.page_num == self.current_page else 'TButton')

        style.configure('Selected.TButton', background='#0078d4' if self.dark_mode else '#0078d4', foreground='white')

    def bind_keys(self):
        self.root.bind('<Left>', lambda e: self.prev_page())
        self.root.bind('<Right>', lambda e: self.next_page())
        self.root.bind('<Up>', lambda e: self.canvas.yview_scroll(-3, 'units'))
        self.root.bind('<Down>', lambda e: self.canvas.yview_scroll(3, 'units'))
        self.root.bind('<Prior>', lambda e: self.prev_page())
        self.root.bind('<Next>', lambda e: self.next_page())
        self.root.bind('<Home>', lambda e: self.goto_page(0))
        self.root.bind('<End>', lambda e: self.goto_page(len(self.doc) - 1))
        self.root.bind('<Control-d>', lambda e: self.toggle_dark())
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen() if self.fullscreen else self.clear_search())
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in())
        self.root.bind('<Control-0>', lambda e: self.reset_zoom())
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<MouseWheel>', self.on_mousewheel)

    def get_pdf_resource_path(self):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, 'meinkampf.pdf')
        return self.pdf_path

    def render_page(self):
        if not (0 <= self.current_page < len(self.doc)):
            return

        page = self.doc[self.current_page]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_data = pix.tobytes("ppm")
        self.photo = tk.PhotoImage(data=img_data)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        self.highlight_search()

        self.page_label.config(text=f"Page {self.current_page + 1} / {len(self.doc)}")
        self.zoom_label.config(text=f"{int(self.zoom * 100)}%")
        self.status_var.set(f"Page {self.current_page + 1} of {len(self.doc)} | Zoom: {int(self.zoom * 100)}%")

        self.update_page_buttons()
        self.root.title(f"{APP_NAME} - {os.path.basename(self.pdf_path)} (Page {self.current_page + 1})")

    def highlight_search(self):
        if not self.search_results:
            return
        page = self.doc[self.current_page]
        for rect in page.search_for(self.search_var.get()):
            x0, y0, x1, y1 = rect * self.zoom
            self.canvas.create_rectangle(x0, y0, x1, y1, outline='#ffff00', width=2, fill='#ffff0040', tags='search_highlight')
        if self.search_index >= 0 and self.search_index < len(self.search_results):
            r = self.search_results[self.search_index]
            x0, y0, x1, y1 = r * self.zoom
            self.canvas.create_rectangle(x0, y0, x1, y1, outline='#ff0000', width=3, tags='search_current')

    def update_page_list(self):
        for widget in self.page_inner.winfo_children():
            widget.destroy()
        self.page_buttons = []

        for i in range(len(self.doc)):
            page = self.doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.15, 0.15), alpha=False)
            img_data = pix.tobytes("ppm")
            photo = tk.PhotoImage(data=img_data)

            btn = ttk.Button(self.page_inner, image=photo, command=lambda p=i: self.goto_page(p))
            btn.image = photo
            btn.page_num = i
            btn.pack(fill=tk.X, pady=1)
            ttk.Label(self.page_inner, text=f"Page {i+1}", font=('', 8)).pack(anchor=tk.W)
            self.page_buttons.append(btn)

        self.page_inner.update_idletasks()
        self.page_canvas.configure(scrollregion=self.page_canvas.bbox('all'))

    def update_page_buttons(self):
        for btn in self.page_buttons:
            if btn.page_num == self.current_page:
                btn.configure(style='Selected.TButton')
            else:
                btn.configure(style='TButton')
        self.page_canvas.yview_moveto(self.current_page / max(1, len(self.doc) - 1))

    def goto_page(self, page_num):
        if 0 <= page_num < len(self.doc):
            self.current_page = page_num
            self.render_page()

    def goto_page_entry(self, event):
        try:
            p = int(self.page_entry.get()) - 1
            self.goto_page(p)
        except:
            pass
        self.page_entry.delete(0, tk.END)

    def prev_page(self):
        self.goto_page(max(0, self.current_page - 1))

    def next_page(self):
        self.goto_page(min(len(self.doc) - 1, self.current_page + 1))

    def zoom_in(self):
        self.zoom = min(5.0, self.zoom * 1.2)
        self.render_page()

    def zoom_out(self):
        self.zoom = max(0.1, self.zoom / 1.2)
        self.render_page()

    def reset_zoom(self):
        self.zoom = DEFAULT_ZOOM
        self.render_page()

    def fit_width(self):
        page = self.doc[self.current_page]
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:
            page_width = page.rect.width
            self.zoom = (canvas_width - 20) / page_width
            self.render_page()

    def fit_page(self):
        page = self.doc[self.current_page]
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width > 1 and canvas_height > 1:
            page_width = page.rect.width
            page_height = page.rect.height
            zoom_w = (canvas_width - 20) / page_width
            zoom_h = (canvas_height - 20) / page_height
            self.zoom = min(zoom_w, zoom_h)
            self.render_page()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.dark_btn.config(text="☀ Light" if self.dark_mode else "🌙 Dark")
        self.apply_theme()
        self.render_page()
        self.save_config()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        self.fullscreen_btn.config(text="⛶ Windowed" if self.fullscreen else "⛶ Fullscreen")

    def exit_fullscreen(self):
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)
            self.fullscreen_btn.config(text="⛶ Fullscreen")

    def on_mousewheel(self, event):
        if event.state & 0x1:
            self.canvas.xview_scroll(-1 * (event.delta // 120), 'units')
        else:
            self.canvas.yview_scroll(-1 * (event.delta // 120), 'units')

    def on_h_mousewheel(self, event):
        self.canvas.xview_scroll(-1 * (event.delta // 120), 'units')

    def on_canvas_click(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.drag_data['dragging'] = True
        self.canvas.config(cursor='fleur')

    def on_canvas_drag(self, event):
        if self.drag_data['dragging']:
            dx = self.drag_data['x'] - event.x
            dy = self.drag_data['y'] - event.y
            self.canvas.xview_scroll(dx, 'units')
            self.canvas.yview_scroll(dy, 'units')

    def on_canvas_release(self, event):
        self.drag_data['dragging'] = False
        self.canvas.config(cursor='')

    def search(self, event=None):
        query = self.search_var.get().strip()
        if not query:
            self.clear_search()
            return

        self.search_results = []
        for i in range(len(self.doc)):
            page = self.doc[i]
            rects = page.search_for(query)
            self.search_results.extend([(i, r) for r in rects])

        if self.search_results:
            self.search_index = 0
            page_num, _ = self.search_results[0]
            self.goto_page(page_num)
            self.status_var.set(f"Found {len(self.search_results)} matches")
        else:
            self.status_var.set("No matches found")
            self.search_index = -1

    def search_next(self):
        if self.search_results:
            self.search_index = (self.search_index + 1) % len(self.search_results)
            page_num, _ = self.search_results[self.search_index]
            self.goto_page(page_num)

    def search_prev(self):
        if self.search_results:
            self.search_index = (self.search_index - 1) % len(self.search_results)
            page_num, _ = self.search_results[self.search_index]
            self.goto_page(page_num)

    def clear_search(self):
        self.search_var.set('')
        self.search_results = []
        self.search_index = -1
        self.canvas.delete('search_highlight', 'search_current')
        self.status_var.set(f"Page {self.current_page + 1} of {len(self.doc)} | Zoom: {int(self.zoom * 100)}%")

def get_embedded_pdf_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'meinkampf.pdf')
    return '/home/strane/Downloads/meinkampf.pdf'

def main():
    pdf_path = get_embedded_pdf_path()

    if not os.path.exists(pdf_path):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"PDF not found at:\n{pdf_path}")
        return

    root = tk.Tk()
    app = PDFViewer(root, pdf_path)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_config(), root.destroy()))
    root.mainloop()

if __name__ == '__main__':
    main()