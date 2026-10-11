import os

# Windows without Developer Mode can't create symlinks in the Hugging Face
# cache. huggingface_hub falls back to copying files and warns each time;
# this only silences that warning (symlinks stay unavailable). It must be
# set before huggingface_hub is first imported.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
