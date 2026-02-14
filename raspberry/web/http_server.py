"""
http_server.py
--------------
Serveur HTTP statique pour le cockpit AxisOne.

Version PREMIUM :
- Sert automatiquement tous les fichiers du dossier www/
- Page par défaut : index.html
- Architecture cockpit-driven
"""

import os
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Répertoire du cockpit web
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "www")


class CockpitHandler(SimpleHTTPRequestHandler):
    """
    Handler HTTP servant les fichiers du cockpit (www/).
    """

    def translate_path(self, path):
        """
        Redéfinit la résolution des chemins pour pointer vers www/.
        """
        # Nettoyage du chemin
        path = path.lstrip("/")

        # Page par défaut
        if not path:
            path = "index.html"

        return os.path.join(WEB_DIR, path)

    def log_message(self, format, *args):
        """
        Supprime les logs HTTP bruyants.
        """
        pass


def start_http_server():
    """
    Démarre le serveur HTTP statique sur le port 8080.
    """
    server = HTTPServer(("0.0.0.0", 8080), CockpitHandler)
    print(f"[HTTP] Cockpit disponible sur http://<ip_du_pi>:8080")
    server.serve_forever()