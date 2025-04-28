# FileSorter: Smart CLI File Organizer

---

## 📂 Overview
FileSorter is a command-line tool that automates the process of organizing files in a directory. It can:
- Sort files based on extensions or dates
- Move or rename files using regex patterns
- Perform dry-run previews before applying changes
- Undo any operations performed
- Understand natural language instructions via OpenAI GPT-4 integration

---

## ✨ Key Features
- **Regex Matching**: Match filenames flexibly using regular expressions.
- **AI-Powered**: Describe tasks in plain English; FileSorter translates them into commands.
- **Dry-Run Mode**: Preview changes safely.
- **Undo Capability**: Reverse the last file operations.
- **Interactive Sorting**: Get organization suggestions based on file metadata.

---

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

If you are using natural language mode:
```bash
pip install openai python-dotenv
```

Also, set your OpenAI API key:
```bash
# Create a .env file
OPENAI_API_KEY=your-openai-api-key-here
```

---

## 🔄 Usage

### 1. Sort Files by Extension or Date
```bash
python filesorter.py --directory ./path/to/dir --action sort
```

### 2. Rename Files with Regex
```bash
python filesorter.py --directory ./path/to/dir --action rename --regex "report" --replace "summary"
```

### 3. Move Files Based on Regex Match
```bash
python filesorter.py --directory ./path/to/dir --action move --regex "\.(jpg|png)$" --replace images
```

### 4. Perform a Dry-Run (Preview)
```bash
python filesorter.py --directory ./path/to/dir --action move --regex "\.pdf$" --replace documents --dry-run
```

### 5. Undo the Last Operation
```bash
python filesorter.py --undo
```

### 6. Natural Language Command (Requires OpenAI Key)
```bash
python filesorter.py --directory ./path/to/dir --natural "Move all images to a folder called 'photos' and rename invoices to 'invoice_2024'"
```

---

## 🌐 Technologies Used
- Python 3.10+
- `os`, `shutil`, `re`, `argparse`
- OpenAI GPT-4 API (optional)
- dotenv for environment variable management

---

## 💪 Inspiration
Manual file organization is time-consuming and error-prone. FileSorter aims to empower users with automation and simple tools, enhanced by natural language understanding.

---

## 🛠️ License
MIT License

---

## 🚀 Future Improvements
- Full batch undo history
- Customizable sorting templates
- Integration with local LLMs (e.g., Ollama, LM Studio)
- File content-based classification (optional)

---

Happy Sorting! 📂✨
