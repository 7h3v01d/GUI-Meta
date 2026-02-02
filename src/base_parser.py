import re
import os

class BaseParser:
    def __init__(self):
        # print("INFO: BaseParser instance created. Initializing common regex patterns.")
        self.year_pattern = re.compile(r'\b(\d{4})\b')
        self.resolution_pattern = re.compile(r'\b(480p|720p|1080p|1440p|2160p|4k|8k)\b', re.IGNORECASE)
        self.source_pattern = re.compile(r'\b(WEB-DL|WEBRip|BluRay|BDRip|DVDRip|HDRip|HDTV|DVD|VOD|DDC|CAM|TS)\b', re.IGNORECASE)
        self.video_format_pattern = re.compile(r'\b(x264|x265|HEVC|H\.264|H\.265|VP9|AV1|XviD|DivX)\b', re.IGNORECASE)
        self.audio_format_pattern = re.compile(r'\b(AC3|DTS|DTS-HD|TrueHD|Atmos|DD5\.1|AAC|MP3)\b', re.IGNORECASE) # Fixed DD5.1
        self.group_tag_pattern = re.compile(r'\[?([A-Za-z0-9_\.\-]+)\]?$', re.IGNORECASE) # Fixed dot and hyphen escaping
        self.version_pattern = re.compile(r'\b(PROPER|REPACK|RERIP|EXTENDED|DIRECTORS\.\?CUT|UNCUT|UNRATED)\b', re.IGNORECASE) # Fixed dot escaping


        # Comprehensive list of all patterns that represent "metadata" (not part of main title/episode title)
        # IMPORTANT: Removed the outer \b(?:...) from these internal patterns for consistent wrapping in the list comprehension.
        self.all_release_tag_patterns_raw = [
            r'[Ss]\d{1,2}[Ee](\d{1,2}(?:-\d{1,2})?)', # SxxExx pattern (still needs inner non-capturing group)
            r'\d{1,2}\d{2}', # 201-style for TV shows (e.g., S02E01 is 201)
            r'\d{4}', # Year
            r'480p|720p|1080p|1440p|2160p|4k|8k', # Resolutions
            r'WEB-DL|WEBRip|BluRay|BDRip|DVDRip|HDRip|HDTV|DVD|VOD|DDC|CAM|TS', # Sources
            r'x264|x265|HEVC|H\.264|H\.265|VP9|AV1|XviD|DivX', # Video formats
            r'AC3|DTS|DTS-HD|TrueHD|Atmos|DD5\.1|AAC|MP3', # Audio formats (dot escaped)
            r'PROPER|REPACK|RERIP|EXTENDED|DIRECTORS\.\?CUT|UNCUT|UNRATED', # Versions/Cuts (dot escaped)
            r'Multi|Dual|Eng|Jpn|Ger|Fre|Rus|Spa|Ita|Kor|Chi', # Language tags
            r'Sub|Dub|Retail|Subs|Dubs', # Subtitle/Dubbing tags
            r'NF|AMZN|HULU|WEB|iTunes|CR', # Streaming Service Tags
            r'COMPLETE|COLLECTION|SEASON|PACK', # Collection/Season indicators
            r'\[[^\]]+\]', # Anything in square brackets (e.g., [GROUP]) - keeps its literal brackets
            r'\([^)]+\)', # Anything in parentheses (e.g., (2020)) - keeps its literal parentheses
            r'[0-9A-Fa-f]{8}', # Common hash values
            r'Internal', # Internal release
            r'DD[0-9]\.[0-9]|DD[0-9]|DDP', # Dolby Digital patterns
            r'AAC2\.0|AAC5\.1', # AAC channel configurations
            r'HDR|DV', # HDR types
            r'xvid|divx|mp3|avi|mkv|mp4|mov|flac|m4a|srt|ass', # Common file/codec extensions
            r'V2|V3|FIXED', # Versioning
            r'UHD|HD|SD', # Quality indicators
            r'FANSUB|VOSTFR|ITA|JAP' # Fan Sub/Dub specifics
        ]
        # Compile these for efficiency with consistent wrapping
        # Now each `p` itself should be a simpler pattern that is then wrapped with \b(?:...)\b.
        self.compiled_release_tag_patterns = [re.compile(r'\b(?:' + p + r')\b', re.IGNORECASE) for p in self.all_release_tag_patterns_raw]

    @staticmethod
    def _normalize_string_for_comparison(text):
        """
        Normalizes a string (like a title or search term) for robust comparison:
        - Converts to lowercase.
        - Replaces common separators (dots, underscores, hyphens) with spaces.
        - Collapses multiple spaces into a single space and strips leading/trailing spaces.
        """
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[._-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_season_episode_from_string(text):
        """
        Extracts SxxExx pattern from a string (e.g., "S01E02", "s1e2", "s01e02-e03").
        Returns (season_int, episode_str, match_start_index, match_end_index) if found, else (None, None, -1, -1).
        The indices help in splitting the string accurately.
        """
        match = re.search(r'\b[Ss](\d{1,2})[Ee](\d{1,2}(?:-\d{1,2})?)\b', text, re.IGNORECASE)
        if match:
            try:
                season = int(match.group(1))
            except ValueError:
                season = None
            episode = match.group(2)
            return season, episode, match.start(), match.end()
        return None, None, -1, -1

    def _clean_string_of_all_tags(self, text):
        """Removes all known release tags from a string, then normalizes."""
        cleaned_text = text
        for pattern in self.compiled_release_tag_patterns:
            cleaned_text = pattern.sub(' ', cleaned_text)
        return self._normalize_string_for_comparison(cleaned_text)

