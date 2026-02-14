from googletrans import Translator
import asyncio

class TextTranslator:
    def __init__(self):
        self.translator = Translator()

    async def translate_text(self, text, dest_lang):
        try:
            result = await self.translator.translate(text, dest=dest_lang)
            return result.text
        except Exception as e:
            print(f"Translation error for '{text}': {e}")
            return text

    async def translate_batch(self, texts, dest_lang="es"):
        tasks = [self.translate_text(text, dest_lang) for text in texts]
        return await asyncio.gather(*tasks)

    def translate_sync(self, text, dest_lang):
        # Helper for synchronous calls if needed, though async is preferred
        return asyncio.run(self.translate_text(text, dest_lang))
