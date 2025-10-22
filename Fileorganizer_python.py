import os
import sys
import re
import shutil
import logging
import functools
import threading
from pathlib import Path
from collections import namedtuple, defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor

# Optional imports
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import ahocorasick
except ImportError:
    ahocorasick = None

# --- Logging setup (used only for standalone mode) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

Client = namedtuple("Client", ["first", "middle", "last"])

# ====================================================
# Utility Functions
# ====================================================

def get_client_display_name(client: Client) -> str:
    """Get a display-friendly, capitalized name for the client."""
    if client.middle:
        return f"{client.first.capitalize()} {client.middle.capitalize()} {client.last.capitalize()}"
    else:
        return f"{client.first.capitalize()} {client.last.capitalize()}"

def has_valid_extension(file_path):
    return file_path.suffix.lower() in [".pdf", ".docx", ".txt"]

def extract_text(file_path):
    ext = file_path.suffix.lower()
    try:
        if ext == ".txt":
            return file_path.read_text(encoding='utf-8', errors='ignore')
        elif ext == ".pdf" and PdfReader:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                return "\n".join(page.extract_text() or '' for page in reader.pages)
        elif ext == ".docx" and Document:
            doc = Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)
    except Exception:
        return ""
    return ""

def get_base_folder_name(client):
    parts = [client.last, client.middle, client.first]
    return "_".join(part for part in parts if part)

def build_automaton(clients):
    if not ahocorasick:
        return None
    A = ahocorasick.Automaton()
    for client in clients:
        A.add_word(client.first.lower(), (client, 'first'))
        A.add_word(client.last.lower(), (client, 'last'))
        if client.middle:
            A.add_word(client.middle.lower(), (client, 'middle'))
    A.make_automaton()
    return A

def find_client_match(text, automaton, clients):
    text_lower = text.lower()
    if automaton:
        found_parts = defaultdict(set)
        for end_index, (client, part) in automaton.iter(text_lower):
            start_index = end_index - len(getattr(client, part)) + 1
            if start_index > 0 and text_lower[start_index - 1].isalnum():
                continue
            if end_index < len(text_lower) - 1 and text_lower[end_index + 1].isalnum():
                continue
            found_parts[client].add(part)
        for client, parts in found_parts.items():
            if 'first' in parts and 'last' in parts:
                return client
    else:
        for client in clients:
            if re.search(fr'\b{client.first.lower()}\b', text_lower) and re.search(fr'\b{client.last.lower()}\b', text_lower):
                return client
    return None

def generate_folder_names(clients):
    folder_map = {}
    name_counts = Counter()
    for client in clients:
        base = get_base_folder_name(client)
        count = name_counts[base]
        name_counts[base] += 1
        folder_map[client] = base if count == 0 else f"{base}_{count+1}"
    return folder_map

def collect_files(src_path: Path):
    files = []
    src_path = Path(src_path)
    if src_path.drive and not str(src_path).startswith("\\\\?\\"):
        src_path = Path(f"\\\\?\\{src_path}")
    for entry in src_path.rglob("*"):
        try:
            if entry.is_file() and has_valid_extension(entry):
                files.append(entry)
        except (PermissionError, OSError):
            continue
    return files

def get_unique_filepath(target_dir, filename):
    target_path = target_dir / filename
    if not target_path.exists():
        return target_path
    stem, suffix = target_path.stem, target_path.suffix
    counter = 1
    while True:
        new_path = target_dir / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

# ====================================================
# Core Logic for GUI or External Control
# ====================================================

def run_organization_task(config):
    src_path = Path(config['src_path'])
    dest_path = Path(config['dest_path'])
    clients = config['clients_list']
    do_move = config['do_move']
    dry_run = config.get('dry_run', False)
    stop_event = config.get('stop_event', threading.Event())

    log = config.get('log_callback', lambda msg, cat='info': print(f"[{cat}] {msg}"))
    progress = config.get('progress_callback', lambda done, total: None)

    folder_map = generate_folder_names(clients)
    automaton = build_automaton(clients)

    files = collect_files(src_path)
    if not files:
        log("No valid files found.", 'info')
        return

    log(f"Found {len(files)} files to process.", 'info')

    stats = Counter()

    def worker_func(file_path):
        if stop_event.is_set():
            return ('CANCELLED', file_path, None)
        match_type = None
        matched_client = None

        filename_client = find_client_match(file_path.name, automaton, clients)
        if filename_client:
            matched_client = filename_client
            match_type = "FILENAME"
        else:
            text = extract_text(file_path)
            if text:
                content_client = find_client_match(text, automaton, clients)
                if content_client:
                    matched_client = content_client
                    match_type = "CONTENT"

        if matched_client:
            folder_name = folder_map[matched_client]
            target_dir = dest_path / folder_name
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = get_unique_filepath(target_dir, file_path.name)

            if not dry_run:
                try:
                    (shutil.move if do_move else shutil.copy)(file_path, target_path)
                    log(f"[{match_type}] {file_path.name} -> {folder_name}", 'file')
                    return (match_type, file_path, target_path)
                except Exception as e:
                    log(f"Error processing {file_path.name}: {e}", 'error')
                    return ('ERROR', file_path, None)
            else:
                log(f"[DRY-RUN] {file_path.name} would go to {folder_name}", 'info')
                return (match_type, file_path, target_path)
        else:
            log(f"[NO MATCH] {file_path.name}", 'info')
            return ('NO_MATCH', file_path, None)

    total_files = len(files)
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        done_count = 0
        for result in executor.map(worker_func, files):
            if stop_event.is_set():
                log("Processing was cancelled by user.", 'error')
                return
            stats[result[0]] += 1
            done_count += 1
            progress(done_count, total_files)

    log(f"Completed: {dict(stats)}", 'summary')

# ====================================================
# Standalone Mode for Testing
# ====================================================

if __name__ == "__main__":
    clients = [Client('john', '', 'doe'), Client('jane', '', 'smith')]
    stop_event = threading.Event()

    config = {
        'src_path': input("Enter source folder: "),
        'dest_path': input("Enter destination folder: "),
        'clients_list': clients,
        'do_move': False,
        'dry_run': True,
        'log_callback': lambda msg, cat='info': logger.info(msg),
        'progress_callback': lambda done, total: logger.info(f"Progress: {done}/{total}"),
        'stop_event': stop_event
    }

    run_organization_task(config)
