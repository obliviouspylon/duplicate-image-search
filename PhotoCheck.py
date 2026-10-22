# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:31:13 2021

@author: james
"""

import sys
import os
import datetime
from PIL import Image
import imagehash

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".gif"}


def find_duplicates(target_dir, hash_size=16, threshold=0, progress_callback=None):
    """
    Scan a directory for duplicate or perceptually similar images.

    Returns:
        clusters: list of lists, where each list is [hash_str, file1, file2, ...]
    """
    target_dir = os.path.abspath(target_dir)
    if not os.path.isdir(target_dir):
        raise ValueError(f"Directory not found: {target_dir}")

    # Collect all image files
    image_paths = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                image_paths.append(os.path.join(root, file))

    total = len(image_paths)
    seen_hashes = {}  # hash_obj: [file_paths]

    for index, path in enumerate(image_paths):
        if progress_callback:
            progress_callback(index + 1, total, path)

        try:
            with Image.open(path) as img:
                current_hash = imagehash.phash(img, hash_size=hash_size)
        except Exception as err:
            # Skip invalid, unreadable, or corrupted image files
            print(f"Skipping {path}: {err}", file=sys.stderr)
            continue

        matched_hash = None
        if threshold == 0:
            # Fast exact hash lookup
            if current_hash in seen_hashes:
                matched_hash = current_hash
        else:
            # Perceptual Hamming distance lookup
            for existing_hash in seen_hashes:
                if (current_hash - existing_hash) <= threshold:
                    matched_hash = existing_hash
                    break

        if matched_hash is not None:
            seen_hashes[matched_hash].append(path)
        else:
            seen_hashes[current_hash] = [path]

    # Filter to groups with at least 2 images
    clusters = []
    for h, files in seen_hashes.items():
        if len(files) > 1:
            clusters.append(['#' + str(h)] + files)

    return clusters


def main(argv):
    clusters = find_duplicates(argv, hash_size=16, threshold=0)
    return clusters


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <folder_path>")
        sys.exit(1)

    target_folder = sys.argv[1]
    duplicates = main(target_folder)

    if not duplicates:
        print("No Duplicate/Similar Photos Found")
    else:
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        file_path = os.path.join(script_dir, f"PhotoDuplicates_{date}.txt")

        with open(file_path, "w", encoding="utf-8") as output:
            for cluster in duplicates:
                output.write(f"{cluster[0]}\n")
                for filepath in cluster[1:]:
                    output.write(f"\t{filepath}\n")

        print(f"{os.path.basename(sys.argv[0])} Done")
        print(f"Duplicate/Similar Photos Found. Report saved to:\n  {file_path}")

