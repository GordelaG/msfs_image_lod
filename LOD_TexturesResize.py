import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image
import threading

EXCLUDED_TAGS = ['_NRM', '_NML', '_NORMAL', '_LOD1', '_LOD2', '_LOD3', '_LOD4']
LOD_SIZES = {
    "_LOD1": (1024, 1024),
    "_LOD2": (256, 256),
    "_LOD3": (64, 64),
    "_LOD4": (16, 16)
}

DARK_COLORS = {
    "bg": "#1e1e1e",
    "panel_bg": "#252526",
    "fg": "#dcdcdc",
    "accent": "#00ff08",
    "border": "#3c3c3c",
    "input_bg": "#585861",
    "button_bg": "#3a3d41",
    "button_hover": "#9D9069"
}

def apply_dark_theme(root: tk.Tk):
    """Define um tema escuro simples para a janela."""
    colors = DARK_COLORS
    root.configure(bg=colors["bg"])

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=colors["bg"])
    style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
    style.configure(
        "TButton",
        background=colors["button_bg"],
        foreground=colors["fg"],
        bordercolor=colors["border"],
        focusthickness=3,
        focuscolor=colors["accent"]
    )
    style.map("TButton", background=[("active", colors["button_hover"])])
    style.configure(
        "TEntry",
        fieldbackground=colors["input_bg"],
        foreground=colors["fg"],
        insertcolor=colors["fg"],
        background=colors["input_bg"]
    )
    style.map("TEntry", fieldbackground=[("readonly", colors["input_bg"])])
    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=colors["bg"],
        troughcolor=colors["input_bg"],
        bordercolor=colors["border"],
        arrowcolor=colors["fg"]
    )


def is_excluded(filename: str) -> bool:
    return any(tag in filename for tag in EXCLUDED_TAGS)


def generate_lods(image_path: Path, status_callback):
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGBA")  # Garante compatibilidade

            for lod_suffix, size in LOD_SIZES.items():
                lod_filename = image_path.with_name(image_path.stem + lod_suffix + image_path.suffix)
                if not lod_filename.exists():
                    resized = img.resize(size, Image.LANCZOS)
                    resized.save(lod_filename)
                    status_callback(f"{lod_suffix[1:]} criado: {lod_filename.name}")
                else:
                    status_callback(f"{lod_suffix[1:]} ignorado (ja existe): {lod_filename.name}")
    except Exception as e:
        status_callback(f"Erro ao processar {image_path.name}: {e}")


def process_folder(folder_path: Path, status_callback, done_callback):
    png_files = list(folder_path.glob("*.png"))
    if not png_files:
        status_callback("Nenhum arquivo PNG encontrado.")
        done_callback()
        return

    status_callback(f"Processando {len(png_files)} arquivos PNG...")

    for idx, file in enumerate(png_files, 1):
        if is_excluded(file.stem):
            status_callback(f"[{idx}] Ignorado (excluido): {file.name}")
            continue
        status_callback(f"[{idx}] Processando: {file.name}")
        generate_lods(file, status_callback)

    status_callback("\n#### Finalizado! Que a Forca esteja com voce :)")
    done_callback()


class TextureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LOD Textures Generator")
        self.folder_path = tk.StringVar()
        apply_dark_theme(self.root)

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Selecione a pasta de texturas:").grid(row=0, column=0, sticky='w')
        ttk.Entry(frame, textvariable=self.folder_path, width=50).grid(row=1, column=0, sticky='we')
        ttk.Button(frame, text="Procurar", command=self.browse_folder).grid(row=1, column=1, padx=5)

        self.process_btn = ttk.Button(frame, text="Gerar LODs", command=self.start_processing)
        self.process_btn.grid(row=2, column=0, pady=10, sticky='w')

        ttk.Button(frame, text="Limpar status", command=self.clear_status).grid(row=2, column=1, pady=10, sticky='e')

        self.status = tk.Text(
            frame,
            height=15,
            state='disabled',
            wrap='word',
            bg=DARK_COLORS["panel_bg"],
            fg=DARK_COLORS["fg"],
            insertbackground=DARK_COLORS["fg"],
            highlightthickness=0,
            relief=tk.FLAT
        )
        self.status.grid(row=3, column=0, columnspan=2, sticky='nsew')

        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(0, weight=1)

    def browse_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder_path.set(selected)

    def clear_status(self):
        self.status.config(state='normal')
        self.status.delete("1.0", tk.END)
        self.status.config(state='disabled')

    def start_processing(self):
        folder = Path(self.folder_path.get())
        if not folder.exists():
            messagebox.showerror("Erro", "A pasta selecionada nao existe.")
            return

        self.process_btn.config(state='disabled')
        self.status_output("\n=== Iniciando processamento ===\n")

        # Iniciar thread de forma segura
        thread = threading.Thread(
            target=process_folder,
            args=(folder, self.status_output, self.reenable_button),
            daemon=True
        )
        thread.start()

    def reenable_button(self):
        self.process_btn.config(state='normal')

    def status_output(self, message):
        self.status.config(state='normal')
        self.status.insert(tk.END, message + "\n")
        self.status.see(tk.END)
        self.status.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    app = TextureApp(root)
    root.geometry("700x450")
    root.mainloop()
