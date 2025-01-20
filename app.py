# Importer les bibliothèques nécessaires
from flask import Flask, request, jsonify
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Créer une application Flask
app = Flask(__name__)

# Fonction pour télécharger le contenu HTML depuis une URL
def recuperer_page_html(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")
        return None

# Fonction pour extraire les tables HTML et les convertir en DataFrames pandas
def extraire_tables_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        return None  # Aucune table trouvée

    dataframes = []
    for table in tables:
        try:
            df = pd.read_html(str(table))[0]  # Convertir la table HTML en DataFrame
            dataframes.append(df)
        except Exception as e:
            print(f"Erreur lors de la conversion : {e}")
            continue
    
    return dataframes

# Route principale pour extraire des tables et les exporter en Excel
@app.route('/extract-tables', methods=['POST'])
def extract_tables():
    # Récupérer les données JSON envoyées dans la requête POST
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "Veuillez fournir une URL valide."}), 400

    # Télécharger la page HTML
    html_content = recuperer_page_html(url)
    if not html_content:
        return jsonify({"error": "Impossible de télécharger le contenu de l'URL."}), 500

    # Extraire les tables
    tables = extraire_tables_html(html_content)
    if not tables:
        return jsonify({"error": "Aucune table trouvée sur cette page."}), 404

    # Générer le nom du fichier Excel avec horodatage
    horodatage = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    nom_fichier = f"donnees-{horodatage}.xlsx"
    chemin_fichier = os.path.join(os.path.expanduser("~/Documents"), nom_fichier)

    # Exporter les tables dans un fichier Excel
    try:
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            for idx, table in enumerate(tables):
                table.to_excel(writer, sheet_name=f"Table_{idx+1}", index=False)
        
        return jsonify({
            "message": "Les données ont été exportées avec succès.",
            "file_path": chemin_fichier
        }), 200
    except Exception as e:
        print(f"Erreur lors de l'exportation : {e}")
        return jsonify({"error": "Erreur lors de l'exportation des données."}), 500

# Route d'accueil pour vérifier que le serveur fonctionne
@app.route('/')
def home():
    return "Bienvenue à l'API Flask ! Utilisez l'endpoint '/extract-tables' avec une requête POST pour extraire des tables HTML."

# Démarrer le serveur Flask
if __name__ == '__main__':
    app.run(debug=True)
