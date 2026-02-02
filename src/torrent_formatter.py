# torrent_formatter.py - Module for formatting torrent metadata and verification results

import datetime
import os
import math # Added for potential use in formatting if needed, though not directly used by formatter yet

def format_torrent_metadata_as_string(metadata):
    """
    Formats the raw torrent metadata into a human-readable string with titles and spacing.

    Args:
        metadata (dict): The decoded raw torrent metadata dictionary.

    Returns:
        str: A nicely formatted string of the torrent metadata.
    """
    output_lines = []
    append = output_lines.append

    append("==========================================")
    append("           TORRENT METADATA               ")
    append("==========================================")
    append("")

    # === General Information ===
    append("--- GENERAL INFORMATION ---")
    if b'announce' in metadata:
        append(f"Announce URL: {metadata[b'announce'].decode('utf-8', errors='replace')}")

    if b'announce-list' in metadata:
        announce_list_flat = [url.decode('utf-8', errors='replace') for sublist in metadata[b'announce-list'] for url in sublist]
        append(f"Announce List: {', '.join(announce_list_flat)}")

    if b'comment' in metadata:
        append(f"Comment: {metadata[b'comment'].decode('utf-8', errors='replace')}")

    if b'created by' in metadata:
        append(f"Created By: {metadata[b'created by'].decode('utf-8', errors='replace')}")

    if b'creation date' in metadata:
        try:
            timestamp = metadata[b'creation date']
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            append(f"Creation Date: {dt_object.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except (TypeError, ValueError):
            append(f"Creation Date: Invalid timestamp ({metadata[b'creation date']})")

    append("")

    # === Info Dictionary Details ===
    info = metadata.get(b'info', {})
    if info:
        append("--- INFO DICTIONARY DETAILS ---")
        torrent_name = info.get(b'name', b'N/A').decode('utf-8', errors='replace')
        append(f"Torrent Name: {torrent_name}")

        piece_length = info.get(b'piece length')
        if piece_length is not None:
            # Format piece length in human-readable units (e.g., KB, MB)
            def format_bytes(bytes_val):
                if bytes_val < 1024:
                    return f"{bytes_val} bytes"
                elif bytes_val < 1024**2:
                    return f"{bytes_val / 1024:.2f} KB"
                elif bytes_val < 1024**3:
                    return f"{bytes_val / (1024**2):.2f} MB"
                else:
                    return f"{bytes_val / (1024**3):.2f} GB"
            append(f"Piece Length: {format_bytes(piece_length)}")

        pieces_hash_string = info.get(b'pieces')
        if pieces_hash_string:
            num_pieces = len(pieces_hash_string) // 20 # SHA1 hash is 20 bytes
            append(f"Number of Pieces: {num_pieces}")
        else:
            append("Number of Pieces: N/A (pieces hash string missing)")

        # Handle Single-File vs. Multi-File Torrents
        total_size_bytes = 0
        if b'files' in info:
            append("\nFiles (Multiple):")
            for i, file_entry in enumerate(info[b'files']):
                try:
                    path_parts = [p.decode('utf-8', errors='replace') for p in file_entry[b'path']]
                    file_path = os.path.join(*path_parts)
                    file_length_bytes = file_entry.get(b'length', 0)
                    total_size_bytes += file_length_bytes
                    append(f"  {i+1}. Path: {file_path}, Size: {format_bytes(file_length_bytes)}")
                except (KeyError, AttributeError, UnicodeDecodeError) as e:
                    append(f"  - Error parsing file entry: {file_entry} ({e})")
        elif b'length' in info:
            length = info[b'length']
            total_size_bytes += length
            append(f"File Size: {format_bytes(length)}")
        else:
            append("File Info: N/A (Neither 'files' nor 'length' found in info dict)")

        if total_size_bytes > 0:
            append(f"\nTotal Torrent Content Size: {format_bytes(total_size_bytes)}")
    else:
        append("--- INFO DICTIONARY MISSING ---")

    append("\n===========================================")
    append("          END OF METADATA REPORT           ")
    append("===========================================")

    return "\n".join(output_lines)

def format_verification_results_as_string(results):
    """
    Formats the verification results dictionary into a human-readable string.

    Args:
        results (dict): The dictionary returned by verify_torrent_integrity.

    Returns:
        str: A nicely formatted string of the verification report.
    """
    output_lines = []
    append = output_lines.append

    append("==========================================")
    append("       INTEGRITY VERIFICATION RESULTS     ")
    append("==========================================")
    append("")

    append(f"Overall Status: {results.get('status', 'N/A').upper()}")
    append(f"Message: {results.get('message', 'No message provided.')}")
    append("")

    append(f"Total Pieces Expected: {results.get('total_pieces', 0)}")
    append(f"Pieces Verified Successfully: {results.get('verified_pieces', 0)}")
    append("")

    if results.get('missing_files'):
        append("--- MISSING FILES ---")
        for f in results['missing_files']:
            # Format the dictionary for each missing file clearly
            torrent_path = f.get('torrent_path', 'N/A')
            attempted_absolute_path = f.get('attempted_absolute_path', 'N/A')
            reason = f.get('reason', 'N/A')
            append(f"- Torrent Path: '{torrent_path}'")
            append(f"  Attempted Local Path: '{attempted_absolute_path}'")
            append(f"  Reason: {reason}")
            append("---") # Separator for clarity
        append("")

    # --- NEW ADDITION FOR VERIFIED FILES ---
    # This section displays the list of files that were actually opened and verified.
    if results.get('actual_file_paths_used'):
        append("--- VERIFIED FILES ---")
        # Sort for consistent output, though not strictly necessary for functionality
        sorted_paths = sorted(results['actual_file_paths_used'])
        for i, path in enumerate(sorted_paths):
            append(f"- {i+1}. {path}")
        append("")
    # --- END NEW ADDITION ---

    if results.get('mismatched_pieces'):
        append("--- MISMATCHED PIECES ---")
        append(f"Number of Mismatched Pieces: {len(results['mismatched_pieces'])}")
        # For brevity, only show first few or range. For full list: 'for p_idx in results['mismatched_pieces']:'
        if len(results['mismatched_pieces']) <= 10:
            append(f"Piece Indexes: {', '.join(map(str, results['mismatched_pieces']))}")
        else:
            append(f"Piece Indexes (first 10): {', '.join(map(str, results['mismatched_pieces'][:10]))} ...")
        append("")

    # Diagnostic messages are useful for debugging base path resolution and normalization attempts
    if results.get('diagnostics'):
        append("--- VERIFIER DIAGNOSTICS ---")
        for diag_msg in results['diagnostics']:
            append(f"- {diag_msg}")
        append("") # Add a blank line for separation

    append("==========================================")
    append("       END OF VERIFICATION REPORT         ")
    append("==========================================")

    return "\n".join(output_lines)

# Helper function for format_bytes and format_time might be defined here
# if not already in torinfo.py and needed by this module