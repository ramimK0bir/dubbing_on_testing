import argparse
import asyncio
import os
import sys

# Add the src structure to path if needed, though running as python project_dubbing/main.py might need partial fixes
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.dubber import DubbingEngine

def main():
    parser = argparse.ArgumentParser(description="Local Dubbing Tool")
    parser.add_argument("--input", "-i", required=True, help="Input video file path")
    parser.add_argument("--lang", "-l", default="es", help="Target language code (default: es)")
    parser.add_argument("--output", "-o", help="Output video file path")
    
    args = parser.parse_args()
    
    input_file = args.input
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    output_file = args.output
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_dubbed_{args.lang}{ext}"

    print(f"Input: {input_file}")
    print(f"Target Language: {args.lang}")
    print(f"Output: {output_file}")
    
    dubber = DubbingEngine()
    
    try:
        asyncio.run(dubber.process_video(input_file, args.lang, output_file))
    except KeyboardInterrupt:
        print("\nProcess interrupted.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
