import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel, ttk, messagebox, filedialog
import os
import configparser
import threading
from datetime import datetime
from pathlib import Path
import pandas as pd 
import Fileorganizer_python as organizer
from Fileorganizer_python import Client

class LawyerFileOrganizerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lawyer File Organizer")
        self.geometry("1920x1080")
        self.resizable(True, True)
        self.configure(bg="#f3f4f6")

        self.config_dir = Path.home() / ".LawyerFileOrganizer"
        self.config_file = self.config_dir / "config.ini"
        self.config_dir.mkdir(exist_ok=True)
        self.config_parser = configparser.ConfigParser()

        self.client_list = []
        
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        
        self.apply_styles()
        
        self.create_title_bar()
        
        self.create_widgets()

        self.load_clients_from_config()
        
        self.after(100, self.center_window)

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def apply_styles(self):
        self.style = ttk.Style(self)
        
        for theme in ["vista", "xpnative", "winnative", "clam", "alt", "default"]:
            try:
                self.style.theme_use(theme)
                break
            except tk.TclError:
                continue

        self.style.configure("TFrame", background="#f3f4f6")
        self.style.configure("TLabel", background="#f3f4f6", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9), padding=(8, 4))
        self.style.configure("TEntry", padding=4)
        self.style.configure("TCheckbutton", background="#f3f4f6", font=("Segoe UI", 9))
        self.style.configure("TNotebook", background="#f3f4f6")
        self.style.configure("TNotebook.Tab", padding=(12, 6))
        
        self.style.configure("Primary.TButton", 
                        background="#0078d4", 
                        foreground="white",
                        font=("Segoe UI", 9, "bold"))

        self.style.configure("Outline.TButton",
                        background="white",
                        foreground="#0078d4",
                        borderwidth=1,
                        relief="solid")
        
        self.style.configure("Title.TFrame", background="#f3f4f6")
        self.style.configure("Title.TLabel", 
                           background="#f3f4f6", 
                           font=("Segoe UI", 10, "bold"), 
                           foreground="#1f2937")
        self.style.configure("TButton", font=("Segoe UI", 9))

    def create_title_bar(self):
        title_bar = ttk.Frame(self, style="Title.TFrame", height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        
        title_label = ttk.Label(title_bar, text="Lawyer File Organizer", style="Title.TLabel")
        title_label.pack(side="left", padx=10)
        
        controls_frame = ttk.Frame(title_bar, style="Title.TFrame")
        controls_frame.pack(side="right", padx=5)
        
        ttk.Frame(title_bar, style="Title.TFrame", width=100).pack(side="right")

    def create_widgets(self):
        self.content_frame = ttk.Frame(self, style="TFrame")
        self.content_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill="both", expand=True)

        self.organize_files_tab = ttk.Frame(self.notebook, style="TFrame")
        self.settings_tab = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.organize_files_tab, text="Organize Files")
        self.notebook.add(self.settings_tab, text="Settings")

        self.create_organize_files_tab()
        self.create_settings_tab()

        self.create_status_bar()

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self, style="TFrame", relief="sunken", borderwidth=1)
        self.status_bar.pack(side="bottom", fill="x")
        self.status_label = ttk.Label(self.status_bar, text="Ready", style="TLabel")
        self.status_label.pack(side="left", padx=10)
        
        ttk.Separator(self.status_bar, orient="vertical").pack(side="left", fill="y", padx=5)
        
        self.client_count_label = ttk.Label(self.status_bar, text="0 clients configured", style="TLabel")
        self.client_count_label.pack(side="left", padx=5)

    def create_organize_files_tab(self):
        config_frame = ttk.LabelFrame(self.organize_files_tab, text="Configuration", padding=12)
        config_frame.pack(fill="x", padx=10, pady=8)

        source_frame = ttk.Frame(config_frame, style="TFrame")
        source_frame.pack(fill="x", pady=6)
        ttk.Label(source_frame, text="Source Directory:", style="TLabel").pack(side="left", padx=(0, 8))
        
        self.source_dir_entry = ttk.Entry(source_frame, width=50)
        self.source_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ttk.Button(source_frame, text="Browse", command=self.browse_source_dir).pack(side="left")

        dest_frame = ttk.Frame(config_frame, style="TFrame")
        dest_frame.pack(fill="x", pady=6)
        ttk.Label(dest_frame, text="Destination Directory:", style="TLabel").pack(side="left", padx=(0, 8))
        
        self.dest_dir_entry = ttk.Entry(dest_frame, width=50)
        self.dest_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ttk.Button(dest_frame, text="Browse", command=self.browse_dest_dir).pack(side="left")

        client_manager_frame = ttk.LabelFrame(self.organize_files_tab, text="Client Names", padding=12)
        client_manager_frame.pack(fill="x", padx=10, pady=8)

        client_input_frame = ttk.Frame(client_manager_frame, style="TFrame")
        client_input_frame.pack(fill="x", pady=(0, 8))

        self.client_name_entry = ttk.Entry(client_input_frame, width=40)
        self.client_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.setup_placeholder(self.client_name_entry, "Enter client name (First Last or First Middle Last)")

        ttk.Button(client_input_frame, text="Add Client", command=self.add_client).pack(side="left", padx=(0, 8))

        ttk.Button(client_input_frame, text="Batch Import", command=self.batch_import_clients).pack(side="left")

        list_container = ttk.Frame(client_manager_frame, style="TFrame")
        list_container.pack(fill="x", pady=8)

        self.client_canvas = tk.Canvas(list_container, height=180, bg="#f9fafb", highlightthickness=0, borderwidth=1, relief="solid", highlightbackground="#d1d5db")
        self.client_canvas.pack(side="left", fill="x", expand=True)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.client_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.client_canvas.configure(yscrollcommand=scrollbar.set)

        self.clients_frame = ttk.Frame(self.client_canvas, style="TFrame")
        self.client_canvas.create_window((0, 0), window=self.clients_frame, anchor="nw")

        def on_frame_configure(event):
            self.client_canvas.configure(scrollregion=self.client_canvas.bbox("all"))

        def on_mousewheel(event):
            self.client_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.clients_frame.bind("<Configure>", on_frame_configure)
        self.client_canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.show_empty_client_list()

        processing_frame = ttk.LabelFrame(self.organize_files_tab, text="Processing Controls", padding=12)
        processing_frame.pack(fill="x", padx=10, pady=8)

        self.move_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(processing_frame, text="Move files instead of copy", 
                    variable=self.move_files_var, style="TCheckbutton").pack(anchor="w", pady=6)

        button_frame = ttk.Frame(processing_frame, style="TFrame")
        button_frame.pack(fill="x", pady=8)
        
        self.start_btn = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_btn.pack(side="left", padx=(0, 8))
        
        self.pause_btn = ttk.Button(button_frame, text="Pause", command=self.pause_processing, state="disabled")
        self.pause_btn.pack(side="left", padx=(0, 8))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state="disabled")
        self.stop_btn.pack(side="left")
        
        self.progress_bar = ttk.Progressbar(processing_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=6)
        
        self.progress_text = ttk.Label(processing_frame, text="", style="TLabel")
        self.progress_text.pack(pady=4)

        log_frame = ttk.LabelFrame(self.organize_files_tab, text="Activity Log", padding=12)
        log_frame.pack(fill="both", expand=True, padx=10, pady=8)

        log_content_frame = ttk.Frame(log_frame)
        log_content_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(log_content_frame, wrap="word", height=12, 
                            state="disabled", bg="white", fg="#333333", 
                            font=("Consolas", 9), padx=8, pady=8)
        
        log_scrollbar = ttk.Scrollbar(log_content_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

    def setup_placeholder(self, entry, placeholder_text):
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(foreground="black")

        def on_focus_out(event):
            if not entry.get().strip():
                entry.insert(0, placeholder_text)
                entry.config(foreground="grey")
                
        def on_return(event):
            if hasattr(self, 'add_client'):
                self.add_client()

        entry.insert(0, placeholder_text)
        entry.config(foreground="grey")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", on_return)

    def create_settings_tab(self):
        file_settings_frame = ttk.LabelFrame(self.settings_tab, text="File Processing Settings", padding=12)
        file_settings_frame.pack(fill="x", padx=10, pady=8)
        
        ttk.Label(file_settings_frame, text="Supported File Types: PDF, DOCX, TXT", 
                 style="TLabel").pack(anchor="w", pady=2)
        
        ttk.Label(file_settings_frame, 
                 text="Matching Behavior: Client names are searched in filenames and document content.", 
                 style="TLabel", wraplength=800).pack(anchor="w", pady=2)

        about_frame = ttk.LabelFrame(self.settings_tab, text="About", padding=12)
        about_frame.pack(fill="x", padx=10, pady=8)
        
        ttk.Label(about_frame, text="Application Version: v1.0", 
                 style="TLabel").pack(anchor="w", pady=2)
        
        ttk.Label(about_frame, 
                 text="This application helps organize legal documents by client name.", 
                 style="TLabel", wraplength=800).pack(anchor="w", pady=2)
        
        deps_frame = ttk.LabelFrame(self.settings_tab, text="Dependencies", padding=12)
        deps_frame.pack(fill="x", padx=10, pady=8)
        
        try:
            import PyPDF2
            pdf_status = "✓ PyPDF2 installed"
            pdf_color = "green"
        except ImportError:
            pdf_status = "✗ PyPDF2 not installed (PDF processing disabled)"
            pdf_color = "red"
        
        try:
            from docx import Document
            docx_status = "✓ python-docx installed"
            docx_color = "green"
        except ImportError:
            docx_status = "✗ python-docx not installed (DOCX processing disabled)"
            docx_color = "red"
        
        pdf_label = ttk.Label(deps_frame, text=pdf_status, style="TLabel")
        pdf_label.pack(anchor="w", pady=2)
        
        docx_label = ttk.Label(deps_frame, text=docx_status, style="TLabel")
        docx_label.pack(anchor="w", pady=2)

    def show_empty_client_list(self):
        for widget in self.clients_frame.winfo_children():
            widget.destroy()
            
        empty_label = ttk.Label(self.clients_frame, text="No clients configured. Add clients using the field above.", 
                              style="TLabel", foreground="gray")
        empty_label.pack(pady=20)

    def browse_source_dir(self):
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_dir_entry.delete(0, tk.END)
            self.source_dir_entry.insert(0, directory)
            self.log_activity(f"Source directory set to: {directory}", "info")

    def browse_dest_dir(self):
        directory = filedialog.askdirectory(title="Select Destination Directory")
        if directory:
            self.dest_dir_entry.delete(0, tk.END)
            self.dest_dir_entry.insert(0, directory)
            self.log_activity(f"Destination directory set to: {directory}", "info")

    def add_client(self):
        client_name = self.client_name_entry.get().strip()
        
        if client_name.startswith("Enter client name"):
            messagebox.showwarning("Invalid Input", "Please enter a client name.")
            return
        
        if not client_name:
            return
        
        parts = client_name.split()
        client_obj = None
        
        if len(parts) == 2:
            client_obj = Client(parts[0].lower(), "", parts[1].lower())
        elif len(parts) == 3:
            client_obj = Client(parts[0].lower(), parts[1].lower(), parts[2].lower())
        else:
            messagebox.showerror("Invalid Name Format", 
                               "Please enter name as 'First Last' or 'First Middle Last'.")
            return
        
        if client_obj in self.client_list:
            messagebox.showinfo("Duplicate Client", 
                              f"Client '{client_name}' is already in the list.")
            self.log_activity(f"Attempt to add duplicate client: {client_name}", "error")
            return
        
        self.client_list.append(client_obj)
        self.client_name_entry.delete(0, tk.END)
        self.update_client_list_ui()
        self.save_clients_to_config()
        self.log_activity(f"Added client: {client_name}", "info")

    def remove_client(self, client):
        if client in self.client_list:
            self.client_list.remove(client)
            self.update_client_list_ui()
            display_name = organizer.get_client_display_name(client)
            self.save_clients_to_config()
            self.log_activity(f"Removed client: {display_name}", "info")

    def update_client_list_ui(self):
        if hasattr(self, 'client_count_label'):
            self.client_count_label.config(text=f"{len(self.client_list)} clients configured")
        
        for widget in self.clients_frame.winfo_children():
            widget.destroy()

        if not self.client_list:
            self.show_empty_client_list()
            return

        for client in self.client_list:
            display_name = organizer.get_client_display_name(client)
            
            client_card = tk.Frame(self.clients_frame, bg="white", relief="solid", 
                                 borderwidth=1, padx=8, pady=4)
            client_card.pack(fill="x", pady=2, padx=2)
            
            name_label = tk.Label(client_card, text=display_name, bg="white", 
                                font=("Segoe UI", 9), anchor="w")
            name_label.pack(side="left", fill="x", expand=True)
            
            remove_btn = tk.Button(client_card, text="×", font=("Arial", 12, "bold"),
                                 fg="#dc2626", bg="white", relief="flat",
                                 command=lambda c=client: self.remove_client(c),
                                 cursor="hand2")
            remove_btn.pack(side="right")
            
            def on_enter(e, btn=remove_btn):
                btn.config(bg="#fef2f2")
                
            def on_leave(e, btn=remove_btn):
                btn.config(bg="white")
                
            remove_btn.bind("<Enter>", on_enter)
            remove_btn.bind("<Leave>", on_leave)

    def load_clients_from_config(self):
        if not self.config_file.exists():
            return

        self.config_parser.read(self.config_file)
        if 'Clients' in self.config_parser:
            loaded_clients = []
            for key, value in self.config_parser['Clients'].items():
                parts = value.split()
                if len(parts) == 2:
                    loaded_clients.append(Client(parts[0], "", parts[1]))
                elif len(parts) == 3:
                    loaded_clients.append(Client(parts[0], parts[1], parts[2]))
            
            if loaded_clients:
                self.client_list = loaded_clients
                self.update_client_list_ui()
                self.log_activity(f"Loaded {len(loaded_clients)} clients from config.", "info")

    def save_clients_to_config(self):
        self.config_parser['Clients'] = {}
        for i, client in enumerate(self.client_list):
            name_str = " ".join(filter(None, client))
            self.config_parser['Clients'][f'client_{i}'] = name_str
        
        try:
            with open(self.config_file, 'w') as f:
                self.config_parser.write(f)
        except Exception as e:
            self.log_activity(f"Error saving client list: {e}", "error")

    def get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def log_activity(self, message, log_type="info"):
        self.log_text.config(state="normal")
        
        timestamp = self.get_timestamp()
        
        log_config = {
            "info": ("[INFO]", "blue"),
            "success": ("[SUCCESS]", "green"),
            "error": ("[ERROR]", "red"),
            "file": ("[FILE]", "darkblue")
        }
        
        prefix, color = log_config.get(log_type, ("[INFO]", "blue"))
        
        self.log_text.insert(tk.END, f"{prefix} {message} ({timestamp})\n")
        
        start_index = self.log_text.index("end-2l")
        end_index = self.log_text.index("end-1c")
        self.log_text.tag_add(log_type, start_index, end_index)
        self.log_text.tag_config(log_type, foreground=color)
        
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def post_log_message(self, message, log_type="info"):
        self.after(0, self.log_activity, message, log_type)

    def post_progress_update(self, processed_count, total_count):
        def update():
            if total_count > 0:
                percent = int((processed_count / total_count) * 100)
                self.progress_bar["value"] = percent
                self.progress_text.config(text=f"Processing file {processed_count} of {total_count}... {percent}%")
            
            if processed_count == total_count:
                self.progress_text.config(text="Processing complete!")
                self.status_label.config(text="Ready")
                self.toggle_controls(processing=False)
        
        self.after(0, update)

    def toggle_controls(self, processing=True):
        if processing:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
        else:
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")

    def start_processing(self):
        source_dir = self.source_dir_entry.get().strip()
        dest_dir = self.dest_dir_entry.get().strip()

        if not source_dir:
            messagebox.showerror("Error", "Please select a source directory.")
            self.log_activity("No source directory selected", "error")
            return
            
        if not dest_dir:
            messagebox.showerror("Error", "Please select a destination directory.")
            self.log_activity("No destination directory selected", "error")
            return
            
        if not os.path.isdir(source_dir):
            messagebox.showerror("Error", "Invalid Source Directory.")
            self.log_activity(f"Invalid source directory: {source_dir}", "error")
            return
            
        if not os.path.isdir(dest_dir):
            messagebox.showerror("Error", "Invalid Destination Directory.")
            self.log_activity(f"Invalid destination directory: {dest_dir}", "error")
            return
            
        if not self.client_list:
            messagebox.showerror("Error", "No clients configured.")
            self.log_activity("No clients configured for processing", "error")
            return

        self.stop_event.clear()
        self.pause_event.set()
        
        self.toggle_controls(processing=True)
        self.status_label.config(text="Processing...")
        self.log_activity("Processing started...", "info")
        self.progress_bar["value"] = 0
        
        config = {
            'src_path': Path(source_dir),
            'dest_path': Path(dest_dir),
            'clients_list': self.client_list,
            'do_move': self.move_files_var.get(),
            'log_callback': self.post_log_message,
            'progress_callback': self.post_progress_update,
            'stop_event': self.stop_event
        }
        
        self.processing_thread = threading.Thread(
            target=organizer.run_organization_task,
            args=(config,),
            daemon=True
        )
        self.processing_thread.start()

    def pause_processing(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.log_activity("Processing paused", "info")
            self.status_label.config(text="Paused")
            self.pause_btn.config(text="Resume")
        else:
            self.pause_event.set()
            self.log_activity("Processing resumed", "info")
            self.status_label.config(text="Processing...")
            self.pause_btn.config(text="Pause")

    def stop_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.log_activity("Stop requested by user. Finishing current file...", "error")
            self.stop_event.set()
        else:
            self.log_activity("No process to stop.", "info")
        
        self.status_label.config(text="Ready")
        self.progress_bar["value"] = 0
        self.progress_text.config(text="")
        self.toggle_controls(processing=False)

    def batch_import_clients(self):
        file_path = filedialog.askopenfilename(
            title="Select Client List File",
            filetypes=[("Supported Files", "*.txt *.csv *.xlsx")]
        )
        if not file_path:
            return

        new_clients = set()
        duplicates = 0
        added = 0

        try:
            ext = Path(file_path).suffix.lower()

            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        name = line.strip()
                        if name:
                            new_clients.add(name)

            elif ext in [".csv", ".xlsx"]:
                df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
                if df.empty:
                    messagebox.showwarning("Empty File", "The spreadsheet contains no data.")
                    return

                orientation_window = Toplevel(self)
                orientation_window.title("Select Orientation")
                orientation_window.geometry("300x150")
                orientation_window.transient(self)
                orientation_window.grab_set()

                tk.Label(orientation_window, text="How are client names arranged?").pack(pady=10)
                orientation_choice = tk.StringVar(value="column")

                ttk.Radiobutton(orientation_window, text="Single Column", variable=orientation_choice, value="column").pack(anchor="w", padx=40)
                ttk.Radiobutton(orientation_window, text="Single Row", variable=orientation_choice, value="row").pack(anchor="w", padx=40)

                confirmed = tk.BooleanVar(value=False)

                def confirm_orientation():
                    confirmed.set(True)
                    orientation_window.destroy()

                ttk.Button(orientation_window, text="Next", command=confirm_orientation).pack(pady=10)
                orientation_window.wait_variable(confirmed)
                orientation = orientation_choice.get()

                if orientation == "column":
                    col_window = Toplevel(self)
                    col_window.title("Select Column")
                    col_window.geometry("300x200")
                    col_window.transient(self)
                    col_window.grab_set()

                    ttk.Label(col_window, text="Select the column with client names:").pack(pady=10)
                    columns = list(df.columns)
                    col_choice = tk.StringVar(value=columns[0])

                    col_dropdown = ttk.Combobox(col_window, textvariable=col_choice, values=columns, state="readonly")
                    col_dropdown.pack(pady=5)

                    skip_header_var = tk.BooleanVar(value=False)
                    ttk.Checkbutton(col_window, text="First row is header (skip)", variable=skip_header_var).pack(pady=5)

                    confirm = tk.BooleanVar(value=False)

                    def confirm_column():
                        confirm.set(True)
                        col_window.destroy()

                    ttk.Button(col_window, text="Import", command=confirm_column).pack(pady=10)
                    col_window.wait_variable(confirm)

                    series = df[col_choice.get()]
                    if skip_header_var.get():
                        series = series[1:]

                    for val in series:
                        if isinstance(val, str) and val.strip():
                            new_clients.add(val.strip())

                else:
                    row_window = Toplevel(self)
                    row_window.title("Select Row")
                    row_window.geometry("300x200")
                    row_window.transient(self)
                    row_window.grab_set()

                    ttk.Label(row_window, text="Select the row with client names:").pack(pady=10)
                    row_indices = [f"Row {i+1}" for i in range(len(df))]
                    row_choice = tk.StringVar(value=row_indices[0])

                    row_dropdown = ttk.Combobox(row_window, textvariable=row_choice, values=row_indices, state="readonly")
                    row_dropdown.pack(pady=5)

                    skip_first_var = tk.BooleanVar(value=False)
                    ttk.Checkbutton(row_window, text="First column is header (skip)", variable=skip_first_var).pack(pady=5)

                    confirm = tk.BooleanVar(value=False)

                    def confirm_row():
                        confirm.set(True)
                        row_window.destroy()

                    ttk.Button(row_window, text="Import", command=confirm_row).pack(pady=10)
                    row_window.wait_variable(confirm)

                    idx = int(row_choice.get().split()[-1]) - 1
                    row = df.iloc[idx]
                    if skip_first_var.get():
                        row = row[1:]
                    for val in row:
                        if isinstance(val, str) and val.strip():
                            new_clients.add(val.strip())

            for name in new_clients:
                parts = name.split()
                if len(parts) == 2:
                    client_obj = Client(parts[0].lower(), "", parts[1].lower())
                elif len(parts) == 3:
                    client_obj = Client(parts[0].lower(), parts[1].lower(), parts[2].lower())
                else:
                    continue

                if client_obj not in self.client_list:
                    self.client_list.append(client_obj)
                    added += 1
                else:
                    duplicates += 1

            self.update_client_list_ui()
            self.save_clients_to_config()
            messagebox.showinfo("Import Complete", f"Import successful.\n{added} new clients added.\n{duplicates} duplicates skipped.")
            self.log_activity(f"Batch import complete: {added} added, {duplicates} duplicates skipped.", "success")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import clients: {e}")
            self.log_activity(f"Batch import failed: {e}", "error")


if __name__ == "__main__":
    app = LawyerFileOrganizerUI()
    app.mainloop()