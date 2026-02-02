import os
import re
import sys
from base_parser import BaseParser # Import BaseParser

class FileTracker(BaseParser): # Inherit from BaseParser
    def __init__(self):
        super().__init__() # Initialize BaseParser's attributes (like regex patterns)
        print("INFO: FileTracker instance created.")

    def find_file(self, search_term, search_location):
        """
        Searches for files within a given directory and its subdirectories
        using intelligent matching based on filename structure.

        Args:
            search_term (str): The term to search for (e.g., "Game of Thrones S04E04", "game of s04e04", "My Movie").
            search_location (str): The starting directory for the search.

        Returns:
            list: A list of dictionaries, each containing 'path' and 'size_bytes'
                  for matching files. Returns an empty list if no matches found.
        """
        found_files = []
        normalized_search_term = self._normalize_string_for_comparison(search_term)

        # Pre-parse the search term for TV show components
        search_season, search_episode, sxe_start_in_search, sxe_end_in_search = self.extract_season_episode_from_string(search_term)

        # If SxE was found in search term, get the title part that comes before it
        if sxe_start_in_search != -1:
            raw_search_title_part = search_term[:sxe_start_in_search].strip()
            # Clean the search title part of potential trailing garbage from other tags if any
            normalized_search_title_part = self._clean_string_of_all_tags(raw_search_title_part)
        else:
            # If no SxE, use the full normalized search term as the title part
            normalized_search_title_part = normalized_search_term


        print(f"INFO: Search requested for term='{search_term}' (normalized: '{normalized_search_term}') in location='{search_location}'")
        print(f"DEBUG: FileTracker's internal search parameters: Search Title Part: '{normalized_search_title_part}', Search Season: {search_season}, Search Episode: {search_episode}")
        print(f"Searching for files containing '{normalized_search_term}' or TV show components in '{search_location}' and its subdirectories...")

        if not os.path.isdir(search_location):
            print(f"ERROR: Search location '{search_location}' is not a valid directory.")
            return []

        print(f"INFO: Starting recursive directory walk from '{search_location}'...")
        for root, dirs, files in os.walk(search_location):
            print(f"INFO: Scanning directory: '{root}'")

            for file_name in files:
                full_path = os.path.join(root, file_name)
                
                # Assume a match by default, then try to disprove it
                is_a_match = False

                # Option 1: Direct substring match on normalized filename
                normalized_file_name_full = self._normalize_string_for_comparison(file_name)
                if normalized_search_term in normalized_file_name_full:
                    is_a_match = True
                    print(f"DEBUG:   Direct normalized match: '{normalized_search_term}' found in '{normalized_file_name_full}'")
                else:
                    print(f"DEBUG:   No direct normalized match for '{normalized_search_term}' in '{normalized_file_name_full}'")


                # Option 2: Smart TV Show match (if search term had SxE)
                if not is_a_match and search_season is not None and search_episode is not None:
                    # Try to parse the current file's name as a TV show
                    file_season, file_episode, file_sxe_start, file_sxe_end = self.extract_season_episode_from_string(file_name)

                    if file_season is not None and file_episode is not None:
                        # Extract and normalize the title part of the current file's name
                        raw_file_title_part = file_name[:file_sxe_start].strip()
                        normalized_file_title_part = self._clean_string_of_all_tags(raw_file_title_part)

                        print(f"DEBUG:   Attempting TV show smart match for file '{file_name}'")
                        print(f"DEBUG:     File's Parsed Title Part: '{normalized_file_title_part}', Season: {file_season}, Episode: {file_episode}")

                        title_part_matches = False
                        if normalized_search_title_part and normalized_search_title_part in normalized_file_title_part:
                            title_part_matches = True
                        elif not normalized_search_title_part and normalized_file_title_part: # If search had only SxE, and file has a title part
                            title_part_matches = True # Consider it a match on title part if search title was empty.

                        sxe_matches = (file_season == search_season) and (file_episode == search_episode)

                        print(f"DEBUG:     Title Part Match: {title_part_matches}, SxE Match: {sxe_matches}")

                        if title_part_matches and sxe_matches:
                            is_a_match = True
                            print(f"DEBUG:   TV Show Smart Match SUCCESS for '{file_name}'!")


                if is_a_match:
                    try:
                        file_size_bytes = os.path.getsize(full_path)
                        found_files.append({"path": full_path, "size_bytes": file_size_bytes})
                        # print(f"Found: {full_path} (Size: {file_size_bytes} bytes)") # Suppressed in GUI
                    except FileNotFoundError:
                        print(f"WARNING: File not found during size check (possibly moved/deleted): {full_path}")
                    except OSError as e:
                        print(f"ERROR: OS error accessing file {full_path}: {e}")
        print("INFO: Finished scanning all subdirectories.")
        print(f"INFO: Total items matching search term: {len(found_files)}.")
        return found_files

# Example Usage (for testing filetracker.py directly)
if __name__ == '__main__':
    tracker = FileTracker()

    # Example 1: Search for a TV show episode (should now work if file is normalized-match)
    print("\n--- Test 1: Search for 'game of s04e04' ---")
    # Assuming you have a file like 'Game.of.Thrones.S04E04.HDTV.x264-KILLERS.mp4'
    results1 = tracker.find_file(
        search_term="game of s04e04",
        search_location=r"//PL3XSVR/WDElements 12TB/Plex TV Shows" # Adjust to a real path if testing
    )
    if results1:
        for res in results1:
            print(f"Found: {res['path']} (Size: {res['size_bytes']} bytes)")
    else:
        print("No results found for 'game of s04e04'.")

    # Example 2: Search for 'game of thron s04e04'
    print("\n--- Test 2: Search for 'game of thron s04e04' ---")
    results2 = tracker.find_file(
        search_term="game of thron s04e04",
        search_location=r"//PL3XSVR/WDElements 12TB/Plex TV Shows" # Adjust to a real path if testing
    )
    if results2:
        for res in results2:
            print(f"Found: {res['path']} (Size: {res['size_bytes']} bytes)")
    else:
        print("No results found for 'game of thron s04e04'.")

    # Example 3: Search for 'game of thrones s04e04'
    print("\n--- Test 3: Search for 'game of thrones s04e04' ---")
    results3 = tracker.find_file(
        search_term="game of thrones s04e04",
        search_location=r"//PL3XSVR/WDElements 12TB/Plex TV Shows" # Adjust to a real path if testing
    )
    if results3:
        for res in results3:
            print(f"Found: {res['path']} (Size: {res['size_bytes']} bytes)")
    else:
        print("No results found for 'game of thrones s04e04'.")
