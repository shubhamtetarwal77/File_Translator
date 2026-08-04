"""
Translation Engine Wrapper
Supports Google Translate and MyMemory (free), with optional API-key services.
Includes caching, rate limiting, and chunking for large texts.
"""

import time
from deep_translator import (
    GoogleTranslator,
    MyMemoryTranslator,
)

# Simple in-memory translation cache
_translation_cache = {}


class TranslationEngine:
    """Wraps deep-translator with caching, chunking, and rate limiting."""

    ENGINES = ['google', 'mymemory']

    # Maximum characters per request (conservative limits)
    CHUNK_LIMITS = {
        'google': 4500,
        'mymemory': 4500,
    }

    def __init__(self, engine='google', source_lang='auto', target_lang='en'):
        if engine not in self.ENGINES:
            raise ValueError(f"Unsupported engine: {engine}. Choose from {self.ENGINES}")
        if target_lang == 'auto':
            raise ValueError("Target language cannot be 'auto'. Please specify a language.")

        self.engine = engine
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.chunk_limit = self.CHUNK_LIMITS.get(engine, 4500)
        self._request_count = 0
        self._init_translator()

    def _init_translator(self):
        """Initialize the underlying translator instance."""
        if self.engine == 'google':
            self._translator = GoogleTranslator(
                source=self.source_lang,
                target=self.target_lang
            )
        elif self.engine == 'mymemory':
            self._translator = MyMemoryTranslator(
                source=self.source_lang if self.source_lang != 'auto' else 'auto',
                target=self.target_lang
            )

    def translate_text(self, text):
        """
        Translate a single string of text.
        Returns original text if translation fails or text is empty.
        Uses caching to avoid re-translating identical strings.
        """
        if not text or not text.strip():
            return text

        # Check cache
        cache_key = (self.engine, self.source_lang, self.target_lang, text)
        if cache_key in _translation_cache:
            return _translation_cache[cache_key]

        # Handle long text by chunking
        if len(text) > self.chunk_limit:
            result = self._translate_long_text(text)
        else:
            result = self._translate_single(text)

        # Cache the result
        _translation_cache[cache_key] = result
        return result

    def _translate_single(self, text):
        """Translate a single chunk of text with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self._translator.translate(text)
                self._request_count += 1

                # Small delay to avoid rate limiting
                if self._request_count % 10 == 0:
                    time.sleep(0.5)

                return result if result else text

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                else:
                    print(f"[Translator] Failed after {max_retries} attempts: {e}")
                    return text

    def _translate_long_text(self, text):
        """Split long text into chunks at sentence boundaries and translate each."""
        chunks = self._split_into_chunks(text)
        translated_chunks = []

        for chunk in chunks:
            translated = self._translate_single(chunk)
            translated_chunks.append(translated)

        return ' '.join(translated_chunks)

    def _split_into_chunks(self, text, max_chars=None):
        """Split text into chunks at sentence boundaries, respecting max_chars."""
        if max_chars is None:
            max_chars = self.chunk_limit

        if len(text) <= max_chars:
            return [text]

        chunks = []
        current_chunk = ""

        # Try splitting at sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n', '。', '！', '？']

        i = 0
        while i < len(text):
            char = text[i]
            current_chunk += char

            # Check if we hit a sentence boundary
            is_boundary = False
            for ending in sentence_endings:
                if current_chunk.endswith(ending):
                    is_boundary = True
                    break

            # Also split at newlines
            if char == '\n' and len(current_chunk.strip()) > 0:
                is_boundary = True

            if is_boundary and len(current_chunk) >= max_chars * 0.5:
                if len(current_chunk) > max_chars:
                    # Force split at max_chars
                    chunks.append(current_chunk[:max_chars])
                    current_chunk = current_chunk[max_chars:]
                else:
                    chunks.append(current_chunk)
                    current_chunk = ""
            elif len(current_chunk) >= max_chars:
                # Force split at max_chars
                chunks.append(current_chunk[:max_chars])
                current_chunk = current_chunk[max_chars:]

            i += 1

        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks

    @property
    def request_count(self):
        return self._request_count

    @staticmethod
    def clear_cache():
        """Clear the translation cache."""
        _translation_cache.clear()