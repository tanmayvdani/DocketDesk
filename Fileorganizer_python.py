import os
import sys
import re
import shutil
import argparse
import logging
import functools
from pathlib import Path
from collections import namedtuple, defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor

# Attempt to import necessary text extraction libraries
try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Warning: PyPDF2 is not installed. PDF processing will fail.", file=sys.stderr)
    print("Install it with: pip install PyPDF2", file=sys.stderr)
    PdfReader = None

try:
    from docx import Document
except ImportError:
    print("Warning: python-docx is not installed. DOCX processing will fail.", file=sys.stderr)
    print("Install it with: pip install python-docx", file=sys.stderr)
    Document = None

try:
    import ahocorasick
except ImportError:
    print("Warning: pyahocorasick is not installed. The script will be slower.", file=sys.stderr)
    print("Install it with: pip install pyahocorasick", file=sys.stderr)
    ahocorasick = None

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm is not installed. No progress bar will be shown.", file=sys.stderr)
    print("Install it with: pip install tqdm", file=sys.stderr)
    tqdm = None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

# Setup logger for failed files
failed_file_logger = logging.getLogger('failed_files')
failed_file_logger.addHandler(logging.FileHandler('failed_files.log', mode='w'))
failed_file_logger.propagate = False

# Represents a client with first, middle, and last names
Client = namedtuple("Client", ["first", "middle", "last"])

def get_base_folder_name(client):
    """Generates the base folder name for a client."""
    parts = [client.last, client.middle, client.first]
    return "_".join(part for part in parts if part)

# ======================= Utility ============================

def has_valid_extension(file_path):
    """Checks if the file has a supported extension."""
    return file_path.suffix.lower() in [".pdf", ".docx", ".txt"]

def extract_text(file_path):
    """Extracts text from a file based on its extension."""
    ext = file_path.suffix.lower()
    try:
        if ext == ".txt":
            return file_path.read_text(encoding='utf-8', errors='ignore')
        elif ext == ".pdf" and PdfReader:
            if not PdfReader:
                logger.error(f"PyPDF2 is required to read {file_path.name} but is not installed.")
                return ""
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                texts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
                return "\n".join(texts)
        elif ext == ".docx" and Document:
            if not Document:
                logger.error(f"python-docx is required to read {file_path.name} but is not installed.")
                return ""
            doc = Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        logger.error(f"Error extracting text from {file_path.name}: {e}")
    return ""

def build_automaton(clients):
    """Builds an Aho-Corasick automaton for efficient multi-keyword search."""
    if not ahocorasick:
        return None
        
    A = ahocorasick.Automaton()
    for client in clients:
        # Add name parts as plain strings (not regex patterns)
        A.add_word(client.first.lower(), (client, 'first'))
        A.add_word(client.last.lower(), (client, 'last'))
        if client.middle:
            A.add_word(client.middle.lower(), (client, 'middle'))
    A.make_automaton()
    return A

def find_client_match(text, automaton, clients):
    """
    Finds the first client that has both their first and last name in the text.
    Uses an automaton for fast searching, otherwise falls back to a simple loop.
    """
    text_lower = text.lower()
    
    if automaton:
        # Efficiently find all name parts present in the text
        found_parts = defaultdict(set)
        
        # Find all matches using the automaton
        for end_index, (client, name_part) in automaton.iter(text_lower):
            # Verify word boundaries manually
            start_index = end_index - len(getattr(client, name_part)) + 1
            
            # Check if character before is a word boundary (or start of string)
            if start_index > 0:
                char_before = text_lower[start_index - 1]
                if char_before.isalnum() or char_before == '_':
                    continue
            
            # Check if character after is a word boundary (or end of string)
            if end_index < len(text_lower) - 1:
                char_after = text_lower[end_index + 1]
                if char_after.isalnum() or char_after == '_':
                    continue
            
            # Valid word boundary match
            found_parts[client].add(name_part)
        
        # Check if any client has both 'first' and 'last' name parts found
        for client, parts in found_parts.items():
            if 'first' in parts and 'last' in parts:
                return client
    else:
        # Fallback to simple regex search if pyahocorasick is not installed
        for client in clients:
            first_pattern = fr'\b{re.escape(client.first.lower())}\b'
            last_pattern = fr'\b{re.escape(client.last.lower())}\b'
            if re.search(first_pattern, text_lower) and re.search(last_pattern, text_lower):
                return client
    return None

def get_unique_filepath(target_dir, filename):
    """Generates a unique filepath in the target directory to avoid collisions."""
    target_path = target_dir / filename
    if not target_path.exists():
        return target_path
    
    stem = target_path.stem
    suffix = target_path.suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_target_path = target_dir / new_name
        if not new_target_path.exists():
            return new_target_path
        counter += 1

def process_file(file_path, folder_map, automaton, clients, dest_path, do_move, dry_run):
    """
    Processes a single file, checking for client names and moving/copying it.
    Returns a status tuple: (status, source, destination).
    status can be 'FILENAME', 'CONTENT', 'NO_MATCH', 'ERROR'
    """
    match_type = None
    matched_client = None

    # 1. Check filename first
    filename_client = find_client_match(file_path.name, automaton, clients)
    if filename_client:
        matched_client = filename_client
        match_type = "FILENAME"
    else:
        # 2. Check content if not found by filename
        text = extract_text(file_path)
        if text:
            content_client = find_client_match(text, automaton, clients)
            if content_client:
                matched_client = content_client
                match_type = "CONTENT"

    if matched_client:
        folder_name = folder_map[matched_client]
        target_dir = dest_path / folder_name
        
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = get_unique_filepath(target_dir, file_path.name)
        else:
            target_path = target_dir / file_path.name # For display in dry run

        try:
            if not dry_run:
                action = shutil.move if do_move else shutil.copy
                action(file_path, target_path)
            
            logger.info(f"[{match_type}] {file_path.name} -> {folder_name}/{target_path.name}")
            return (match_type, file_path, target_path)
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {e}"
            logger.error(error_msg)
            failed_file_logger.error(error_msg)
            return ('ERROR', file_path, None)

    logger.info(f"[NO MATCH] {file_path.name}")
    return ('NO_MATCH', file_path, None)

