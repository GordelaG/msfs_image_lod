import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image
import threading

EXCLUDED_TAGS = ['_LOD1', '_LOD2', '_LOD3', '_LOD4', '_LOD5', '_LOD6', '_LOD7', '_LOD8', '_LOD9']
LOD_ORDER = ["_LOD1", "_LOD2", "_LOD3", "_LOD4", "_LOD5", "_LOD6", "_LOD7", "_LOD8", "_LOD9"]
ALLOWED_SIZES = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
DEFAULT_LOD_SIZES = ["4096", "2048", "1024", "512", "256", "128", "64", "32", "16"]

DARK_COLORS = {
    "bg": "#0f1117",
    "panel_bg": "#151a24",
    "fg": "#e7ecf3",
    "muted": "#9aa4b5",
    "accent": "#5de4c7",
    "accent_hover": "#7ff0d8",
    "border": "#1f2633",
    "input_bg": "#1d2431",
    "button_bg": "#1f2836",
    "button_hover": "#2c3545"
}

def apply_dark_theme(root: tk.Tk):
    """Define um tema escuro simples para a janela."""
    colors = DARK_COLORS
    root.configure(bg=colors["bg"])
    # Font specs need tuple form to keep family names with spaces intact
    root.option_add("*Font", ("Segoe UI", 10))
    root.option_add("*TCombobox*Listbox*Font", ("Segoe UI", 10))

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=colors["bg"])
    style.configure("Card.TFrame", background=colors["panel_bg"])
    style.configure("Header.TLabel", background=colors["panel_bg"], foreground=colors["fg"], font=("Segoe UI Semibold", 14))
    style.configure("Subheader.TLabel", background=colors["panel_bg"], foreground=colors["muted"], font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=colors["panel_bg"], foreground=colors["fg"])
    style.configure("CardMuted.TLabel", background=colors["panel_bg"], foreground=colors["muted"])
    style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
    style.configure(
        "TButton",
        background=colors["button_bg"],
        foreground=colors["fg"],
        bordercolor=colors["border"],
        focusthickness=3,
        focuscolor=colors["accent"]
    )
    style.configure(
        "Accent.TButton",
        background=colors["accent"],
        foreground=colors["bg"],
        bordercolor=colors["accent"],
        focusthickness=3,
        focuscolor=colors["accent"]
    )
    style.map("TButton", background=[("active", colors["button_hover"])])
    style.map("Accent.TButton", background=[("active", colors["accent_hover"])])
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
    style.configure(
        "TCombobox",
        fieldbackground=colors["input_bg"],
        background=colors["input_bg"],
        foreground=colors["fg"],
        arrowcolor=colors["fg"]
    )
    style.map("TCombobox", fieldbackground=[("readonly", colors["input_bg"])])
    style.configure(
        "Card.TCheckbutton",
        background=colors["panel_bg"],
        foreground=colors["fg"],
        focusthickness=2,
        focuscolor=colors["accent"]
    )
    style.map(
        "Card.TCheckbutton",
        background=[("active", colors["button_hover"])],
        indicatorcolor=[("selected", colors["accent"])],
        indicatorbackground=[("selected", colors["accent"])]
    )


def is_excluded(filename: str, include_normals: bool) -> bool:
    name_lower = filename.lower()
    if not include_normals and "norm" in name_lower:
        return True
    return any(tag.lower() in name_lower for tag in EXCLUDED_TAGS)
def generate_lods(image_path: Path, sizes, status_callback):
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGBA")  # Garante compatibilidade

            for lod_suffix, size in zip(LOD_ORDER, sizes):
                lod_filename = image_path.with_name(image_path.stem + lod_suffix + image_path.suffix)
                if not lod_filename.exists():
                    resized = img.resize(size, Image.LANCZOS)
                    resized.save(lod_filename)
                    status_callback(f"{lod_suffix[1:]} criado: {lod_filename.name} ({size[0]}x{size[1]})")
                else:
                    status_callback(f"{lod_suffix[1:]} ignorado (ja existe): {lod_filename.name}")
    except Exception as e:
        status_callback(f"Erro ao processar {image_path.name}: {e}")


def delete_lods_in_folder(folder_path: Path, status_callback, done_callback):
    png_files = list(folder_path.glob("*.png"))
    if not png_files:
        status_callback("Nenhum arquivo PNG encontrado.")
        done_callback()
        return

    removed = 0
    status_callback(f"Procurando LODs gerados em {folder_path}...")
    for file in png_files:
        if any(tag.lower() in file.stem.lower() for tag in EXCLUDED_TAGS):
            try:
                file.unlink()
                removed += 1
                status_callback(f"Removido: {file.name}")
            except Exception as exc:
                status_callback(f"Falha ao remover {file.name}: {exc}")

    if removed == 0:
        status_callback("Nenhum LOD encontrado para remover.")
    else:
        status_callback(f"Total removido: {removed}")
    done_callback()


