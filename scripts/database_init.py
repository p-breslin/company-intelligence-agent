import subprocess

# Define the scripts to run
scripts = [
    "scripts/postgres/postgres_clear.py",
    "scripts/postgres/postgres_setup.py",
    "scripts/weaviate/weaviate_clear.py",
]

# Run each script
for script in scripts:
    subprocess.run(["python", script])
