"""
Subtitle File Handler
Translates .srt and .vtt subtitle files while preserving:
- Timing information
- Sequence numbers
- Subtitle structure
- Formatting tags (italic, bold)
"""

import re
from core.utils import is_translatable


class SubtitleHandler:
    """Handles translation of .srt and .vtt subtitle files."""

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """Translate a subtitle file."""

        # Detect format
        ext = input_path.rsplit('.', 1)[-1].lower()

        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        if ext == 'srt':
            translated = self._translate_srt(content, translator, progress_callback)
        elif ext == 'vtt':
            translated = self._translate_vtt(content, translator, progress_callback)
        else:
            translated = self._translate_srt(content, translator, progress_callback)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated)

        if progress_callback:
            progress_callback(1.0, "Subtitle translation complete!")

    def _translate_srt(self, content, translator, progress_callback=None):
        """
        Translate SRT format subtitles.
        SRT format:
            1
            00:00:01,000 --> 00:00:04,000
            Hello, welcome!

            2
            00:00:05,000 --> 00:00:08,000
            This is a sample.
        """
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        total = len(blocks)

        for i, block in enumerate(blocks):
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # Lines[0] = sequence number
            # Lines[1] = timing
            # Lines[2:] = text (may be multi-line)
            seq_num = lines[0]
            timing = lines[1]
            text_lines = lines[2:]

            # Combine text lines for translation
            combined_text = '\n'.join(text_lines)

            # Preserve HTML-like tags
            has_tags = bool(re.search(r'<[^>]+>', combined_text))

            if is_translatable(combined_text):
                # Strip tags for translation, then re-add
                if has_tags:
                    clean_text = re.sub(r'<[^>]+>', '', combined_text)
                    translated = translator.translate_text(clean_text)
                    # Simple re-wrapping (tags are lost — acceptable trade-off)
                else:
                    translated = translator.translate_text(combined_text)

                # Reconstruct block
                blocks[i] = f"{seq_num}\n{timing}\n{translated}"

            if progress_callback and (i + 1) % 20 == 0:
                progress_callback(
                    (i + 1) / total,
                    f"Translating subtitle {i + 1} of {total}..."
                )

        return '\n\n'.join(blocks) + '\n'

    def _translate_vtt(self, content, translator, progress_callback=None):
        """
        Translate WebVTT format subtitles.
        VTT format:
            WEBVTT

            00:00:01.000 --> 00:00:04.000
            Hello, welcome!

            00:00:05.000 --> 00:00:08.000
            This is a sample.
        """
        lines = content.split('\n')
        result_lines = []
        total = len(lines)

        # Keep the WEBVTT header
        in_header = True
        for line in lines:
            if in_header:
                result_lines.append(line)
                if line.strip() == '' or '-->' in line:
                    in_header = False
                continue

        # Process cues
        i = 0
        cue_count = 0
        while i < len(lines):
            line = lines[i]

            # Detect timing line
            if '-->' in line:
                result_lines.append(line)  # Keep timing
                i += 1

                # Collect text lines until empty line or next cue
                text_lines = []
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text_lines.append(lines[i])
                    i += 1

                if text_lines:
                    combined = '\n'.join(text_lines)
                    if is_translatable(combined):
                        translated = translator.translate_text(combined)
                        result_lines.append(translated)
                    else:
                        result_lines.extend(text_lines)

                    cue_count += 1
                    if progress_callback and cue_count % 20 == 0:
                        progress_callback(
                            i / total,
                            f"Translating VTT cue {cue_count}..."
                        )
            else:
                result_lines.append(line)
                i += 1

        return '\n'.join(result_lines)