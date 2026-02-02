# torinfo.py - A module for decoding BitTorrent files into raw metadata

import bencoding
import os
import traceback

# --- NOTES ON LIBRARY CHOICE AND DEBUGGING HISTORY ---
# PROBLEM ENCOUNTERED:
# Initially, attempts to use 'bencode' or 'python-bencode' libraries led to:
# 1. AttributeError: module 'bencode' has no attribute 'bdecode' (or 'decode')
# 2. TypeError: cannot use a string pattern on a bytes-like object
#
# ROOT CAUSE:
# Multiple Python packages on PyPI use the 'bencode' import name but have
# different APIs (e.g., bencode.bdecode, bencode.decode, bencode._decode)
# or are not fully compatible with Python 3's handling of binary data (bytes).
# The specific 'bencode' library initially installed on the user's system
# (often 'bencode.py') was causing these compatibility errors.
#
# SOLUTION:
# 1. Uninstalled the problematic 'bencode' library:
#    pip uninstall bencode
#    (Often required manual deletion of C:\...\site-packages\bencode folder)
# 2. Installed a known-good and Python 3 compatible bencode parsing library:
#    pip install bencoding
# 3. Changed the import statement from 'import bencode' to 'import bencoding'
#    and updated function calls to 'bencoding.bdecode()'.
#
# This ensures a consistent and reliable bencode decoding experience.
# --- END NOTES ---

def decode_torrent_file(filepath):
    """
    Decodes a .torrent file and returns its raw bencoded metadata dictionary.

    Args:
        filepath (str): The path to the .torrent file.

    Returns:
        dict: The decoded raw torrent metadata. Keys and string values are bytes.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        Exception: For any errors during bencode decoding or file reading.
    """
    try:
        with open(filepath, 'rb') as f:
            torrent_data = bencoding.bdecode(f.read())
        return torrent_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{filepath}' was not found.")
    except Exception as e:
        raise Exception(f"Error decoding torrent file: {e}")

def get_torrent_metadata(filepath):
    """
    High-level function to decode a torrent file and return its raw metadata.
    This simplifies interaction for other modules.

    Args:
        filepath (str): The path to the .torrent file.

    Returns:
        dict: The decoded raw torrent metadata, or raises an exception if an error occurs.
    """
    return decode_torrent_file(filepath)

# No display or formatting functions here.
# No __main__ block, as this is purely a module.