def get_clients_from_user():
    """Prompts the user to enter client names."""
    clients = []
    client_set = set()
    print("\nEnter client names (First Middle(optional) Last), type 'done' when finished:")
    while True:
        line = input().strip()
        if line.lower() == 'done':
            break
        if not line:
            continue
        
        parts = line.split()
        client = None
        if len(parts) == 2:
            client = Client(parts[0].lower(), "", parts[1].lower())
        elif len(parts) == 3:
            client = Client(parts[0].lower(), parts[1].lower(), parts[2].lower())
        else:
            print("Invalid input format. Please use First Last or First Middle Last.", file=sys.stderr)
            continue

        if client in client_set:
            print(f"Client '{' '.join(filter(None, client))}' already exists. Skipping.", file=sys.stderr)
        else:
            clients.append(client)
            client_set.add(client)

    return clients

def generate_folder_names(clients):
    """Generates unique folder names from a list of clients."""
    folder_map = {}
    name_counts = Counter()
    for client in clients:
        base_name = get_base_folder_name(client)
        count = name_counts[base_name]
        name_counts[base_name] += 1
        
        folder_name = base_name
        if count > 0:
            folder_name = f"{base_name}_{count + 1}"
        folder_map[client] = folder_name
    return folder_map

def display_client_mapping(folder_map):
    """Prints the mapping from client to their designated folder."""
    logger.info("\nClient -> Folder mapping:")
    for client, folder_name in folder_map.items():
        full_name = f"{client.first} {client.middle} {client.last}" if client.middle else f"{client.first} {client.last}"
        print(f"  {full_name} -> {folder_name}")

def collect_files(src_path: Path):
    """
    Recursively collects all files with valid extensions from the source path.
    Works properly on Windows (handles long paths and hidden dirs safely).
    """
    files = []
    src_path = Path(src_path)

    # Ensure Windows paths are handled correctly (for long paths)
    if src_path.drive and not str(src_path).startswith("\\\\?\\"):
        src_path = Path(f"\\\\?\\{src_path}")

    for entry in src_path.rglob("*"):
        try:
            if entry.is_file() and has_valid_extension(entry):
                files.append(entry)
        except (PermissionError, OSError):
            # Skip directories or files we can’t access
            continue

    return files

def main():
    """Main function to run the file organizer."""
    parser = argparse.ArgumentParser(description="Lawyer File Organizer (Optimized)")
    parser.add_argument('--move', action='store_true', help="Move files instead of copying.")
    parser.add_argument('--workers', type=int, default=os.cpu_count() or 4, help="Number of parallel worker threads.")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be done without actually processing files.")
    args = parser.parse_args()

    logger.info("======================================")
    logger.info(" Lawyer File Organizer (Python, Optimized)")
    logger.info("======================================\n")

    if args.dry_run:
        logger.info("--- DRY RUN MODE: No files will be moved or copied. ---")

    # Get source and destination paths
    src_path_str = input("Enter source folder path: ")
    dest_path_str = input("Enter destination folder path: ")

    src_path = Path(src_path_str).resolve()
    dest_path = Path(dest_path_str).resolve()

    if not src_path.is_dir():
        logger.error(f"Error: Invalid source directory: {src_path}")
        sys.exit(1)

    try:
        dest_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Error: Cannot create destination directory: {dest_path}. Reason: {e}")
        sys.exit(1)

    # Get client information
    clients = get_clients_from_user()
    if not clients:
        logger.error("No clients provided. Exiting.")
        sys.exit(1)

    # Generate folder names and display mapping
    folder_map = generate_folder_names(clients)
    display_client_mapping(folder_map)

    # Build the search automaton for fast matching (if available)
    automaton = build_automaton(clients)

    # Collect files
    files = collect_files(src_path)
    if not files:
        logger.info("No valid files (.txt, .pdf, .docx) found in the source directory.")
        sys.exit(0)

    logger.info(f"\nFound {len(files)} files. Processing with up to {args.workers} workers...\n")

    # Process each file in parallel
    stats = Counter()
    
    # Use functools.partial to create a function with fixed arguments for the workers
    worker_func = functools.partial(process_file, 
                                    folder_map=folder_map, 
                                    automaton=automaton, 
                                    clients=clients, 
                                    dest_path=dest_path, 
                                    do_move=args.move,
                                    dry_run=args.dry_run)

    progress_bar = tqdm(total=len(files), desc="Processing Files", unit="file") if tqdm else None

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(worker_func, files):
            stats[result[0]] += 1
            if progress_bar:
                progress_bar.update(1)
    
    if progress_bar:
        progress_bar.close()

    logger.info("\n--- Processing Summary ---")
    logger.info(f"Total files scanned: {len(files)}")
    logger.info(f"Matches by Filename: {stats['FILENAME']}")
    logger.info(f"Matches by Content:  {stats['CONTENT']}")
    logger.info(f"No Match Found:      {stats['NO_MATCH']}")
    logger.info(f"Errors:              {stats['ERROR']}")
    if stats['ERROR'] > 0:
        logger.info("Details for failed files have been logged to failed_files.log")
    
    if not args.dry_run:
        logger.info("Files were MOVED." if args.move else "Files were COPIED.")
    logger.info("Done.")

if __name__ == "__main__":
    main()