def process_folder(folder_path: Path, lod_sizes, include_normals: bool, status_callback, done_callback):
    png_files = list(folder_path.glob("*.png"))
    if not png_files:
        status_callback("Nenhum arquivo PNG encontrado.")
        done_callback()
        return

    size_desc = ", ".join(f"{s[0]}x{s[1]}" for s in lod_sizes)
    status_callback(f"Processando {len(png_files)} arquivos PNG ({len(lod_sizes)} LODs: {size_desc})...")
    status_callback("Incluindo arquivos NORM." if include_normals else "Ignorando arquivos NORM.")

    for idx, file in enumerate(png_files, 1):
        if is_excluded(file.stem, include_normals):
            status_callback(f"[{idx}] Ignorado (excluido): {file.name}")
            continue
        status_callback(f"[{idx}] Processando: {file.name}")
        generate_lods(file, lod_sizes, status_callback)

    status_callback("\n#### Finalizado! Que a Forca esteja com voce :)")
    done_callback()


class TextureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LOD Textures Generator")
        self.folder_path = tk.StringVar()
        self.lod_count = tk.StringVar(value="4")
        self.lod_size_vars = [
            tk.StringVar(value=DEFAULT_LOD_SIZES[idx])
            for idx in range(len(LOD_ORDER))
        ]
        self.include_normals = tk.BooleanVar(value=True)
        self.process_btn = None
        self.delete_btn = None
        apply_dark_theme(self.root)

        self.create_widgets()

    def create_widgets(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        header = ttk.Frame(container, style="Card.TFrame", padding=(16, 14))
        header.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        ttk.Label(header, text="LOD Textures Generator", style="Header.TLabel").grid(row=0, column=0, sticky='w')
        ttk.Label(
            header,
            text="Gere, ajuste e limpe LODs de texturas com rapidez.",
            style="Subheader.TLabel"
        ).grid(row=1, column=0, sticky='w', pady=(4, 0))

        input_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        input_card.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        input_card.columnconfigure(0, weight=1)
        ttk.Label(input_card, text="Pasta de texturas", style="Card.TLabel").grid(row=0, column=0, sticky='w')
        ttk.Label(
            input_card,
            text="Selecione a pasta contendo os PNGs que deseja processar.",
            style="CardMuted.TLabel"
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=(2, 6))
        ttk.Entry(input_card, textvariable=self.folder_path, width=50).grid(row=2, column=0, sticky='we', pady=(0, 6))
        ttk.Button(input_card, text="Procurar", command=self.browse_folder).grid(row=2, column=1, padx=(8, 0), sticky='e')
        ttk.Checkbutton(
            input_card,
            text="Incluir arquivos NORM (normal map)",
            variable=self.include_normals,
            style="Card.TCheckbutton",
            padding=(4, 4)
        ).grid(row=3, column=0, columnspan=2, sticky='w')

        lod_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        lod_card.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        lod_card.columnconfigure(1, weight=1)
        ttk.Label(lod_card, text="Configuracao de LODs", style="Card.TLabel").grid(row=0, column=0, sticky='w')
        ttk.Label(
            lod_card,
            text="Defina a quantidade de LODs e o tamanho de cada textura.",
            style="CardMuted.TLabel"
        ).grid(row=1, column=0, columnspan=3, sticky='w', pady=(2, 8))

        ttk.Label(lod_card, text="Quantidade de LODs:", style="Card.TLabel").grid(row=2, column=0, sticky='w')
        ttk.Combobox(
            lod_card,
            textvariable=self.lod_count,
            values=[str(i) for i in range(1, len(LOD_ORDER) + 1)],
            width=15,
            state="readonly"
        ).grid(row=2, column=0, sticky='s', pady=(2, 2))

        ttk.Label(
            lod_card,
            text="Selecione o tamanho de redução de cada LOD em ordem decrescente.",
            style="Card.TLabel"
        ).grid(row=3, column=0, sticky='nw', pady=(10, 0))
        sizes_frame = ttk.Frame(lod_card)
        sizes_frame.grid(row=4, column=0, sticky='w', pady=(10, 0))
        for idx, lod_name in enumerate(LOD_ORDER):
            row = idx // 3
            col = (idx % 3) * 2
            ttk.Label(sizes_frame, text=f"{lod_name[1:]}:", style="Card.TLabel").grid(row=row, column=col, sticky='w', padx=(0, 4), pady=(0, 6))
            ttk.Combobox(
                sizes_frame,
                textvariable=self.lod_size_vars[idx],
                values=[str(v) for v in ALLOWED_SIZES],
                width=15,
                state="readonly"
            ).grid(row=row, column=col + 1, sticky='w', padx=(0, 12), pady=(0, 6))

        actions = ttk.Frame(container, padding=(0, 4))
        actions.grid(row=3, column=0, sticky='ew', pady=(0, 10))
        actions.columnconfigure(2, weight=1)

        self.process_btn = ttk.Button(actions, text="Gerar LODs", style="Accent.TButton", command=self.start_processing)
        self.process_btn.grid(row=0, column=0, padx=(0, 8))
        self.delete_btn = ttk.Button(actions, text="Deletar LODs", command=self.start_deleting)
        self.delete_btn.grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text="Limpar status", command=self.clear_status).grid(row=0, column=2, sticky='e')

        ttk.Label(container, text="Status", foreground=DARK_COLORS["muted"]).grid(row=4, column=0, sticky='w', pady=(0, 6))
        self.status = tk.Text(
            container,
            height=14,
            state='disabled',
            wrap='word',
            bg=DARK_COLORS["panel_bg"],
            fg=DARK_COLORS["fg"],
            insertbackground=DARK_COLORS["fg"],
            highlightthickness=1,
            highlightbackground=DARK_COLORS["border"],
            relief=tk.FLAT
        )
        self.status.grid(row=5, column=0, columnspan=2, sticky='nsew')

        container.rowconfigure(5, weight=1)


    def browse_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder_path.set(selected)

    def clear_status(self):
        self.status.config(state='normal')
        self.status.delete("1.0", tk.END)
        self.status.config(state='disabled')

    def collect_lod_sizes(self, lod_count: int):
        sizes = []
        allowed_set = set(ALLOWED_SIZES)
        for idx in range(lod_count):
            try:
                value = int(self.lod_size_vars[idx].get())
            except ValueError:
                raise ValueError(f"Valor invalido para {LOD_ORDER[idx][1:]}: escolha um dos valores permitidos.")
            if value not in allowed_set:
                raise ValueError(f"{LOD_ORDER[idx][1:]} deve ser um destes valores: {ALLOWED_SIZES}.")
            sizes.append((value, value))

        for idx in range(1, len(sizes)):
            if sizes[idx][0] > sizes[idx - 1][0] or sizes[idx][1] > sizes[idx - 1][1]:
                raise ValueError("Defina os LODs em ordem decrescente (ex.: 4096 >= 2048 >= 1024 ...).")

        return sizes

    def start_processing(self):
        folder = Path(self.folder_path.get())
        if not folder.exists():
            messagebox.showerror("Erro", "A pasta selecionada nao existe.")
            return
        try:
            lod_count = int(self.lod_count.get())
        except ValueError:
            lod_count = 0

        if lod_count < 1 or lod_count > len(LOD_ORDER):
            messagebox.showerror("Erro", f"Informe um valor entre 1 e {len(LOD_ORDER)} LODs.")
            return

        try:
            lod_sizes = self.collect_lod_sizes(lod_count)
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc))
            return

        self.process_btn.config(state='disabled')
        self.delete_btn.config(state='disabled')
        self.status_output("\n=== Iniciando processamento ===\n")

        # Iniciar thread de forma segura
        thread = threading.Thread(
            target=process_folder,
            args=(folder, lod_sizes, self.include_normals.get(), self.status_output, self.reenable_actions),
            daemon=True
        )
        thread.start()

    def start_deleting(self):
        folder = Path(self.folder_path.get())
        if not folder.exists():
            messagebox.showerror("Erro", "A pasta selecionada nao existe.")
            return

        self.process_btn.config(state='disabled')
        self.delete_btn.config(state='disabled')
        self.status_output("\n=== Removendo LODs gerados ===\n")

        thread = threading.Thread(
            target=delete_lods_in_folder,
            args=(folder, self.status_output, self.reenable_actions),
            daemon=True
        )
        thread.start()

    def reenable_actions(self):
        self.process_btn.config(state='normal')
        self.delete_btn.config(state='normal')

    def status_output(self, message):
        self.status.config(state='normal')
        self.status.insert(tk.END, message + "\n")
        self.status.see(tk.END)
        self.status.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    app = TextureApp(root)
    root.geometry("1000x720")
    root.minsize(880, 640)
    root.mainloop()
