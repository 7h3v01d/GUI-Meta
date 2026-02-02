import hashlib
import os
import math
import bencoding # You might need to install this: pip install bencoding

class TorrentVerifier:
    """
    A class to parse .torrent files and verify the integrity of downloaded files
    against the torrent's piece hashes.
    """

    def __init__(self):
        """
        Initializes the TorrentVerifier. No specific state is held at init
        as verification is done per file.
        """
        pass

    def parse_torrent_file(self, torrent_file_path):
        """
        Parses a .torrent file to extract essential information.
        Assumes a single-file torrent for simplicity. For multi-file torrents,
        you would iterate through the 'files' key in the 'info' dictionary.

        Args:
            torrent_file_path (str): The path to the .torrent file.

        Returns:
            dict: A dictionary containing 'file_name', 'total_size',
                  'piece_length', and 'piece_hashes'.
                  Returns None if parsing fails or essential keys are missing.
        """
        try:
            with open(torrent_file_path, 'rb') as f:
                torrent_data = bencoding.bdecode(f.read())

            info = torrent_data.get(b'info')
            if not info:
                print(f"Error: 'info' dictionary not found in {torrent_file_path}")
                return None

            # Extract file name
            file_name = info.get(b'name', b'unknown_file').decode('utf-8')

            # Extract total file size
            # Check for single file torrents first
            total_size = info.get(b'length')
            if total_size is None:
                # Check for multi-file torrents (sum lengths)
                files = info.get(b'files')
                if files:
                    total_size = sum(f.get(b'length', 0) for f in files)
                else:
                    print(f"Error: Could not determine total file size in {torrent_file_path}")
                    return None

            # Extract piece length
            piece_length = info.get(b'piece length')
            if not isinstance(piece_length, int) or piece_length <= 0:
                print(f"Error: Invalid 'piece length' in {torrent_file_path}")
                return None

            # Extract concatenated piece hashes
            pieces_bytes = info.get(b'pieces')
            if not isinstance(pieces_bytes, bytes) or len(pieces_bytes) % 20 != 0:
                print(f"Error: Invalid 'pieces' data in {torrent_file_path}")
                return None

            # Split concatenated hashes into a list of 20-byte SHA1 hashes
            piece_hashes = [pieces_bytes[i:i+20] for i in range(0, len(pieces_bytes), 20)]

            return {
                'file_name': file_name,
                'total_size': total_size,
                'piece_length': piece_length,
                'piece_hashes': piece_hashes
            }

        except FileNotFoundError:
            print(f"Error: Torrent file not found at {torrent_file_path}")
            return None
        except Exception as e:
            print(f"Error parsing torrent file {torrent_file_path}: {e}")
            return None

    def verify_file_integrity(self, torrent_file_path, downloaded_file_path):
        """
        Verifies the integrity and completeness of a downloaded file against
        its corresponding .torrent file.

        Args:
            torrent_file_path (str): The path to the .torrent file.
            downloaded_file_path (str): The path to the downloaded file.

        Returns:
            dict: A dictionary containing verification results:
                  'status': 'Complete & Verified', 'Complete (Size Match)', 'Incomplete (Size Mismatch)', 'Verification Failed', 'Error'.
                  'message': Detailed message about the verification.
                  'matched_pieces': Number of pieces that matched their hashes.
                  'total_pieces_expected': Total number of pieces as per torrent.
                  'expected_file_size': Size of the file as per torrent.
                  'actual_file_size': Size of the downloaded file.
        """
        results = {
            'status': 'Verification Failed',
            'message': 'An unknown error occurred.',
            'matched_pieces': 0,
            'total_pieces_expected': 0,
            'expected_file_size': 0,
            'actual_file_size': 0
        }

        # 1. Parse the .torrent file
        torrent_info = self.parse_torrent_file(torrent_file_path) # Call class method
        if not torrent_info:
            results['status'] = 'Error'
            results['message'] = 'Failed to parse torrent file.'
            return results

        expected_file_size = torrent_info['total_size']
        piece_length = torrent_info['piece_length']
        expected_piece_hashes = torrent_info['piece_hashes']

        results['expected_file_size'] = expected_file_size
        results['total_pieces_expected'] = len(expected_piece_hashes)

        # 2. Get actual file size
        try:
            actual_file_size = os.path.getsize(downloaded_file_path)
            results['actual_file_size'] = actual_file_size
        except FileNotFoundError:
            results['status'] = 'Error'
            results['message'] = f"Downloaded file not found at {downloaded_file_path}"
            return results
        except Exception as e:
            results['status'] = 'Error'
            results['message'] = f"Error accessing downloaded file: {e}"
            return results

        # 3. Check for completeness based on size
        if actual_file_size < expected_file_size:
            results['status'] = 'Incomplete (Size Mismatch)'
            results['message'] = (f"File is incomplete. Expected size: {expected_file_size} bytes, "
                                  f"Actual size: {actual_file_size} bytes.")
            return results
        elif actual_file_size > expected_file_size:
            # This shouldn't happen with proper downloads, but indicates corruption/extra data
            results['status'] = 'Verification Failed'
            results['message'] = (f"File size mismatch. Actual size ({actual_file_size} bytes) "
                                  f"is greater than expected ({expected_file_size} bytes). Possible corruption.")
            return results
        else:
            results['status'] = 'Complete (Size Match)'
            results['message'] = (f"File is complete based on size ({actual_file_size} bytes). "
                                  f"Proceeding with hash verification...")

        # 4. Perform piece-by-piece hash verification
        matched_pieces = 0
        num_pieces_expected = len(expected_piece_hashes)
        results['total_pieces_expected'] = num_pieces_expected

        try:
            with open(downloaded_file_path, 'rb') as f:
                for i in range(num_pieces_expected):
                    # Calculate the exact length of the current piece
                    # The last piece might be smaller than piece_length
                    start_byte = i * piece_length
                    # Ensure we don't read beyond the actual file size for the last piece
                    length_to_read = min(piece_length, expected_file_size - start_byte)

                    # If length_to_read is 0 or less, it means we've read past the end of the file,
                    # which can happen if actual_file_size was unexpectedly smaller during loop.
                    if length_to_read <= 0:
                        print(f"Warning: Attempted to read past file end at piece {i}.")
                        break # Exit loop if no more bytes to read for this piece

                    piece_data = f.read(length_to_read)

                    # If piece_data is less than length_to_read, the file is truncated mid-piece
                    if len(piece_data) < length_to_read:
                        results['status'] = 'Incomplete (Truncated Mid-Piece)'
                        results['message'] = (f"File truncated mid-piece at piece {i}. "
                                              f"Read {len(piece_data)} bytes, expected {length_to_read} bytes.")
                        return results

                    calculated_hash = hashlib.sha1(piece_data).digest()

                    if calculated_hash == expected_piece_hashes[i]:
                        matched_pieces += 1
                    # else:
                        # Optional: Print which piece failed to match for debugging
                        # print(f"Piece {i} hash mismatch!")

            results['matched_pieces'] = matched_pieces

            if matched_pieces == num_pieces_expected:
                results['status'] = 'Complete & Verified'
                results['message'] = (f"File is fully complete and all {matched_pieces} pieces "
                                      f"successfully verified against torrent hashes.")
            else:
                results['status'] = 'Complete (Partial Hash Match)'
                results['message'] = (f"File is complete by size, but only {matched_pieces} out of "
                                      f"{num_pieces_expected} pieces matched their hashes. "
                                      f"The file may be corrupted or altered.")

        except Exception as e:
            results['status'] = 'Error'
            results['message'] = f"An error occurred during hash verification: {e}"

        return results

