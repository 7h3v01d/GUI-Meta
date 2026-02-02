The Program Files

torinfo.py (The Decoder/Info Gatherer)
--------------------------------------
What it does: This is the "brain" for understanding the core .torrent file. When you give it a .torrent file, it reads the raw, jumbled data inside (which is in a special format called "bencode") and turns it into something Python can understand (like dictionaries and lists).
Key function: get_torrent_metadata(filepath)
How it passes data: It gives the decoded torrent information (a Python dictionary) to other files that ask for it, like main.py, gui.py, and torrent_verifier.py.

torrent_formatter.py (The Report Card Generator)
------------------------------------------------
What it does: Imagine you have a bunch of raw numbers and details. This file takes that raw information (especially the decoded torrent data from torinfo.py or verification results from torrent_verifier.py) and makes it pretty and easy to read. It adds headings, spacing, and makes sense of the numbers (like converting bytes to GB).
Key functions: format_torrent_metadata_as_string(metadata), format_verification_results_as_string(results)
How it passes data: It receives raw data (dictionaries) and returns nicely formatted strings. It doesn't directly send data to other files, but other files call its functions to get the formatted text back.

torrent_verifier.py (The Integrity Checker)
-------------------------------------------
What it does: This is the "detective." It takes a .torrent file and a folder on your computer, and then it meticulously checks if the files in that folder match what the .torrent file says they should be. It calculates "hashes" (like digital fingerprints) of your local files and compares them to the hashes stored in the torrent file.
Key function: verify_torrent_integrity(torrent_filepath, data_root_directory, progress_callback=None)
How it passes data:
It asks torinfo.py for the torrent's metadata to know what to check.
It receives the torrent_filepath and data_root_directory from whoever calls it (e.g., gui.py).
It sends progress updates (current piece, total pieces, message) to the gui.py if a progress_callback function is provided.
It returns a detailed dictionary of results (success/failure, missing files, mismatched pieces, etc.) to the calling code (gui.py).

main.py (The Command-Line Runner)
---------------------------------
What it does: This is the "quick console tool." If you prefer typing commands in your terminal, this is what you use. It takes a .torrent file path as an argument and then uses torinfo.py and torrent_formatter.py to simply print the torrent's metadata directly to your screen. It doesn't have a graphical interface.
How it passes data:
It gets the torrent file path from the command line when you run it.
It calls torinfo.py to get the metadata.
It calls torrent_formatter.py to make the metadata readable.
It prints the formatted output to the console.

gui.py (The User-Friendly Window)
---------------------------------
What it does: This is the "pretty interface" that brings everything together for you to click and interact with. It creates the window, buttons, text boxes, and progress bars. It lets you select torrent files and data folders visually. It runs the verification process in the background so the app doesn't freeze.
Key class: TorrentInfoApp
How it passes data:
It allows you (the user) to select the torrent_filepath and data_root_directory using file dialogs.
When you click "Load Metadata," it calls torinfo.py to get the metadata and then calls torrent_formatter.py to display it in a text box.
When you click "Verify Integrity," it creates a VerificationWorker (a background task) and passes the torrent_filepath and data_root_directory to it.
The VerificationWorker then calls torrent_verifier.py to do the actual checking.
It receives progress updates (progress_updated signal) from the VerificationWorker and updates the progress bar and status message.
It receives the final verification_results (dictionary) from the VerificationWorker (verification_finished signal) and then calls torrent_formatter.py to display the results in its own text box and shows a popup message (QMessageBox).

check_file.py (The Test Helper)
-------------------------------
What it does: This isn't part of the main application flow, but it's a helpful little script for you (the developer) to quickly check if a specific file exists at a specific path. It's often used for debugging or confirming file paths outside of the main application.
How it passes data: It doesn't pass data to other Python files. It's a standalone script that prints its findings directly to the console.


How They Work Together (The Flow):
----------------------------------
Imagine you open the gui.py application:

1. You: Click "Browse Torrent File" button.
2. gui.py: Shows a file dialog.
3. You: Select my_movie.torrent.
4. gui.py: Stores the path to my_movie.torrent.
5. You: Click "Load Metadata" button.
6. gui.py: Calls torinfo.get_torrent_metadata('path/to/my_movie.torrent').
7. torinfo.py: Reads my_movie.torrent, decodes it, and returns a Python dictionary of metadata to gui.py.
8. gui.py: Calls torrent_formatter.format_torrent_metadata_as_string(metadata_dictionary).
9. torrent_formatter.py: Takes the dictionary, makes it pretty, and returns a nice string to gui.py.
10. gui.py: Displays that formatted string in the "Metadata Display" text box.

Now, for verification:

1. You: Click "Browse Data Root Directory."
2. gui.py: Shows a folder dialog.
3. You: Select H:\MyMovies.
4. gui.py: Stores the path to H:\MyMovies.
5. You: Click "Verify Integrity" button.
6. gui.py: Starts a VerificationWorker thread, passing it my_movie.torrent path and H:\MyMovies path, and a function for progress updates.
7. VerificationWorker.run(): Calls torrent_verifier.verify_torrent_integrity('path/to/my_movie.torrent', 'H:\MyMovies', progress_callback_function).
8. torrent_verifier.py:
	Internally, it calls torinfo.get_torrent_metadata to get the torrent's piece hashes and file structure.
	It then starts reading your actual files in H:\MyMovies.
	As it checks each piece, it calls the progress_callback_function (which belongs to gui.py) to send updates about how many pieces are verified and an optional message.
9. gui.py (via progress_callback_function): Receives the progress updates and updates its progress bar and status label.
10 torrent_verifier.py: Finishes checking all pieces and returns a dictionary of verification_results (status, mismatched pieces, etc.) to the VerificationWorker.
11.	VerificationWorker: Emits the verification_finished signal, sending the verification_results dictionary to gui.py.
12. gui.py: Receives the verification_results.
13. gui.py: Calls torrent_formatter.format_verification_results_as_string(results_dictionary).
14. torrent_formatter.py: Takes the results, makes them readable, and returns a string to gui.py.
15. gui.py: Displays the formatted verification report in the "Verification Display" text box and pops up a message box (e.g., "Verification Complete" or "Verification Failed").

So, they work like a team, each specializing in a different part of the process, passing information between them to achieve the overall goal of understanding and verifying torrent files.