import subprocess

# Define the scripts to run
scripts = ["scripts/chroma/chroma_del.py", "scripts/chroma/chroma_setup.py"]

# Run each script
for script in scripts:
    subprocess.run(["python", script])
