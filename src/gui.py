# gui.py - PyQt5 GUI for the torrent metadata extractor and integrity verifier

import sys
import os
import traceback

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox, QTabWidget,
    QProgressBar, QSizePolicy, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont

# Import the decoding function from torinfo.py
from torinfo import get_torrent_metadata
# Import the formatting functions from torrent_formatter.py
from torrent_formatter import format_torrent_metadata_as_string, format_verification_results_as_string
# Import the new verification function
from torrent_verifier import verify_torrent_integrity

# --- Worker Thread for Verification ---
class VerificationWorker(QObject):
    # Define signals that the worker can emit
    progress_updated = pyqtSignal(int, str) # current_percentage, status_message
    verification_finished = pyqtSignal(dict) # final_results_dict
    verification_error = pyqtSignal(str) # error_message

    def __init__(self, torrent_filepath, data_root_directory):
        super().__init__()
        self.torrent_filepath = torrent_filepath
        self.data_root_directory = data_root_directory

    def run(self):
        try:
            # Define the progress callback function that the verifier will call
            def internal_progress_callback(current_piece, total_pieces, message):
                # Ensure percentage is calculated correctly, preventing division by zero
                if total_pieces > 0:
                    percentage = int((current_piece / total_pieces) * 100)
                else:
                    percentage = 0
                self.progress_updated.emit(percentage, message)

            # Call the verification function with the internal progress callback
            verification_results = verify_torrent_integrity(
                self.torrent_filepath,
                self.data_root_directory,
                progress_callback=internal_progress_callback
            )
            self.verification_finished.emit(verification_results)
        except Exception as e:
            # Emit an error signal if anything goes wrong in the worker thread
            self.verification_error.emit(f"An unexpected error occurred in the worker thread: {e}\n{traceback.format_exc()}")


class TorrentInfoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.torrent_filepath = None
        self.data_root_directory = None
        self.worker_thread = None # To hold our QThread instance
        self.worker = None        # To hold our QObject worker instance
        self.initUI()
        self.apply_styles() # Apply custom styles after UI initialization

    def initUI(self):
        self.setWindowTitle('TorInfo - Torrent Metadata & Integrity Verifier GUI')
        self.setGeometry(100, 100, 900, 700) # Slightly larger window

        main_layout = QVBoxLayout()

        # Tabs for Metadata and Verification
        self.tabs = QTabWidget()
        self.metadata_tab = QWidget()
        self.verification_tab = QWidget()

        self.tabs.addTab(self.metadata_tab, "Metadata")
        self.tabs.addTab(self.verification_tab, "Verify Integrity")

        self.setup_metadata_tab()
        self.setup_verification_tab()

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def setup_metadata_tab(self):
        layout = QVBoxLayout(self.metadata_tab)

        # Torrent File Selection
        self.torrent_path_label_meta = QLabel("No .torrent file selected.")
        self.torrent_path_label_meta.setWordWrap(True)
        
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(QLabel("Torrent File:"))
        file_selection_layout.addWidget(self.torrent_path_label_meta)
        
        select_button = QPushButton("Select .torrent File")
        select_button.clicked.connect(self.select_torrent_file_meta)
        file_selection_layout.addWidget(select_button)
        
        show_info_button = QPushButton("Show Info")
        show_info_button.clicked.connect(self.show_torrent_info)
        file_selection_layout.addWidget(show_info_button)
        
        layout.addLayout(file_selection_layout)

        # Output area
        self.metadata_display = QTextEdit()
        self.metadata_display.setReadOnly(True)
        self.metadata_display.setText("Torrent metadata will appear here.")
        layout.addWidget(self.metadata_display)

    def setup_verification_tab(self):
        layout = QVBoxLayout(self.verification_tab)

        # Torrent File Selection
        self.torrent_path_label_verify = QLabel("No .torrent file selected.")
        self.torrent_path_label_verify.setWordWrap(True)
        
        verify_torrent_selection_layout = QHBoxLayout()
        verify_torrent_selection_layout.addWidget(QLabel("Torrent File:"))
        verify_torrent_selection_layout.addWidget(self.torrent_path_label_verify)
        
        select_torrent_button = QPushButton("Select .torrent File")
        select_torrent_button.clicked.connect(self.select_torrent_file_verify)
        verify_torrent_selection_layout.addWidget(select_torrent_button)
        
        layout.addLayout(verify_torrent_selection_layout)

        # Data Folder Selection
        self.data_folder_label = QLabel("No data folder selected.")
        self.data_folder_label.setWordWrap(True)
        
        data_folder_selection_layout = QHBoxLayout()
        data_folder_selection_layout.addWidget(QLabel("Data Folder:"))
        data_folder_selection_layout.addWidget(self.data_folder_label)
        
        select_folder_button = QPushButton("Select Data Folder")
        select_folder_button.clicked.connect(self.select_data_folder)
        data_folder_selection_layout.addWidget(select_folder_button)
        
        layout.addLayout(data_folder_selection_layout)

        # Verify Button
        self.verify_button = QPushButton("Verify Integrity")
        self.verify_button.clicked.connect(self.start_verification)
        layout.addWidget(self.verify_button)

        # Progress Bar and Status Label
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to verify.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        # Output Area
        self.verification_display = QTextEdit()
        self.verification_display.setReadOnly(True)
        self.verification_display.setText("Verification report will appear here.")
        layout.addWidget(self.verification_display)
        

    # --- File Selection Methods ---
    def select_torrent_file_meta(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .torrent file", "", "Torrent Files (*.torrent);;All Files (*)")
        if file_path:
            self.torrent_filepath = file_path
            self.torrent_path_label_meta.setText(f"<b>Selected:</b> {os.path.basename(file_path)}")
            self.torrent_path_label_verify.setText(f"<b>Selected:</b> {os.path.basename(file_path)}")


    def select_torrent_file_verify(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .torrent file for verification", "", "Torrent Files (*.torrent);;All Files (*)")
        if file_path:
            self.torrent_filepath = file_path
            self.torrent_path_label_verify.setText(f"<b>Selected:</b> {os.path.basename(file_path)}")
            self.torrent_path_label_meta.setText(f"<b>Selected:</b> {os.path.basename(file_path)}")

    def select_data_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select data folder", "")
        if dir_path:
            self.data_root_directory = dir_path
            self.data_folder_label.setText(f"<b>Selected:</b> {dir_path}")


    # --- Metadata Display Method ---
    def show_torrent_info(self):
        if not self.torrent_filepath:
            QMessageBox.warning(self, "No Torrent Selected", "Please select a .torrent file first.")
            return

        try:
            metadata = get_torrent_metadata(self.torrent_filepath)
            if not metadata:
                self.metadata_display.setText("Failed to read torrent metadata. It might be corrupted or not a valid .torrent file.")
                return

            formatted_info = format_torrent_metadata_as_string(metadata)
            self.metadata_display.setText(formatted_info)
        except Exception as e:
            self.metadata_display.setText(f"Error processing torrent info: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Failed to read torrent info: {e}")

    # --- Verification Methods ---
    def start_verification(self):
        if not self.torrent_filepath:
            QMessageBox.warning(self, "Missing Input", "Please select a .torrent file.")
            return
        if not self.data_root_directory:
            QMessageBox.warning(self, "Missing Input", "Please select the data folder.")
            return

        # Prevent starting a new verification if one is already running
        if self.worker_thread is not None and self.worker_thread.isRunning():
            QMessageBox.information(self, "Verification In Progress", "A verification is already running. Please wait for it to complete.")
            return

        # Clear previous results and show progress elements
        self.verification_display.clear()
        self.status_label.setText("Starting verification...")
        self.status_label.show()
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.verify_button.setEnabled(False) # Disable button during verification

        # Create QThread and Worker
        # IMPORTANT: Pass 'self' as parent to worker and thread for better lifecycle management
        self.worker_thread = QThread(self) # Parent the QThread to the main window
        self.worker = VerificationWorker(self.torrent_filepath, self.data_root_directory)
        
        # Move worker to the thread
        self.worker.moveToThread(self.worker_thread)

        # Connect signals and slots
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.verification_finished.connect(self.handle_verification_finished)
        self.worker.verification_error.connect(self.handle_verification_error)
        
        # When worker finishes, quit its thread (important for QThread lifecycle)
        self.worker.verification_finished.connect(self.worker_thread.quit)
        self.worker.verification_error.connect(self.worker_thread.quit) # Also quit on error

        # Connect to our custom cleanup slot when the QThread finishes
        # This ensures 'self.worker_thread' and 'self.worker' are cleared only after the thread is done
        self.worker_thread.finished.connect(self._cleanup_worker_and_thread_references)

        # Ensure proper cleanup (deleteLater schedules deletion for next event loop iteration)
        # These are crucial and should be connected to the thread's finished signal
        self.worker_thread.finished.connect(self.worker.deleteLater) # Delete the worker QObject
        self.worker_thread.finished.connect(self.worker_thread.deleteLater) # Delete the QThread object itself

        # Start the thread
        self.worker_thread.start()

    def update_progress(self, percentage, message):
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)

    def handle_verification_finished(self, results):
        formatted_results_text = format_verification_results_as_string(results)
        self.verification_display.setText(formatted_results_text)
        
        # Hide progress elements and re-enable button
        self.progress_bar.hide()
        self.status_label.hide()
        self.verify_button.setEnabled(True)

        if results.get('status') == 'success':
            QMessageBox.information(self, "Verification Complete", "Torrent integrity successfully verified!")
        elif results.get('status') == 'failure':
            QMessageBox.warning(self, "Verification Complete", "Torrent integrity verification completed with mismatches.")
        else: # status is 'error'
             QMessageBox.critical(self, "Verification Error", "An error occurred during verification. See details below.")
        
    def handle_verification_error(self, error_message):
        self.verification_display.setText(f"Error during verification:\n{error_message}")
        
        # Hide progress elements and re-enable button
        self.progress_bar.hide()
        self.status_label.hide()
        self.verify_button.setEnabled(True)
        
        QMessageBox.critical(self, "Verification Error", "An unhandled error occurred during verification. Please check the report.")
        
    def _cleanup_worker_and_thread_references(self):
        """
        Slot to be called when the QThread finishes.
        Safely clears references to the worker and thread objects.
        """
        self.worker_thread = None
        self.worker = None

    def apply_styles(self):
        # Basic QSS (Qt Style Sheet) for a slightly prettier look
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0; /* Light gray background */
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QTabWidget::pane { /* The tab widget frame */
                border: 1px solid #c0c0c0;
                background-color: #ffffff; /* White background for tab content */
            }
            QTabWidget::tab-bar {
                left: 5px; /* move to the right */
            }
            QTabBar::tab {
                background: #e0e0e0; /* Gray tab background */
                border: 1px solid #c0c0c0;
                border-bottom-color: #c0c0c0; /* same as pane color */
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff; /* White for selected tab */
                border-color: #c0c0c0;
                border-bottom-color: #ffffff; /* make selected tab appear connected to the pane */
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50; /* Green */
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
            QPushButton:disabled {
                background-color: #a0a0a0; /* Grey when disabled */
                color: #e0e0e0;
            }
            QLabel {
                padding: 5px;
                color: #333;
            }
            QTextEdit {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                padding: 5px;
                background-color: #fdfdfd;
                font-family: "Consolas", "Courier New", monospace; /* Monospaced font for report */
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                text-align: center;
                background-color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: #007bff; /* Blue progress */
                border-radius: 5px;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TorrentInfoApp()
    ex.show()
    sys.exit(app.exec_())