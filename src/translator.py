from deep_translator import GoogleTranslator
import asyncio

class TextTranslator:
    def __init__(self):
        # No persistent session needed like googletrans
        pass

    async def translate_text(self, text, dest_lang):
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: GoogleTranslator(source="auto", target=dest_lang).translate(text)
            )
            return result
        except Exception as e:
            print(f"Translation error for '{text}': {e}")
            return text

    async def translate_batch(self, texts, dest_lang="es"):
        tasks = [self.translate_text(text, dest_lang) for text in texts]
        return await asyncio.gather(*tasks)

    def translate_sync(self, text, dest_lang):
        return GoogleTranslator(source="auto", target=dest_lang).translate(text)