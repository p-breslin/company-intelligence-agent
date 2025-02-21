import subprocess

# Define the scripts to run
scripts = [
    "scripts/postgres_clear.py",
    "scripts/postgres_setup.py",
    "scripts/chroma_clear.py",
    "scripts/chroma_setup.py",
]

# Run each script
for script in scripts:
    subprocess.run(["python", script])
