import subprocess
import argparse
import dotenv
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender", required=True, help="Path to the Blender executable")
    return parser.parse_args()

def main():
    dotenv.load_dotenv()
    args = parse_args()

    print(f"BLENDER: {args.blender}")
    command = [
        args.blender,
        "-b", # background mode
        "--python", "render_images.py",
    ]
    
    print(f"Running command: {' '.join(command)}")  # For debugging purposes
    subprocess.run(command, check=True)

if __name__ == "__main__":
    main()