# --- Example Usage ---
if __name__ == '__main__':
    # Create an instance of the TorrentVerifier class
    verifier = TorrentVerifier()

    # --- IMPORTANT: Replace with your actual paths ---
    # Create a dummy .torrent file and a dummy downloaded file for testing
    # In a real scenario, you would point to your actual files.

    dummy_torrent_path = "test_file.torrent"
    dummy_downloaded_path = "downloaded_test_file.txt"

    # Create dummy data for a simple .torrent structure
    # This simulates a file named 'my_test_file.txt' of size 5000 bytes,
    # with a piece length of 1024 bytes.
    # It has 5 pieces (ceil(5000/1024) = 5).
    # The 'pieces' field is concatenated SHA1 hashes.
    # For this example, we'll use placeholder hashes.
    # In a real torrent, these would be the actual SHA1 hashes of the pieces.

    # Generate some dummy content and corresponding hashes
    dummy_content = b"This is some test data for a dummy file. " * 500
    dummy_file_size = len(dummy_content)
    dummy_piece_length = 1024 # Example piece length
    num_dummy_pieces = math.ceil(dummy_file_size / dummy_piece_length)
    dummy_piece_hashes = []

    for i in range(num_dummy_pieces):
        start_byte = i * dummy_piece_length
        length_to_read = min(dummy_piece_length, dummy_file_size - start_byte)
        piece_data = dummy_content[start_byte:start_byte + length_to_read]
        dummy_piece_hashes.append(hashlib.sha1(piece_data).digest())

    dummy_bencoded_torrent_data = {
        b'announce': b'http://example.com/announce',
        b'info': {
            b'name': b'my_test_file.txt',
            b'length': dummy_file_size,
            b'piece length': dummy_piece_length,
            b'pieces': b''.join(dummy_piece_hashes)
        }
    }

    try:
        with open(dummy_torrent_path, 'wb') as f:
            f.write(bencoding.bencode(dummy_bencoded_torrent_data))
        print(f"Created dummy torrent file: {dummy_torrent_path}")

        # Create a dummy downloaded file (e.g., complete and matching)
        with open(dummy_downloaded_path, 'wb') as f:
            f.write(dummy_content)
        print(f"Created dummy downloaded file: {dummy_downloaded_path}")

        print("\n--- Verifying a COMPLETE and MATCHING file ---")
        verification_result = verifier.verify_file_integrity(dummy_torrent_path, dummy_downloaded_path)
        for key, value in verification_result.items():
            print(f"{key}: {value}")

        # --- Test Case: Incomplete File ---
        incomplete_downloaded_path = "incomplete_test_file.txt"
        with open(incomplete_downloaded_path, 'wb') as f:
            f.write(dummy_content[:-100]) # Make it 100 bytes shorter
        print(f"\nCreated dummy incomplete file: {incomplete_downloaded_path}")

        print("\n--- Verifying an INCOMPLETE file ---")
        verification_result_incomplete = verifier.verify_file_integrity(dummy_torrent_path, incomplete_downloaded_path)
        for key, value in verification_result_incomplete.items():
            print(f"{key}: {value}")

        # --- Test Case: Corrupted Piece (Size matches, but content changes) ---
        corrupted_downloaded_path = "corrupted_test_file.txt"
        corrupted_content = bytearray(dummy_content)
        # Corrupt a byte in the middle
        if len(corrupted_content) > 1000:
            corrupted_content[1000] = (corrupted_content[1000] + 1) % 256 # Change a byte
        with open(corrupted_downloaded_path, 'wb') as f:
            f.write(corrupted_content)
        print(f"\nCreated dummy corrupted file: {corrupted_downloaded_path}")

        print("\n--- Verifying a CORRUPTED (by content) file ---")
        verification_result_corrupted = verifier.verify_file_integrity(dummy_torrent_path, corrupted_downloaded_path)
        for key, value in verification_result_corrupted.items():
            print(f"{key}: {value}")

    finally:
        # Clean up dummy files
        for p in [dummy_torrent_path, dummy_downloaded_path,
                  incomplete_downloaded_path, corrupted_downloaded_path]:
            if os.path.exists(p):
                os.remove(p)
                print(f"Cleaned up {p}")
