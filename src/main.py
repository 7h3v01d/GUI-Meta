# main.py - Console entry point for the torrent metadata extractor

import sys
import os
import traceback

# Import the decoding function from torinfo.py
from torinfo import get_torrent_metadata
# Import the formatting function from the new torrent_formatter.py
from torrent_formatter import format_torrent_metadata_as_string

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py [path_to_torrent_file].torrent")
        sys.exit(1)

    torrent_filepath = sys.argv[1]

    if not os.path.exists(torrent_filepath):
        print(f"ERROR: The file '{torrent_filepath}' was not found.")
        sys.exit(1)

    try:
        metadata = get_torrent_metadata(torrent_filepath)
        # Use the imported formatting function
        formatted_output = format_torrent_metadata_as_string(metadata)
        print(formatted_output)

    except FileNotFoundError as e:
        print(f"\nERROR: File system error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()