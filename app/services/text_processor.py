class DummyTextProcessor:
    """Temporary text processor for development."""

    def process(self, text: str) -> dict:
        cleaned_text = text.strip()

        return {
            "text": cleaned_text,
            "character_count": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
        }
