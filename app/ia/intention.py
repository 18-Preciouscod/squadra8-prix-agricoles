"""Comprend l'intention avec GPT-4.1 mini (sortie JSON stricte). Jamais de prix.

Responsable : Gopal.
"""

# TODO G4 : appel Azure OpenAI, validation Pydantic, repli sur les règles
#           si erreur ou délai > 3 s.


def comprendre(texte: str) -> dict:
    """Retourne l'intention, le produit et le marché, sans aucun prix. À implémenter."""
    raise NotImplementedError("TODO G4 : compréhension de l'intention")
