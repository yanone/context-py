#!/bin/bash
# Build a Python wheel compatible with Pyodide
# Uses build ~=1.2.0 for compatibility with pyodide-build 0.25.1

set -e

echo "Rebuilding docs..."
python makedoc.py

echo "Building context-py wheel for Pyodide..."

# Ensure we have the correct build version
pip install 'build~=1.2.0'

# Build the wheel
python -m build --wheel

# Get the most recent wheel file
WHEEL_FILE=$(ls -t dist/*.whl | head -1)
WHEEL_NAME=$(basename "$WHEEL_FILE")

# Copy to font editor with proper wheel name
DEST_DIR="../context-font-editor/webapp/wheels"
DEST_FILE="$DEST_DIR/$WHEEL_NAME"

echo ""
echo "Cleaning old wheels from font editor..."
mkdir -p "$DEST_DIR"
# Remove any existing contextfonteditor wheels
rm -f "$DEST_DIR"/contextfonteditor-*.whl
echo "Old wheels removed"

echo ""
echo "Copying wheel to font editor..."
cp "$WHEEL_FILE" "$DEST_FILE"

echo ""
echo "Creating wheels manifest..."
# Create a JSON manifest of wheel files for GitHub Pages
cat > "$DEST_DIR/wheels.json" << EOF
{
  "wheels": [
    "$WHEEL_NAME"
  ]
}
EOF
echo "Manifest created: $DEST_DIR/wheels.json"

echo ""
echo "Wheel built successfully!"
echo "Source: $WHEEL_FILE"
echo "Destination: $DEST_FILE"
ls -lh "$DEST_FILE"
