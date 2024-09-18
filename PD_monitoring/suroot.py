import subprocess


try:
    subprocess.run(['su'], check=True)

except subprocess.CalledProcessError as e:
    print(f"An error occurred while executing {command}: {e}")