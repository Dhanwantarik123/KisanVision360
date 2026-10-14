import os
from PIL import Image
from pathlib import Path
import shutil

# ============================================================
# PATHS - CHANGE ONLY DATASET_PATH IF REQUIRED
# ============================================================

DATASET_PATH = r"D:\KisanVision360\dataset"
OUTPUT_PATH = r"D:\KisanVision360\dataset_clean"

# Maximum allowed original image dimension
MAX_SIZE = 1600

# Minimum allowed dimension
MIN_SIZE = 50

# Supported image formats
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ============================================================

dataset = Path(DATASET_PATH)
output = Path(OUTPUT_PATH)

if not dataset.exists():
    print("ERROR: Dataset folder not found:")
    print(dataset)
    exit()

output.mkdir(parents=True, exist_ok=True)

total = 0
copied = 0
bad = 0
large = 0
small = 0
unsupported = 0

print("=" * 70)
print("DATASET FILTERING")
print("=" * 70)
print("Original :", dataset)
print("Clean    :", output)
print()

# Go through class folders
for class_folder in dataset.iterdir():

    if not class_folder.is_dir():
        continue

    class_name = class_folder.name
    output_class = output / class_name
    output_class.mkdir(parents=True, exist_ok=True)

    print(f"\nClass: {class_name}")

    for image_path in class_folder.rglob("*"):

        if not image_path.is_file():
            continue

        total += 1

        # Check extension
        if image_path.suffix.lower() not in VALID_EXTENSIONS:
            unsupported += 1
            continue

        try:
            # Open image
            with Image.open(image_path) as img:

                # Verify image
                img.verify()

            # Open again after verify
            with Image.open(image_path) as img:

                width, height = img.size

                # Reject extremely small images
                if width < MIN_SIZE or height < MIN_SIZE:
                    small += 1
                    continue

                # Reject extremely large images
                if width > MAX_SIZE or height > MAX_SIZE:
                    large += 1
                    continue

            # Copy valid image
            destination = output_class / image_path.name

            # Avoid duplicate filename
            if destination.exists():
                stem = image_path.stem
                suffix = image_path.suffix

                counter = 1

                while destination.exists():
                    destination = output_class / f"{stem}_{counter}{suffix}"
                    counter += 1

            shutil.copy2(image_path, destination)

            copied += 1

        except Exception as e:
            bad += 1

        # Progress
        if total % 1000 == 0:
            print(
                f"Processed: {total} | "
                f"Copied: {copied} | "
                f"Bad: {bad} | "
                f"Large: {large}"
            )

# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("FILTERING COMPLETE")
print("=" * 70)

print(f"Total files       : {total}")
print(f"Valid images      : {copied}")
print(f"Corrupt images    : {bad}")
print(f"Large images      : {large}")
print(f"Small images      : {small}")
print(f"Unsupported files : {unsupported}")

print()
print("Clean dataset:")
print(output)
print("=" * 70)
