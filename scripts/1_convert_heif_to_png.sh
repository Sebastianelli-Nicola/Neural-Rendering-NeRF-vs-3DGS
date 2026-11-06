#!/bin/bash

# Converts all .heif images from an input directory to .png images
# and saves them into the specified output directory.
#
# Usage:
#   ./convert_heif_to_png.sh <input_directory> <output_directory>
#


set -e

INPUT_DIR="$1"
OUTPUT_DIR="$2"

if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_directory> <output_directory>"
    exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: input directory does not exist: $INPUT_DIR"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

for f in "$INPUT_DIR"/*.heif; do
    [ -e "$f" ] || continue

    filename=$(basename "$f" .heif)

    heif-convert \
        "$f" \
        "$OUTPUT_DIR/${filename}.png"
done

echo "Conversion completed."