source .venv/bin/activate 

read -rp "Enter audio file name: " AUDIO_FILE
if [ -z "$AUDIO_FILE" ]; then
    echo "No audio file specified." >&2
    exit 1
fi
if [ ! -f "$AUDIO_FILE" ] && [ -f "audio/$AUDIO_FILE" ]; then
    AUDIO_FILE="audio/$AUDIO_FILE"
fi
export AUDIO_FILE

python3 src/split_audio.py "$AUDIO_FILE" --target-mb 25 --safety-margin-kb 0