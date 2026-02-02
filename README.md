# 🧪 GUI Meta (TorInfo) — File & Torrent Integrity Toolkit (Archived)

A Python-based toolkit for **verifying downloaded files against torrent metadata**, with additional media-aware parsing and a GUI front-end.

This project is currently **on ice**, preserved as a functional and exploratory prototype.

---

⚠️ **LICENSE & USAGE NOTICE — READ FIRST**

This repository is **source-available for private technical evaluation and testing only**.

- ❌ No commercial use  
- ❌ No production use  
- ❌ No academic, institutional, or government use  
- ❌ No research, benchmarking, or publication  
- ❌ No redistribution, sublicensing, or derivative works  
- ❌ No independent development based on this code  

All rights remain exclusively with the author.  
Use of this software constitutes acceptance of the terms defined in **LICENSE.txt**.

---

## 🔍 What problem does this solve?

Large downloads fail quietly.

Files can:
- look complete but be corrupted
- match expected size but fail integrity
- partially download without obvious errors

This project was built to **prove file integrity**, not just assume it.

---

## 🔐 Core capabilities

- 📦 **Torrent-backed file verification**
  - Parse `.torrent` files (bencoding)
  - Extract piece length, hashes, and expected size
  - Verify downloaded files **piece-by-piece**
  - Detect:
    - incomplete downloads
    - truncated files
    - corrupted content
    - fully verified files

- 🧪 **Virtual test harness**
  - Generate dummy torrents and files
  - Simulate:
    - complete files
    - incomplete files
    - corrupted pieces
  - Validate verification logic safely

- 🎞️ **Media-aware helpers**
  - Movie / TV filename parsers
  - Media classification utilities
  - Designed to integrate verification with media libraries

- 🖥️ **GUI front-end (WIP)**
  - Intended to make verification accessible without CLI usage
  - Displays verification status and metadata

---

## 🧠 Why this is interesting

This is **not** a torrent client.

It’s a **verification engine**:
- decoupled from downloading
- usable after-the-fact
- suitable for auditing, archiving, or forensic inspection

The logic works just as well for:
- media libraries
- long-term archives
- integrity checking pipelines

---

## 🗂️ Project structure (conceptual)
```text
guimeta/
├── gui.py # GUI front-end (WIP)
├── main.py # Entry point
├── filetracker.py # File scanning helpers
├── base_parser.py # Shared parsing utilities
├── media_classifier.py # Movie / TV classification
├── movie_parser.py
├── tv_show_parser.py
├── torrent_verifier.py # Core verification logic
├── torrent_formatter.py # Output formatting
├── torinfo.py # Torrent metadata helpers
├── FileTester.py # Test harness
├── Torrent File VirtualTester.py
├── Torrent2File Verifier.py
└── Docs/
└── Program info.docx
```

---

## ▶️ Running it

### Requirements
- Python 3.x
- `bencoding`
  
```bash
  pip install bencoding
```
CLI verification example
```bash
python Torrent2File\ Verifier.py
```
(Test paths inside the script can be adjusted for real files.)

## ⚠️ Project status

Archived / Prototype

- Logic is functional and validated
- GUI is unfinished
- Some code duplication exists across early iterations
- No packaging or installer
- No automated test suite beyond built-in testers

This repo exists as a working snapshot, not a finished product.

## 💡 If revived later…

Clear next steps would be:

- unify all verification logic into a single core module
- remove duplicated verifier scripts
- add a persistent verification report format (JSON)
- finish GUI workflows
- integrate with media library scanners
- add unit tests for verifier edge cases

## Contribution Policy

Feedback, bug reports, and suggestions are welcome.

You may submit:

- Issues
- Design feedback
- Pull requests for review

However:

- Contributions do not grant any license or ownership rights
- The author retains full discretion over acceptance and future use
- Contributors receive no rights to reuse, redistribute, or derive from this code

---

## 📜 License
This project is not open-source.

It is licensed under a private evaluation-only license.
See LICENSE.txt for full terms.

🏷️ Status
On ice — but useful.

This project represents a practical attempt to bring trust and verifiability to downloaded files.
