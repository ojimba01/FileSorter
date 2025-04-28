#!/usr/bin/env python3

import os
import re
import argparse
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

UNDO_LOG_PATH = "undo_log.txt"

def parse_args():
    """
    Parse command-line arguments provided by the user.

    Returns:
        argparse.Namespace: Parsed arguments including directory, action, regex, replace string, dry-run, undo, or natural instruction.
    """

    parser = argparse.ArgumentParser(description="FileSorter: Organize files using regex and file metadata.")
    parser.add_argument("--directory", "-d", help="Target directory to process")
    parser.add_argument("--action", "-a", choices=["sort", "rename", "move"], help="Action to perform on files")
    parser.add_argument("--regex", "-r", help="Regex pattern to match filenames")
    parser.add_argument("--replace", "-p", help="Replacement string for regex rename/move")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    parser.add_argument("--undo", action="store_true", help="Undo the last action")
    parser.add_argument("--natural", help="Natural language instruction to be interpreted by OpenAI")
    parser.add_argument("--auto-suggest", action="store_true", help="Use GPT to suggest how to organize the directory")
    return parser.parse_args()

def analyze_directory(directory):
    """
    Analyze a directory to extract metadata from filenames, including extensions and optional date patterns.

    Args:
        directory (str): The path to the target directory.

    Returns:
        defaultdict: A dictionary containing lists of file extensions and extracted dates (if found).
    """

    file_data = defaultdict(list)
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            extension = filename.split('.')[-1] if '.' in filename else 'no_extension'
            file_data["extension"].append((filename, extension))

            # Try to get date from filename first
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
            if date_match:
                year = date_match.group(1)
            else:
                # Fall back to file's last modified timestamp
                mod_time = os.path.getmtime(filepath)
                year = datetime.fromtimestamp(mod_time).strftime("%Y")

            file_data["dates"].append((filename, year))
    return file_data

def provide_suggestions(file_data):
    """
    Generate organization suggestions based on the analyzed file metadata.

    Args:
        file_data (defaultdict): The collected file extensions and dates.

    Returns:
        list: A list of suggestion dictionaries for organizing files.
    """

    suggestions = []
    ext_set = set(ext for _, ext in file_data['extension'])
    for ext in ext_set:
        suggestions.append({"type": "extension", "extension": ext, "description": f"Move all .{ext} files into '{ext}/'"})
    if file_data.get('dates'):
        suggestions.append({"type": "year", "description": "Group files into folders based on year in filename"})
    return suggestions

def prompt_user_for_reorganization(suggestions, directory, file_data):
    """
    Prompt the user with suggested file organization options and execute the chosen operation.

    Args:
        suggestions (list): List of reorganization suggestions.
        directory (str): The path to the directory.
        file_data (defaultdict): Metadata extracted from filenames.
    """

    print("\nHere are some suggestions to reorganize your directory:")
    for idx, suggestion in enumerate(suggestions, 1):
        print(f"{idx}. {suggestion['description']}")
    print(f"{len(suggestions)+1}. Undo last action")

    try:
        choice = int(input("Choose an option (number) or 0 to skip: "))
    except ValueError:
        print("Invalid input.")
        return

    if choice == 0:
        print("No changes made.")
    elif choice == len(suggestions) + 1:
        undo_last_action()
    else:
        selected = suggestions[choice - 1]
        if selected['type'] == 'extension':
            move_by_extension(directory, selected['extension'], file_data['extension'])
        elif selected['type'] == 'year':
            group_by_year(directory, file_data['dates'])

def move_by_extension(directory, target_ext, extension_data, dry_run=False):
    """
    Move files with a specific extension into a subfolder named after the extension.

    Args:
        directory (str): The path to the target directory.
        target_ext (str): The file extension to group by.
        extension_data (list): List of (filename, extension) tuples.
        dry_run (bool): If True, preview actions without applying changes.
    """

    target_dir = os.path.join(directory, target_ext)
    if not dry_run:
        os.makedirs(target_dir, exist_ok=True)
    for filename, ext in extension_data:
        if ext == target_ext:
            old = os.path.join(directory, filename)
            new = os.path.join(target_dir, filename)
            if dry_run:
                print(f"Would move: {old} -> {new}")
            else:
                os.rename(old, new)
                log_move(old, new)
                print(f"Moved: {old} -> {new}")

