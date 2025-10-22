"""
Backend module for organizing legal documents by client name.
Processes PDF, DOCX, and TXT files, searching for client names in filenames and content.
"""

import os
import shutil
from pathlib import Path
from collections import namedtuple
from typing import List, Callable, Optional
import threading
import re

# For PDF reading
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# For DOCX reading
try:
    from docx import Document
except ImportError:
    Document = None

# Client namedtuple definition
Client = namedtuple('Client', ['first', 'middle', 'last'])

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text content from a PDF file."""
    if PyPDF2 is None:
        return ""
    
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.lower()
    except Exception as e:
        return ""


def extract_text_from_docx(file_path: Path) -> str:
    """Extract text content from a DOCX file."""
    if Document is None:
        return ""
    
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.lower()
    except Exception as e:
        return ""


def extract_text_from_txt(file_path: Path) -> str:
    """Extract text content from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read().lower()
    except Exception as e:
        return ""


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from file based on extension."""
    ext = file_path.suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        return ""


def client_matches_file(client: Client, file_path: Path) -> bool:
    """
    Check if a client's name appears in the filename or file content.
    
    Args:
        client: Client namedtuple with first, middle, last names
        file_path: Path to the file to check
    
    Returns:
        True if client name is found in filename or content
    """
    # Get filename without extension
    filename = file_path.stem.lower()
    
    # Build search patterns for the client name
    patterns = []
    
    # Full name pattern (with middle name if present)
    if client.middle:
        full_name = f"{client.first}.*{client.middle}.*{client.last}"
        patterns.append(full_name)
    
    # First and last name pattern (ignoring middle)
    first_last = f"{client.first}.*{client.last}"
    patterns.append(first_last)
    
    # Last name followed by first name (common in legal documents)
    last_first = f"{client.last}.*{client.first}"
    patterns.append(last_first)
    
    # Check filename first (faster)
    for pattern in patterns:
        if re.search(pattern, filename):
            return True
    
    # Check file content if no match in filename
    content = extract_text_from_file(file_path)
    if content:
        for pattern in patterns:
            if re.search(pattern, content):
                return True
    
    return False


def get_client_display_name(client: Client) -> str:
    """Get a display name for the client."""
    if client.middle:
        return f"{client.first.capitalize()} {client.middle.capitalize()} {client.last.capitalize()}"
    else:
        return f"{client.first.capitalize()} {client.last.capitalize()}"


def get_client_folder_name(client: Client) -> str:
    """Get a safe folder name for the client."""
    if client.middle:
        return f"{client.last.capitalize()}_{client.first.capitalize()}_{client.middle.capitalize()}"
    else:
        return f"{client.last.capitalize()}_{client.first.capitalize()}"


def organize_files(src_path: Path, dest_path: Path, clients_list: List[Client], 
                   do_move: bool = False, 
                   log_callback: Optional[Callable] = None,
                   progress_callback: Optional[Callable] = None,
                   stop_event: Optional[threading.Event] = None) -> dict:
    """
    Organize files from source to destination based on client names.
    
    Args:
        src_path: Source directory path
        dest_path: Destination directory path
        clients_list: List of Client namedtuples
        do_move: If True, move files instead of copying
        log_callback: Optional callback function for logging (message, log_type)
        progress_callback: Optional callback for progress updates (processed, total)
        stop_event: Optional threading.Event to signal stop
    
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'processed': 0,
        'matched': 0,
        'unmatched': 0,
        'errors': 0,
        'stopped': False
    }
    
    def log(message: str, log_type: str = "info"):
        """Helper to call log_callback if provided."""
        if log_callback:
            log_callback(message, log_type)
    
    def update_progress(processed: int, total: int):
        """Helper to call progress_callback if provided."""
        if progress_callback:
            progress_callback(processed, total)
    
    # Gather all files to process
    files_to_process = []
    for root, dirs, files in os.walk(src_path):
        for filename in files:
            file_path = Path(root) / filename
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files_to_process.append(file_path)
    
    total_files = len(files_to_process)
    log(f"Found {total_files} files to process", "info")
    
    if total_files == 0:
        log("No supported files found in source directory", "error")
        return stats
    
    # Process each file
    for idx, file_path in enumerate(files_to_process, 1):
        # Check for stop signal
        if stop_event and stop_event.is_set():
            log("Processing stopped by user", "error")
            stats['stopped'] = True
            break
        
        try:
            filename = file_path.name
            log(f"Processing: {filename}", "file")
            
            matched_client = None
            
            # Check each client
            for client in clients_list:
                if client_matches_file(client, file_path):
                    matched_client = client
                    break
            
            if matched_client:
                # Create client folder
                client_folder_name = get_client_folder_name(matched_client)
                client_folder = dest_path / client_folder_name
                client_folder.mkdir(parents=True, exist_ok=True)
                
                # Destination file path
                dest_file = client_folder / filename
                
                # Handle duplicate filenames
                counter = 1
                while dest_file.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    dest_file = client_folder / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Move or copy the file
                if do_move:
                    shutil.move(str(file_path), str(dest_file))
                    action = "Moved"
                else:
                    shutil.copy2(str(file_path), str(dest_file))
                    action = "Copied"
                
                client_display = get_client_display_name(matched_client)
                log(f"{action}: {filename} → {client_display}/", "success")
                stats['matched'] += 1
            else:
                log(f"No match: {filename}", "info")
                stats['unmatched'] += 1
            
            stats['processed'] += 1
            update_progress(stats['processed'], total_files)
            
        except Exception as e:
            log(f"Error processing {file_path.name}: {str(e)}", "error")
            stats['errors'] += 1
    
    # Final summary
    if not stats['stopped']:
        log(f"Processing complete: {stats['matched']} matched, {stats['unmatched']} unmatched, {stats['errors']} errors", "success")
    
    return stats


def run_organization_task(config: dict):
    """
    Main entry point for running the organization task.
    Designed to be called from a separate thread.
    
    Args:
        config: Dictionary containing:
            - src_path: Source directory Path
            - dest_path: Destination directory Path
            - clients_list: List of Client objects
            - do_move: Boolean for move vs copy
            - log_callback: Logging callback function
            - progress_callback: Progress callback function
            - stop_event: threading.Event for stopping
    """
    try:
        stats = organize_files(
            src_path=config['src_path'],
            dest_path=config['dest_path'],
            clients_list=config['clients_list'],
            do_move=config.get('do_move', False),
            log_callback=config.get('log_callback'),
            progress_callback=config.get('progress_callback'),
            stop_event=config.get('stop_event')
        )
        return stats
    except Exception as e:
        if config.get('log_callback'):
            config['log_callback'](f"Fatal error: {str(e)}", "error")
        return None