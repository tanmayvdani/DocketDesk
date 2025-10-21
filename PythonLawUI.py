import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime

class LawyerFileOrganizerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lawyer File Organizer")
        self.geometry("896x700")  # Max width 4xl (896px), height 700px
        self.resizable(False, False)
        self.configure(bg="#f3f4f6")  # Light gray background

        # Initialize client list BEFORE creating widgets
        self.client_list = []
        
        # Apply styling first
        self.apply_styles()
        
        # Create custom title bar
        self.create_title_bar()
        
        # Create all widgets
        self.create_widgets()
        
        # Center the window after initial rendering
        self.after(100, self.center_window)

    def center_window(self):
        """Center the window on screen after it's rendered"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def apply_styles(self):
        """Apply Windows 11-like styling with fallback themes"""
        self.style = ttk.Style(self)
        
        # Try different themes in order of preference
        for theme in ["vista", "xpnative", "winnative", "clam", "alt", "default"]:
            try:
                self.style.theme_use(theme)
                break
            except tk.TclError:
                continue

        # Configure styles
        self.style.configure("TFrame", background="#f3f4f6")
        self.style.configure("TLabel", background="#f3f4f6", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9), padding=(8, 4))
        self.style.configure("TEntry", padding=4)
        self.style.configure("TCheckbutton", background="#f3f4f6", font=("Segoe UI", 9))
        self.style.configure("TNotebook", background="#f3f4f6")
        self.style.configure("TNotebook.Tab", padding=(12, 6))
        
        # Custom styles
# Custom styles
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
        """Create a custom title bar"""
        title_bar = ttk.Frame(self, style="Title.TFrame", height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)  # Prevent frame from shrinking
        
        # Title
        title_label = ttk.Label(title_bar, text="Lawyer File Organizer", style="Title.TLabel")
        title_label.pack(side="left", padx=10)
        
        # Window controls (minimize, maximize, close) - placeholder
        controls_frame = ttk.Frame(title_bar, style="Title.TFrame")
        controls_frame.pack(side="right", padx=5)
        
        # Add some spacing
        ttk.Frame(title_bar, style="Title.TFrame", width=100).pack(side="right")

    def create_widgets(self):
        # Main container frame for content below title bar
        self.content_frame = ttk.Frame(self, style="TFrame")
        self.content_frame.pack(fill="both", expand=True, padx=12, pady=12)

        # Tab Navigation
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill="both", expand=True)

        self.organize_files_tab = ttk.Frame(self.notebook, style="TFrame")
        self.settings_tab = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.organize_files_tab, text="Organize Files")
        self.notebook.add(self.settings_tab, text="Settings")

        self.create_organize_files_tab()
        self.create_settings_tab()

        # Status Bar - MUST be created last
        self.create_status_bar()

    def create_status_bar(self):
        """Create the status bar separately to ensure it's created after everything else"""
        self.status_bar = ttk.Frame(self, style="TFrame", relief="sunken", borderwidth=1)
        self.status_bar.pack(side="bottom", fill="x")
        self.status_label = ttk.Label(self.status_bar, text="Ready", style="TLabel")
        self.status_label.pack(side="left", padx=10)
        
        ttk.Separator(self.status_bar, orient="vertical").pack(side="left", fill="y", padx=5)
        
        self.client_count_label = ttk.Label(self.status_bar, text="0 clients configured", style="TLabel")
        self.client_count_label.pack(side="left", padx=5)

    def create_organize_files_tab(self):
        # Configuration Section
        config_frame = ttk.LabelFrame(self.organize_files_tab, text="Configuration", padding=12)
        config_frame.pack(fill="x", padx=10, pady=8)

        # Source Directory
        source_frame = ttk.Frame(config_frame, style="TFrame")
        source_frame.pack(fill="x", pady=6)
        ttk.Label(source_frame, text="Source Directory:", style="TLabel").pack(side="left", padx=(0, 8))
        
        self.source_dir_entry = ttk.Entry(source_frame, width=50)
        self.source_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ttk.Button(source_frame, text="Browse", command=self.browse_source_dir).pack(side="left")

        # Destination Directory
        dest_frame = ttk.Frame(config_frame, style="TFrame")
        dest_frame.pack(fill="x", pady=6)
        ttk.Label(dest_frame, text="Destination Directory:", style="TLabel").pack(side="left", padx=(0, 8))
        
        self.dest_dir_entry = ttk.Entry(dest_frame, width=50)
        self.dest_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ttk.Button(dest_frame, text="Browse", command=self.browse_dest_dir).pack(side="left")

        # Client Manager Component
        client_manager_frame = ttk.LabelFrame(self.organize_files_tab, text="Client Names", padding=12)
        client_manager_frame.pack(fill="x", padx=10, pady=8)

        client_input_frame = ttk.Frame(client_manager_frame, style="TFrame")
        client_input_frame.pack(fill="x", pady=8)
        
        # Client Name Entry with placeholder
        self.client_name_entry = ttk.Entry(client_input_frame, width=40)
        self.client_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Setup placeholder functionality
        self.setup_placeholder(self.client_name_entry, "Enter client name")
        
        ttk.Button(client_input_frame, text="Add Client", command=self.add_client).pack(side="left")
        self.clients_frame = ttk.Frame(client_manager_frame, style="TFrame")
        self.clients_frame.pack(fill="both", expand=True, pady=8)
        
        # Don't call update_client_list_ui here - it will be called when we add clients
        # Just show the initial empty state
        self.show_empty_client_list()

        # Processing Panel Component
        processing_frame = ttk.LabelFrame(self.organize_files_tab, text="Processing Controls", padding=12)
        processing_frame.pack(fill="x", padx=10, pady=8)

        self.move_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(processing_frame, text="Move files instead of copy", 
                       variable=self.move_files_var, style="TCheckbutton").pack(anchor="w", pady=6)

        button_frame = ttk.Frame(processing_frame, style="TFrame")
        button_frame.pack(fill="x", pady=8)
        
        ttk.Button(button_frame, text="Start Processing", 
                command=self.start_processing).pack(side="left", padx=(0, 8))
        ttk.Button(button_frame, text="Pause", 
                command=self.pause_processing).pack(side="left", padx=(0, 8))
        ttk.Button(button_frame, text="Stop", 
                command=self.stop_processing).pack(side="left")
        
        self.progress_bar = ttk.Progressbar(processing_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=6)
        
        self.progress_text = ttk.Label(processing_frame, text="", style="TLabel")
        self.progress_text.pack(pady=4)

        # Activity Log Component
        log_frame = ttk.LabelFrame(self.organize_files_tab, text="Activity Log", padding=12)
        log_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # Create a frame for the text widget and scrollbar
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
        """Setup placeholder text for an entry widget"""
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
        # File Processing Settings
        file_settings_frame = ttk.LabelFrame(self.settings_tab, text="File Processing Settings", padding=12)
        file_settings_frame.pack(fill="x", padx=10, pady=8)
        
        ttk.Label(file_settings_frame, text="Supported File Types: PDF, DOCX, TXT", 
                 style="TLabel").pack(anchor="w", pady=2)
        
        ttk.Label(file_settings_frame, 
                 text="Matching Behavior: Client names are searched in filenames and document content.", 
                 style="TLabel", wraplength=800).pack(anchor="w", pady=2)

        # About Section
        about_frame = ttk.LabelFrame(self.settings_tab, text="About", padding=12)
        about_frame.pack(fill="x", padx=10, pady=8)
        
        ttk.Label(about_frame, text="Application Version: v1.0", 
                 style="TLabel").pack(anchor="w", pady=2)
        
        ttk.Label(about_frame, 
                 text="This application helps organize legal documents by client name.", 
                 style="TLabel", wraplength=800).pack(anchor="w", pady=2)

    def show_empty_client_list(self):
        """Show empty state for client list"""
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
        
        # Check if it's placeholder text
        if client_name == "Enter client name":
            messagebox.showwarning("Invalid Input", "Please enter a client name.")
            return
            
        if client_name and client_name not in self.client_list:
            self.client_list.append(client_name)
            self.client_name_entry.delete(0, tk.END)
            self.update_client_list_ui()
            self.log_activity(f"Added client: {client_name}", "info")
        elif client_name in self.client_list:
            messagebox.showinfo("Duplicate Client", f"Client '{client_name}' already exists.")
            self.log_activity(f"Attempt to add duplicate client: {client_name}", "error")

    def remove_client(self, client_name):
        if client_name in self.client_list:
            self.client_list.remove(client_name)
            self.update_client_list_ui()
            self.log_activity(f"Removed client: {client_name}", "info")

    def update_client_list_ui(self):
        """Update the client list display and status bar"""
        # Update status bar if it exists
        if hasattr(self, 'client_count_label'):
            self.client_count_label.config(text=f"{len(self.client_list)} clients configured")
        
        # Clear existing client cards
        for widget in self.clients_frame.winfo_children():
            widget.destroy()

        if not self.client_list:
            self.show_empty_client_list()
            return

        # Create client cards
        for client in self.client_list:
            client_card = tk.Frame(self.clients_frame, bg="white", relief="solid", 
                                 borderwidth=1, padx=8, pady=4)
            client_card.pack(fill="x", pady=2, padx=2)
            
            # Client name label
            name_label = tk.Label(client_card, text=client, bg="white", 
                                font=("Segoe UI", 9), anchor="w")
            name_label.pack(side="left", fill="x", expand=True)
            
            # Remove button
            remove_btn = tk.Button(client_card, text="×", font=("Arial", 12, "bold"),
                                 fg="#dc2626", bg="white", relief="flat",
                                 command=lambda c=client: self.remove_client(c),
                                 cursor="hand2")
            remove_btn.pack(side="right")
            
            # Hover effects
            def on_enter(e, btn=remove_btn):
                btn.config(bg="#fef2f2")
                
            def on_leave(e, btn=remove_btn):
                btn.config(bg="white")
                
            remove_btn.bind("<Enter>", on_enter)
            remove_btn.bind("<Leave>", on_leave)

    def get_timestamp(self):
        """Get current timestamp for logging"""
        return datetime.now().strftime("%H:%M:%S")

    def log_activity(self, message, log_type="info"):
        """Add entry to activity log with proper formatting"""
        self.log_text.config(state="normal")
        
        timestamp = self.get_timestamp()
        
        # Define log type prefixes and colors
        log_config = {
            "info": ("[INFO]", "blue"),
            "success": ("[SUCCESS]", "green"),
            "error": ("[ERROR]", "red"),
            "file": ("[FILE]", "darkblue")
        }
        
        prefix, color = log_config.get(log_type, ("[INFO]", "blue"))
        
        # Insert the log entry
        self.log_text.insert(tk.END, f"{prefix} {message} ({timestamp})\n")
        
        # Apply color to the last inserted line
        start_index = self.log_text.index("end-2l")
        end_index = self.log_text.index("end-1c")
        self.log_text.tag_add(log_type, start_index, end_index)
        self.log_text.tag_config(log_type, foreground=color)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def start_processing(self):
        """Start file processing with validation"""
        source_dir = self.source_dir_entry.get().strip()
        dest_dir = self.dest_dir_entry.get().strip()

        # Validation
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

        # Start processing simulation
        self.log_activity("Processing started...", "info")
        self.status_label.config(text="Processing...")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100
        
        # Simulate progress updates
        self.simulate_progress()

    def simulate_progress(self):
        """Simulate file processing progress (for demo purposes)"""
        self.progress_value = 0
        
        def update_progress():
            if self.progress_value < 100:
                self.progress_value += 5
                self.progress_bar["value"] = self.progress_value
                self.progress_text.config(text=f"Processing files... {self.progress_value}%")
                self.after(200, update_progress)
            else:
                self.progress_bar["value"] = 100
                self.progress_text.config(text="Processing complete!")
                self.log_activity("Processing finished successfully", "success")
                self.status_label.config(text="Ready")
                messagebox.showinfo("Processing Complete", "File processing completed successfully!")

        update_progress()

    def pause_processing(self):
        """Pause the file processing"""
        self.log_activity("Processing paused", "info")
        self.status_label.config(text="Paused")
        # In a real implementation, you would pause the processing thread here

    def stop_processing(self):
        """Stop the file processing"""
        self.log_activity("Processing stopped by user", "info")
        self.status_label.config(text="Ready")
        self.progress_bar["value"] = 0
        self.progress_text.config(text="")
        # In a real implementation, you would stop the processing thread here


if __name__ == "__main__":
    app = LawyerFileOrganizerUI()
    app.mainloop()