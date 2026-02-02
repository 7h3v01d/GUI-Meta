# torrent_verifier.py - Module for verifying torrent file integrity against local data

import os
import hashlib
import math
import traceback
import re # Added for regex

from torinfo import get_torrent_metadata

def _sanitize_path_for_os(path_component: str) -> str:
    """
    Sanitizes a single path component (filename or directory name) for OS compatibility,
    primarily for Windows, by replacing illegal characters.
    Common illegal characters for Windows: < > : " / \ | ? *
    The pipe '|' character is specifically known to be replaced by '_' by Windows.
    """
    # Define a set of characters that are illegal in Windows filenames
    # For simplicity, replacing them with underscore '_'
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized_component = re.sub(illegal_chars, '_', path_component)

    # Windows also disallows names like CON, PRN, AUX, NUL, COM1-COM9, LPT1-LPT9
    # at the end of a path component without an extension, but for this context,
    # just handling the special characters is sufficient.
    return sanitized_component

def verify_torrent_integrity(torrent_filepath: str, data_root_directory: str, progress_callback=None):
    """
    Verifies the integrity of files in a given data_root_directory against
    the piece hashes specified in a .torrent file.

    Args:
        torrent_filepath (str): Path to the .torrent file.
        data_root_directory (str): Root directory where the downloaded/target files are located.
        progress_callback (callable, optional): A function to call with (current_piece, total_pieces, message)
                                                 during verification. Defaults to None.

    Returns:
        dict: A dictionary containing verification results:
              'status': 'success', 'failure', 'error'
              'message': Detailed message about the verification.
              'total_pieces': Total number of pieces expected.
              'verified_pieces': Number of pieces successfully verified.
              'missing_files': List of dicts {torrent_path, attempted_absolute_path, reason, is_sanitized_attempt}.\
              'mismatched_pieces': List of piece indexes that failed verification.
              'actual_file_paths_used': List of absolute paths to files actually opened for verification.
              'diagnostics': List of strings for debugging (e.g., base paths tried).
    """
    results = {
        'status': 'error',
        'message': 'An unhandled error occurred during verification.',
        'total_pieces': 0,
        'verified_pieces': 0,
        'missing_files': [],
        'mismatched_pieces': [],
        'actual_file_paths_used': [],
        'diagnostics': []
    }

    try:
        torrent_metadata = get_torrent_metadata(torrent_filepath)
        info = torrent_metadata.get(b'info', {})

        piece_length = info.get(b'piece length')
        pieces_hashes = info.get(b'pieces')

        if not piece_length or not pieces_hashes:
            results['message'] = "Invalid torrent file: Missing 'piece length' or 'pieces'."
            return results

        total_pieces = len(pieces_hashes) // 20 # SHA1 hash is 20 bytes
        results['total_pieces'] = total_pieces

        files_info = []
        if b'files' in info: # Multi-file torrent
            for file_dict in info[b'files']:
                path_components = [p.decode('utf-8', errors='replace') for p in file_dict[b'path']]
                files_info.append({
                    'path': os.path.join(*path_components),
                    'length': file_dict[b'length']
                })
        else: # Single-file torrent
            file_name = info.get(b'name', b'').decode('utf-8', errors='replace')
            file_length = info.get(b'length', 0)
            if file_name and file_length:
                files_info.append({
                    'path': file_name,
                    'length': file_length
                })
            else:
                results['message'] = "Invalid torrent file: Missing file name or length for single-file torrent."
                return results

        normalized_data_root = os.path.abspath(data_root_directory)
        results['diagnostics'].append(f"Normalized data_root_directory: {normalized_data_root}")

        # Determine potential base paths for files
        # 1. The data_root_directory itself
        # 2. data_root_directory + torrent_name (common for single-folder torrents)
        torrent_name = info.get(b'name', b'').decode('utf-8', errors='replace')
        potential_base_paths = [
            normalized_data_root,
            os.path.join(normalized_data_root, torrent_name)
        ]
        results['diagnostics'].append(f"Potential base paths to try: {potential_base_paths}")

        # Map torrent file paths to actual file system paths
        actual_file_paths = {}
        current_file_handle = None # Store the currently open file handle
        current_file_handle_path = None # Store the path of the currently open file handle

        results['diagnostics'].append(f"Detected {len(files_info)} files in torrent.")

        for torrent_file in files_info:
            torrent_path_orig = torrent_file['path']
            found_actual_path = None
            is_sanitized_attempt = False

            # Try finding the file with original path, then with sanitized path
            for path_variant in [torrent_path_orig]:
                # Split the path into components, sanitize each, then rejoin
                sanitized_path_components = [_sanitize_path_for_os(p) for p in path_variant.split(os.sep)]
                sanitized_torrent_path = os.path.join(*sanitized_path_components)

                attempt_paths = [
                    os.path.join(base, torrent_path_orig) for base in potential_base_paths
                ]
                # Add sanitized attempts
                if torrent_path_orig != sanitized_torrent_path:
                    attempt_paths.extend([
                        os.path.join(base, sanitized_torrent_path) for base in potential_base_paths
                    ])
                    is_sanitized_attempt = True


                for attempted_relative_path in [torrent_path_orig, sanitized_torrent_path]:
                    for base_path in potential_base_paths:
                        attempted_absolute_path = os.path.join(base_path, attempted_relative_path)
                        results['diagnostics'].append(f"Attempting to find: {attempted_absolute_path}")
                        if os.path.exists(attempted_absolute_path) and os.path.isfile(attempted_absolute_path):
                            found_actual_path = attempted_absolute_path
                            results['diagnostics'].append(f"FOUND: {found_actual_path} (from base: {base_path})")
                            break
                    if found_actual_path:
                        break # Found it with one of the sanitized paths

                if found_actual_path:
                    break # Found it with original or sanitized path

            if found_actual_path:
                actual_file_paths[torrent_path_orig] = {
                    'path': found_actual_path,
                    'length': torrent_file['length']
                }
            else:
                missing_info = {
                    'torrent_path': torrent_path_orig,
                    'attempted_local_path': 'See diagnostics for paths tried', # Too long to put all here
                    'reason': 'File not found at any attempted location.'
                }
                results['missing_files'].append(missing_info)
                results['diagnostics'].append(f"NOT FOUND: {torrent_path_orig} in any base path.")


        # If all expected files are missing or none were found, report immediately
        if not actual_file_paths:
            results['status'] = 'failure'
            results['message'] = "No torrent data files could be located for verification."
            # Only return if all files are missing. If some are found, proceed to verify what's available.
            return results

        # Sort files by their original torrent path to ensure correct order for piece reading
        sorted_files_to_verify = sorted(actual_file_paths.items(), key=lambda item: item[0])
        results['actual_file_paths_used'] = [f_info['path'] for _, f_info in sorted_files_to_verify]

        current_file_index = 0
        current_file_path_in_list = None
        current_file_size = 0
        current_file_offset = 0 # Current read position within the current file

        # Calculate total size to ensure we don't read beyond end of files if they are truncated
        total_data_length = sum(f['length'] for f in files_info)
        data_read_so_far = 0

        # Initialize current file handle if there are files to verify
        if sorted_files_to_verify:
            current_file_path_in_list = sorted_files_to_verify[current_file_index][1]['path']
            current_file_size = os.path.getsize(current_file_path_in_list) # Actual size on disk
            current_file_handle = open(current_file_path_in_list, 'rb')
            current_file_handle_path = current_file_path_in_list # Store path for diagnostics


        # Iterate through pieces and verify hash
        for current_piece_index in range(total_pieces):
            expected_hash = pieces_hashes[current_piece_index * 20 : (current_piece_index + 1) * 20]
            piece_data = b''
            bytes_to_read_for_piece = piece_length

            # Callback for progress, including current status message
            if progress_callback:
                progress_percent = int((current_piece_index / total_pieces) * 100)
                progress_message = f"Verifying piece {current_piece_index + 1}/{total_pieces}..."
                progress_callback(current_piece_index, total_pieces, progress_message)

            try:
                while bytes_to_read_for_piece > 0:
                    # Check if we need to open a new file
                    if current_file_handle is None or current_file_offset >= current_file_size:
                        if current_file_handle:
                            current_file_handle.close() # Close previous file
                            current_file_handle = None

                        current_file_index += 1
                        if current_file_index >= len(sorted_files_to_verify):
                            # Ran out of files but still need data for the piece.
                            # This means files are missing or severely truncated relative to torrent.
                            results['diagnostics'].append(
                                f"WARNING: Ran out of files before completing piece {current_piece_index}. Padding with nulls."
                            )
                            piece_data += b'\0' * bytes_to_read_for_piece # Pad with nulls
                            bytes_to_read_for_piece = 0 # Stop trying to read
                            break # Exit inner while loop, process the piece data (with padding)


                        current_file_path_in_list = sorted_files_to_verify[current_file_index][1]['path']
                        # Add a diagnostic message when moving to a new file for the current piece
                        results['diagnostics'].append(f"Moved to next file for piece {current_piece_index}: {current_file_path_in_list}")

                        try:
                            current_file_size = os.path.getsize(current_file_path_in_list)
                            current_file_handle = open(current_file_path_in_list, 'rb')
                            current_file_handle_path = current_file_path_in_list
                            current_file_offset = 0
                        except FileNotFoundError:
                            # This should ideally be caught by initial file mapping, but as a fallback:
                            missing_info = {
                                'torrent_path': sorted_files_to_verify[current_file_index][0], # Original torrent path
                                'attempted_local_path': current_file_path_in_list,
                                'reason': 'File was expected but not found when trying to read pieces.'
                            }
                            results['missing_files'].append(missing_info)
                            results['diagnostics'].append(
                                f"ERROR: File '{current_file_path_in_list}' not found during piece reading. "
                                f"Padding piece {current_piece_index} with nulls."
                            )
                            piece_data += b'\0' * bytes_to_read_for_piece # Pad with nulls
                            bytes_to_read_for_piece = 0 # Stop trying to read
                            break # Exit inner while loop

                    # Calculate how much to read from current file for this piece
                    remaining_in_file = current_file_size - current_file_offset
                    to_read_now = min(bytes_to_read_for_piece, remaining_in_file)

                    if to_read_now > 0:
                        current_file_handle.seek(current_file_offset)
                        data = current_file_handle.read(to_read_now)
                        if not data:
                            # Read returned nothing, possibly EOF reached unexpectedly (e.g., truncated file)
                            results['diagnostics'].append(
                                f"WARNING: Unexpected EOF or empty read from '{current_file_handle_path}' at offset {current_file_offset} for piece {current_piece_index}. "
                                f"Expected to read {to_read_now} bytes, got 0. Padding with nulls."
                            )
                            piece_data += b'\0' * bytes_to_read_for_piece # Pad the rest with nulls
                            bytes_to_read_for_piece = 0
                            break
                        
                        piece_data += data
                        current_file_offset += len(data)
                        bytes_to_read_for_piece -= len(data)

                        # If we couldn't read all expected bytes (e.g., truncated file), pad the rest
                        if len(data) < to_read_now:
                            missing_bytes = to_read_now - len(data)
                            results['diagnostics'].append(
                                f"WARNING: Short read from '{current_file_handle_path}'. Expected {to_read_now} bytes, got {len(data)}. "
                                f"Adding {missing_bytes} null bytes for piece {current_piece_index}."
                            )
                            piece_data += b'\0' * missing_bytes
                            bytes_to_read_for_piece -= missing_bytes # Decrement by total bytes added/read
            except Exception as e:
                results['status'] = 'error'
                results['message'] = f"Error reading file '{current_file_handle_path}' for piece {current_piece_index}: {e}. Trace: {traceback.format_exc()}"
                return results


            # After collecting all data for the piece (potentially padded)
            actual_hash = hashlib.sha1(piece_data).digest()

            if actual_hash != expected_hash:
                results['mismatched_pieces'].append(current_piece_index)
                results['diagnostics'].append(f"MISMATCH: Piece {current_piece_index} hash mismatch. Expected: {expected_hash.hex()} Got: {actual_hash.hex()}")
            else:
                results['verified_pieces'] += 1

        # Close any open file handle
        if current_file_handle:
            current_file_handle.close()

        # Final status check after loop
        if not results['mismatched_pieces'] and not results['missing_files'] and results['verified_pieces'] == results['total_pieces']:
            results['status'] = 'success'
            results['message'] = "All pieces verified successfully, and all files found!"
        elif results['mismatched_pieces'] or results['missing_files']:
            results['status'] = 'failure'
            msg_parts = []
            if results['missing_files']:
                msg_parts.append(f"Could not locate all *required* files. Verification will proceed with available data, but integrity check may be incomplete.")
            if results['mismatched_pieces']:
                msg_parts.append(f"And completed with {len(results['mismatched_pieces'])} piece mismatches.")
            results['message'] = " ".join(msg_parts)
        else:
            results['status'] = 'failure'
            results['message'] = "Verification did not complete for all pieces or had unhandled issues."

    except FileNotFoundError as e:
        results['status'] = 'error'
        results['message'] = f"File not found error during initial torrent or data lookup: {e}"
    except Exception as e:
        results['status'] = 'error'
        results['message'] = f"An unexpected error occurred during overall verification process: {e}. Trace: {traceback.format_exc()}"

    # Report final progress
    if progress_callback:
        progress_callback(results['verified_pieces'], results['total_pieces'], results['message'])

    return results