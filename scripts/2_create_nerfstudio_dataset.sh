#!/bin/bash

# Creates a Nerfstudio dataset from a folder in processed/.
#
# Usage:
#   ./create_nerfstudio_dataset.sh <dataset_name>
#
# Example:
#   ./create_nerfstudio_dataset.sh cestino_stoffa

set -e

DATASET_NAME="$1"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <dataset_name>"
    exit 1
fi

INPUT_DIR="project_data/processed/${DATASET_NAME}/images_png"
OUTPUT_DIR="project_data/nerfstudio_dataset/${DATASET_NAME}"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: input directory not found: $INPUT_DIR"
    exit 1
fi

ns-process-data images \
    --data "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR"

echo "Dataset created in $OUTPUT_DIR"