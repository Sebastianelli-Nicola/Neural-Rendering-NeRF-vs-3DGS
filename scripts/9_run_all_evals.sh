#!/usr/bin/env bash
set -e

# Set this to the absolute path of your project_data directory before running.
BASE_DIR="/path/to/your/computer_graphics_project/project_data"

OUTPUTS_DIR="$BASE_DIR/outputs"
EVALS_DIR="$BASE_DIR/evals"

cd "$BASE_DIR"

find "$OUTPUTS_DIR" -name "config.yml" | sort | while read -r CONFIG; do
    EXP_NAME=$(echo "$CONFIG" | sed "s|$OUTPUTS_DIR/||" | cut -d "/" -f 1)
    OUT_JSON="$EVALS_DIR/${EXP_NAME}_eval.json"

    if [ -f "$OUT_JSON" ]; then
        echo "Skipping existing eval: $OUT_JSON"
        continue
    fi

    echo "Running eval:"
    echo "  experiment: $EXP_NAME"
    echo "  config:     $CONFIG"
    echo "  output:     $OUT_JSON"

    ns-eval \
      --load-config "$CONFIG" \
      --output-path "$OUT_JSON"

    echo "Done: $EXP_NAME"
    echo
done

echo "All evaluations completed!"
