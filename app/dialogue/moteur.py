"""Machine à états du dialogue : ne connaît pas le canal (simulateur ou Twilio).

Elle reçoit un événement (bip, touche, audio) et renvoie un « tour »
(ce qu'il faut dire et ce qu'on attend).

Responsable : Guillaume.
"""

# TODO I1 : états (accueil, produit, menu, touches 1-4, silence, erreur) et transitions.


def traiter(evenement: dict) -> dict:
    """Traite un événement et renvoie un tour. À implémenter."""
    raise NotImplementedError("TODO I1 : moteur de dialogue")
