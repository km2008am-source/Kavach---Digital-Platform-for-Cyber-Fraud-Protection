# M1 owns language/service.py. Pass-through stand-in with the frozen signature.
async def translate(text: str, src: str, tgt: str) -> str:
    return text
