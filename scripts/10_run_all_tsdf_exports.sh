#!/usr/bin/env bash
set -e

# Set this to the absolute path of your project_data directory before running.
BASE_DIR="/path/to/your/computer_graphics_project/project_data"

OUTPUTS_DIR="$BASE_DIR/outputs"
EXPORTS_DIR="$BASE_DIR/exports"
FAILED_LOG="$EXPORTS_DIR/failed_tsdf_exports.txt"

mkdir -p "$EXPORTS_DIR"

cd "$BASE_DIR"

# Reset failed log for this run
: > "$FAILED_LOG"

find "$OUTPUTS_DIR" -name "config.yml" | sort | while read -r CONFIG; do
    EXP_NAME=$(echo "$CONFIG" | sed "s|$OUTPUTS_DIR/||" | cut -d "/" -f 1)
    OUT_DIR="$EXPORTS_DIR/${EXP_NAME}_tsdf"

    if [ -d "$OUT_DIR" ]; then
        echo "Skipping existing export: $OUT_DIR"
        continue
    fi

    CKPT_DIR="$(dirname "$CONFIG")/nerfstudio_models"

    if [ ! -d "$CKPT_DIR" ]; then
        echo "Skipping experiment without checkpoint: $EXP_NAME"
        echo "$EXP_NAME | missing checkpoint dir | $CONFIG" >> "$FAILED_LOG"
        continue
    fi

    if ! ls "$CKPT_DIR"/*.ckpt >/dev/null 2>&1; then
        echo "Skipping experiment without .ckpt file: $EXP_NAME"
        echo "$EXP_NAME | missing ckpt file | $CONFIG" >> "$FAILED_LOG"
        continue
    fi

    echo "Running TSDF export:"
    echo "  experiment: $EXP_NAME"
    echo "  config:     $CONFIG"
    echo "  output:     $OUT_DIR"

    if ns-export tsdf \
      --load-config "$CONFIG" \
      --output-dir "$OUT_DIR"; then
        echo "Done: $EXP_NAME"
    else
        echo "FAILED: $EXP_NAME"
        echo "$EXP_NAME | export failed | $CONFIG" >> "$FAILED_LOG"
        rm -rf "$OUT_DIR"
    fi

    echo
done

echo "All TSDF exports completed!"

if [ -s "$FAILED_LOG" ]; then
    echo "Some exports failed. See:"
    echo "  $FAILED_LOG"
else
    echo "No failed exports."
fi