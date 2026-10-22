# PhotoCheck

Perceptual duplicate photo detector and cleanup utility for Windows.

Scans directories for duplicate and visually similar photos using perceptual hashing (pHash). Includes a command-line script for batch reporting and a desktop interface for side-by-side photo review and cleanup.

## Requirements

- Python 3.13 or newer with Tkinter included
- Required Python libraries listed in `requirements.txt`:
  - `Pillow`
  - `ImageHash`

Install dependencies with pip:

```bash
pip install -r requirements.txt
```

## Running the graphical interface

Launch the desktop interface:

```bash
python PhotoCheck_UI.py
```

The application detects your Windows system theme (Dark or Light) on startup and adjusts the window, cards, and title bar. Use the "Mode: Dark / Light" button in the top right to switch themes on the fly.

### Review workflow

1. Select a directory in the target folder field or click Browse.
2. Select a similarity threshold:
   - `0`: Exact perceptual hash match. Catches true duplicates, re-saved files, and minor format changes.
   - `2` to `8`: Hamming distance threshold. Catches photos with small edits, slight cropping, or color changes.
3. Check "Confirm before deleting" if you want an explicit prompt before files are removed.
4. Click "Scan for Duplicates".
5. When duplicates are found, the tool displays matching photos side by side with resolution, file size, and modification date.
6. Choose an action for each duplicate pair:
   - **Keep Left, Delete Right** (Key: `A` or Left Arrow)
   - **Keep Right, Delete Left** (Key: `D` or Right Arrow)
   - **Keep Both** (Key: `K` or Down Arrow)
   - **Delete Both** (Key: `Delete`)

### Handling groups of three or more duplicates

When three or more duplicates share a hash, the interface steps through them pairwise against the first photo in the group. Deleting or keeping an image immediately updates the pair comparison until the entire cluster is resolved.

## Running the command-line script

Run the scanner directly in headless mode:

```bash
python PhotoCheck.py "C:\path\to\your\photos"
```

The script prints duplicate clusters to the terminal and writes a timestamped report file named `PhotoDuplicates_YYYY-MM-DD_HH.MM.SS.txt` in the script directory.

## File overview

- `PhotoCheck.py`: Core duplicate detection engine using `os.walk` and `imagehash.phash`. Callable from Python or CLI.
- `PhotoCheck_UI.py`: Desktop graphical interface built with Tkinter, ttk, and Pillow.
- `requirements.txt`: Python package requirements.