def group_by_year(directory, date_data, dry_run=False):
    """
    Move files into subfolders based on the year extracted from their filenames.

    Args:
        directory (str): The target directory path.
        date_data (list): List of (filename, year) tuples.
        dry_run (bool): If True, preview actions without applying changes.
    """

    for filename, year in date_data:
        year_dir = os.path.join(directory, year)
        old = os.path.join(directory, filename)
        new = os.path.join(year_dir, filename)
        if dry_run:
            print(f"Would move: {old} -> {new}")
        else:
            os.makedirs(year_dir, exist_ok=True)
            os.rename(old, new)
            log_move(old, new)
            print(f"Moved: {old} -> {new}")
    if not dry_run:
        print("Files grouped by year.")

def rename_files(directory, regex, replace, dry_run=False):
    """
    Rename files matching a regex pattern, replacing matched parts according to user input.

    Args:
        directory (str): The target directory.
        regex (str): The regex pattern to search in filenames.
        replace (str): Replacement string or pattern.
        dry_run (bool): If True, preview actions without applying changes.
    """

    for filename in os.listdir(directory):
        if re.search(regex, filename):
            new_name = re.sub(regex, replace, filename)
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_name)
            if dry_run:
                print(f"Would rename: {old_path} -> {new_path}")
            else:
                os.rename(old_path, new_path)
                log_move(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")

def move_files_by_regex(directory, regex, folder, dry_run=False):
    """
    Move files matching a regex pattern into a specific target folder.

    Args:
        directory (str): Path to the directory.
        regex (str): Regex pattern to match files.
        folder (str): Destination folder name.
        dry_run (bool): If True, preview actions without applying changes.
    """

    target_dir = os.path.join(directory, folder)
    if not dry_run:
        os.makedirs(target_dir, exist_ok=True)
    for filename in os.listdir(directory):
        if re.search(regex, filename):
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(target_dir, filename)
            if dry_run:
                print(f"Would move: {old_path} -> {new_path}")
            else:
                os.rename(old_path, new_path)
                log_move(old_path, new_path)
                print(f"Moved: {old_path} -> {new_path}")

def log_move(old_path, new_path):
    """
    Log a file move action to enable undo functionality.

    Args:
        old_path (str): Original file path before moving.
        new_path (str): New file path after moving.
    """

    with open(UNDO_LOG_PATH, "a") as log:
        log.write(f"{new_path} -> {old_path}\n")

def undo_last_action():
    """
    Undo all file moves recorded in the undo log.
    Restores files to their original locations and deletes any now-empty folders.
    """

    if not os.path.exists(UNDO_LOG_PATH):
        print("No undo history found.")
        return
    moved_dirs = set()
    with open(UNDO_LOG_PATH, "r") as log:
        moves = [line.strip().split(" -> ") for line in log if "->" in line]
    for src, dst in moves:
        moved_dirs.add(os.path.dirname(src))
        if os.path.exists(src):
            os.rename(src, dst)
            print(f"Moved back: {src} -> {dst}")
    for dir_path in moved_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
            print(f"Removed empty folder: {dir_path}")
    os.remove(UNDO_LOG_PATH)
    print("Undo complete.")

def summarize_directory(directory):
    """
    Generate a simple summary list of files in a given directory.

    Args:
        directory (str): The path to the directory to summarize.

    Returns:
        str: A formatted string listing all files, or an error message if the directory cannot be read.
    """
    try:
        files = os.listdir(directory)
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
        return "\n".join(f"- {f}" for f in files)
    except Exception as e:
        return f"(Could not read directory: {e})"

examples = r"""
# Move all .txt files into a 'work' folder
filesorter --directory /home/user/files --action move --regex "\.txt$" --replace "work"

# Move all PDF files into a 'docs' folder
filesorter --directory /home/user/files --action move --regex "\.pdf$" --replace "docs"

# Move all image files into 'images'
filesorter --directory /home/user/files --action move --regex "\.(jpg|jpeg|png)$" --replace "images"

# Rename IMG_1234.jpg to photo_1234.jpg
filesorter --directory /home/user/files --action rename --regex "IMG_(\d+)" --replace "photo_\g<1>"

# Rename files with spaces to use underscores
filesorter --directory /home/user/files --action rename --regex " " --replace "_"

# Group files by year found in filename (e.g., 2022-11-01_report.pdf)
filesorter --directory /home/user/files --action sort

# Preview a rename operation
filesorter --directory /home/user/files --action rename --regex "draft" --replace "final" --dry-run

# Move log files with "error" in name to 'logs/error'
filesorter --directory /home/user/files --action move --regex "error.*\.log$" --replace "logs/error"

# Rename versioned files like file_v1.txt to file_version1.txt
filesorter --directory /home/user/files --action rename --regex "_v(\d+)" --replace "_version\g<1>"

# Move all CSV files into a 'data' folder
filesorter --directory /home/user/files --action move --regex "\.csv$" --replace "data"

# Undo the last operation
filesorter --undo

# Automatically analyze and suggest sorting actions
filesorter --directory /home/user/files --action sort

# Rename camera files like DSC001.jpg to trip_001.jpg
filesorter --directory /home/user/photos --action rename --regex "DSC(\d+)" --replace "trip_\g<1>"

# Move invoices with date in filename into a folder named by year
filesorter --directory /home/user/invoices --action sort

# Natural prompt: Group all JPGs into a folder called 'photos'
filesorter --directory /home/user/photos --natural "Move all JPGs into a folder called photos"

# Natural prompt: Rename all log files to start with 'log_'
filesorter --directory /home/user/logs --natural "Rename all .log files to start with 'log_'"

# Natural prompt: Organize my files by type and year
filesorter --directory /home/user/messy --natural "Organize all files by extension and group by year"
"""



def interpret_natural_command_with_gpt(natural_prompt, directory="test_dir"):
    """
    Use OpenAI's GPT model to interpret a natural language instruction
    and generate corresponding CLI commands for file organization.

    Args:
        natural_prompt (str): The user's natural language instruction.
        directory (str): The working directory to be referenced in the commands.

    Returns:
        list: List of command-line suggestions generated by the model.
    """

    client = OpenAI()
    file_summary = summarize_directory(directory)

    prompt = f"""
    You are generating CLI commands using ONLY the 'filesorter' tool.
    DO NOT use bash, mv, mkdir, or shell commands.

    DO NOT use '--action sort' unless the user specifically asks for suggestions interactively.
    Instead, generate individual 'filesorter' CLI commands using '--action move', '--action rename', '--regex', '--replace', etc.

    Here are some valid example commands:
    {examples}

    Current working directory: {directory}

    Files in this directory:
    {file_summary}

    The user asked:
    {natural_prompt}

    Your task:
    Generate one or more CLI commands that perform exactly what the user asked using specific 'filesorter' operations.
    Return one command per line. Each should begin with 'filesorter' and include flags like '--action move' or '--action rename'.
    Avoid using '--action sort'. Do not echo the user's prompt or include explanations.
    """


    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You convert file organization instructions into command-line commands for a CLI tool."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )

    return response.choices[0].message.content.strip().splitlines()

def generate_ai_organization_suggestions(directory="test_dir"):
    """
    Use OpenAI GPT to generate smart file organization ideas based on the structure of a directory.

    Args:
        directory (str, optional): Path to the directory to analyze. Defaults to "test_dir".

    Returns:
        list: A list of plain English suggestions for how to reorganize the directory contents.
    """
    client = OpenAI()

    try:
        items = os.listdir(directory)
        files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
        folders = [f for f in items if os.path.isdir(os.path.join(directory, f))]
    except Exception as e:
        return [f"(Error reading directory: {e})"]

    file_list = "\n".join(f"- {f}" for f in files)
    folder_list = "\n".join(f"- {f}/" for f in folders)

    prompt = f"""
You are a file organization assistant.

The following directory contains:
Folders:
{folder_list or 'None'}

Files:
{file_list or 'None'}

Based on this structure, what are some smart ways the user could reorganize the contents of this directory?
Provide simple, clear suggestions like "Move all PDFs to a 'pdfs' folder", "Group files by year", etc.
Just give helpful ideas, not CLI commands.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You suggest how to organize files and folders in a directory."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content.strip().splitlines()


def main():
    args = parse_args()

    if args.natural:
        suggestions = interpret_natural_command_with_gpt(args.natural, args.directory or "test_dir")
        print("🧠 GPT Suggestions:")
        for cmd in suggestions:
            print("✨", cmd)
        return

    if args.undo:
        undo_last_action()
        return

    directory = args.directory
    if not directory or not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    if args.action == "rename":
        if not args.regex or not args.replace:
            print("Both --regex and --replace are required for renaming.")
            return
        rename_files(directory, args.regex, args.replace, dry_run=args.dry_run)

    elif args.action == "move":
        if not args.regex or not args.replace:
            print("Both --regex and --replace are required for moving.")
            return
        move_files_by_regex(directory, args.regex, args.replace, dry_run=args.dry_run)

    elif args.auto_suggest:
        suggestions = generate_ai_organization_suggestions(args.directory or "test_dir")
        print("🧠 AI-Powered Suggestions:")
        for line in suggestions:
            print("💡", line)
        return


    elif args.action == "sort":
        file_data = analyze_directory(directory)
        suggestions = provide_suggestions(file_data)
        if suggestions:
            prompt_user_for_reorganization(suggestions, directory, file_data)
        else:
            print("No actionable patterns found.")


if __name__ == "__main__":
    main()
