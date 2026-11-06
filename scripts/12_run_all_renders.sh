#!/usr/bin/env bash

# Set this to the absolute path of your project_data directory before running.
BASE_DIR="/path/to/your/computer_graphics_project/project_data"

OUTPUTS_DIR="$BASE_DIR/outputs"
RENDERS_DIR="$BASE_DIR/renders"

mkdir -p "$RENDERS_DIR"

cd "$BASE_DIR"

find "$OUTPUTS_DIR" -name "config.yml" | sort | while read -r CONFIG; do
    EXP_NAME=$(echo "$CONFIG" | sed "s|$OUTPUTS_DIR/||" | cut -d "/" -f 1)
    OUT_DIR="$RENDERS_DIR/$EXP_NAME"

    if [ -d "$OUT_DIR" ]; then
        echo "Skipping existing render folder: $OUT_DIR"
        continue
    fi

    echo "Running render:"
    echo "  experiment: $EXP_NAME"
    echo "  config:     $CONFIG"
    echo "  output:     $OUT_DIR"

    if ns-render dataset \
        --load-config "$CONFIG" \
        --output-path "$OUT_DIR" \
        --image-format png \
        --rendered-output-names rgb gt-rgb \
        --split test; then

        echo "Done: $EXP_NAME"
    else
        echo "ERROR during render: $EXP_NAME"
        echo "Continuing with next experiment..."
    fi

    echo
done

echo "All possible renders completed!"