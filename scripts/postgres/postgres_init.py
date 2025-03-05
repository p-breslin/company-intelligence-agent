import subprocess

# Define the scripts to run
scripts = ["scripts/postgres/postgres_del.py", "scripts/postgres/postgres_setup.py"]

# Run each script
for script in scripts:
    subprocess.run(["python", script])
