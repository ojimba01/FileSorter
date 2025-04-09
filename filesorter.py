import os
import re
from collections import defaultdict

# Function to analyze the directory and gather file information
def analyze_directory(directory):
    # Use defaultdict to automatically create lists for keys like 'extension', 'filenames', and 'dates'
    file_data = defaultdict(list)
    
    # Loop through every file in the given directory
    for filename in os.listdir(directory):
        # Check if the item is a file (ignore directories)
        if os.path.isfile(os.path.join(directory, filename)):
            # Extract file extension (e.g., "txt" from "document.txt"), or label as 'no_extension' if missing
            extension = filename.split('.')[-1] if '.' in filename else 'no_extension'
            
            # Try to extract a date from the filename (YYYY-MM-DD format)
            date_pattern = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
            date_info = date_pattern.group(0) if date_pattern else None
            
            # Save gathered info into the corresponding lists
            file_data['extension'].append(extension)
            file_data['filenames'].append(filename)
            if date_info:
                file_data['dates'].append(date_info)
    
    return file_data

# Function to generate organization suggestions based on the analyzed data
def provide_suggestions(file_data):
    suggestions = []
    
    # Suggest grouping files by extension
    extensions = set(file_data['extension'])  # Use a set to avoid duplicates
    for ext in extensions:
        suggestions.append(f"Move all files with the `. {ext}` extension to a folder called `{ext}`.")
    
    # Suggest grouping files by year if date patterns were found
    if file_data.get('dates'):
        suggestions.append("Group files by year based on the date in filenames (e.g., `2025` folder).")
    
    return suggestions

# Function to interact with the user and let them choose how to reorganize their files
def prompt_user_for_reorganization(suggestions, directory):
    print("Here are some suggestions to reorganize your directory:")
    
    # Display each suggestion with a numbered list
    for idx, suggestion in enumerate(suggestions, 1):
        print(f"{idx}. {suggestion}")
    
    # Ask the user to choose an option
    choice = int(input("Choose an option (1-3) or 0 to skip: "))
    
    # Exit if user chooses to skip
    if choice == 0:
        print("No reorganization selected.")
    else:
        selected_suggestion = suggestions[choice - 1]
        
        # Based on the suggestion, perform the appropriate file operation
        if 'extension' in selected_suggestion:
            ext = selected_suggestion.split('`')[1]  # Extract the extension from the suggestion text
            move_files_based_on_extension(directory, ext)
        elif 'date' in selected_suggestion:
            group_files_by_date(directory)

# Function to move files into a subdirectory based on their extension
def move_files_based_on_extension(directory, ext):
    target_directory = os.path.join(directory, ext)  # Subfolder named after the extension
    
    # Create the subfolder if it doesn't exist
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    
    # Move each matching file to the new subfolder
    for filename in os.listdir(directory):
        if filename.endswith(f".{ext}"):
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(target_directory, filename)
            os.rename(old_path, new_path)
    print(f"Moved all `. {ext}` files to `{ext}` folder.")

# Function to group files by year extracted from a date pattern in the filename
def group_files_by_date(directory):
    for filename in os.listdir(directory):
        # Look for a date in the filename
        date_pattern = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if date_pattern:
            year = date_pattern.group(1)  # Extract the year part
            target_directory = os.path.join(directory, year)  # Subfolder for the year
            
            # Create the year subfolder if it doesn't exist
            if not os.path.exists(target_directory):
                os.makedirs(target_directory)
            
            # Move the file into the year folder
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(target_directory, filename)
            os.rename(old_path, new_path)
    print("Files organized by year.")

# Main entry point of the program
def main():
    # Ask the user for the directory they want to analyze
    directory = input("Enter the path of the directory to analyze: ")
    
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"The directory '{directory}' does not exist!")
        return

    # Step 1: Analyze the directory
    file_data = analyze_directory(directory)
    
    # Step 2: Generate suggestions
    suggestions = provide_suggestions(file_data)
    
    # Step 3: If suggestions exist, prompt user; otherwise, notify
    if suggestions:
        prompt_user_for_reorganization(suggestions, directory)
    else:
        print("No recognizable patterns found in the directory.")

# This ensures the main function only runs when this file is executed directly
if __name__ == "__main__":
    main()
