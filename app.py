from flask import Flask, request, jsonify, send_file
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
            print(f"Erreur lors du téléchargement : HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Erreur lors du téléchargement de l'URL : {e}")
        return None

# Fonction pour extraire les tables HTML et les convertir en DataFrames pandas
def extraire_tables_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        print("Aucune table trouvée.")
        return None  # Aucune table trouvée

    dataframes = []
    for table in tables:
        try:
            df = pd.read_html(str(table))[0]  # Convertir la table HTML en DataFrame
            dataframes.append(df)
        except Exception as e:
            print(f"Erreur lors de la conversion de la table : {e}")
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
    
    # Pour rendre accessible le fichier dans le répertoire de Render, on utilise /mnt/data
    chemin_fichier = f"/mnt/data/{nom_fichier}"

    # Exporter les tables dans un fichier Excel
    try:
        print(f"Début de l'exportation vers le fichier Excel : {chemin_fichier}")
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            for idx, table in enumerate(tables):
                print(f"Exportation de la table {idx+1}...")
                table.to_excel(writer, sheet_name=f"Table_{idx+1}", index=False)
        
        print(f"Exportation réussie : {chemin_fichier}")
        return send_file(chemin_fichier, as_attachment=True, download_name=nom_fichier)

    except Exception as e:
        print(f"Erreur lors de l'exportation : {e}")
        return jsonify({"error": "Erreur lors de l'exportation des données."}), 500

# Page d'accueil pour tester si l'API est fonctionnelle
@app.route('/')
def home():
    return "Bienvenue à l'API Flask ! Utilisez l'endpoint '/extract-tables' avec une requête POST pour extraire des tables HTML."

# Démarrer le serveur Flask
if __name__ == '__main__':
    app.run(debug=True)
