import re
from base_parser import BaseParser

class TvShowParser(BaseParser):
    def __init__(self):
        super().__init__()
        print("INFO: TvShowParser instance created.")

    def parse_tv_show_filename(self, filename_without_ext):
        """
        Parses a TV show filename based on common naming conventions (SxxExx).

        Args:
            filename_without_ext (str): The filename string without its extension.

        Returns:
            dict: Parsed TV show metadata.
        """
        parsed_data = {
            "type": "TV Show",
            "title": filename_without_ext, # Default title
            "season": None,
            "episode": None,
            "episode_title": None,
            "resolution": None,
            "source": None,
            "video_format": None,
            "audio_format": None,
            "group_tag": None,
            "original_filename": filename_without_ext
        }

        # 1. Extract Season and Episode first using helper from BaseParser
        season_num, episode_str, sxe_start, sxe_end = self.extract_season_episode_from_string(filename_without_ext)

        if season_num is not None and episode_str is not None:
            parsed_data["season"] = season_num
            parsed_data["episode"] = episode_str

            # Title is the part before SxxExx, cleaned of any tags
            raw_title_part = filename_without_ext[:sxe_start].strip()
            parsed_data["title"] = self._clean_string_of_all_tags(raw_title_part)

            # Episode title is the part after SxxExx, cleaned of any tags
            raw_episode_title_part = filename_without_ext[sxe_end:].strip()
            parsed_data["episode_title"] = self._clean_string_of_all_tags(raw_episode_title_part)

        else:
            # Fallback for numerical patterns like "201" if SxxExx not found
            # Ensure it's a 3-digit number and not a typical year.
            num_match = re.search(r'\b(\d{1,2})(\d{2})\b', filename_without_ext)
            if num_match and len(num_match.group(0)) == 3 and not (1900 <= int(num_match.group(0)) <= 2099): # Avoid matching common years
                parsed_data["season"] = int(num_match.group(1))
                parsed_data["episode"] = num_match.group(2)
                raw_title_part = filename_without_ext[:num_match.start()].strip()
                parsed_data["title"] = self._clean_string_of_all_tags(raw_title_part)
                parsed_data["episode_title"] = None # Harder to extract with this format

        # Extract other common metadata from the FULL original filename
        group_match = self.group_tag_pattern.search(filename_without_ext)
        if group_match: parsed_data["group_tag"] = group_match.group(1)

        resolution_match = self.resolution_pattern.search(filename_without_ext)
        if resolution_match: parsed_data["resolution"] = resolution_match.group(0)

        source_match = self.source_pattern.search(filename_without_ext)
        if source_match: parsed_data["source"] = source_match.group(0)

        video_match = self.video_format_pattern.search(filename_without_ext)
        if video_match: parsed_data["video_format"] = video_match.group(0)

        audio_match = self.audio_format_pattern.search(filename_without_ext)
        if audio_match: parsed_data["audio_format"] = audio_match.group(0)

        # If title wasn't definitively set by SxxExx or 201 pattern, clean the whole filename as title
        if not parsed_data["title"]:
            parsed_data["title"] = self._clean_string_of_all_tags(filename_without_ext)

        # Final normalization ensures consistency
        parsed_data["title"] = self._normalize_string_for_comparison(parsed_data["title"])
        if parsed_data["episode_title"]:
            parsed_data["episode_title"] = self._normalize_string_for_comparison(parsed_data["episode_title"])

        return parsed_data
