#!/bin/bash
# Full AI content pipeline: stories (IT+EN) first, then cover images. Idempotent — safe to rerun.
cd /app/backend
echo "=== content $(date) ===" >> logs/pipeline.log
python3 generate_content.py --target 20 >> logs/pipeline.log 2>&1
echo "=== images $(date) ===" >> logs/pipeline.log
python3 generate_images.py --kind stories >> logs/pipeline.log 2>&1
echo "=== done $(date) ===" >> logs/pipeline.log
