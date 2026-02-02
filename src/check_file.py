import os

# Define the full path to the Subs directory
subs_directory = r"H:\TorrentCompleter\Cheech Chongs Last Movie (2024) [720p] [WEBRip] [YTS.MX]\Subs"
expected_filename = "Canadian | SDH.eng.HI.srt"
full_expected_path = os.path.join(subs_directory, expected_filename)

print(f"Checking for expected file: {full_expected_path}")

if os.path.exists(full_expected_path):
    print(f"SUCCESS: The file '{expected_filename}' was found at the expected path.")
    print(f"Path verification check: {os.path.isfile(full_expected_path)}")
else:
    print(f"FAILURE: The file '{expected_filename}' was NOT found at the expected path.")

print("\n--- Listing contents of the Subs directory ---")
try:
    if os.path.isdir(subs_directory):
        for item in os.listdir(subs_directory):
            print(f"Found item: '{item}'")
    else:
        print(f"Error: The directory '{subs_directory}' does not exist.")
except PermissionError:
    print(f"Permission Error: Cannot access directory '{subs_directory}'.")
except Exception as e:
    print(f"An error occurred while listing directory contents: {e}")

print("\n--- End of Check ---")