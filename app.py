from flask import Flask, request, jsonify, send_file
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import os
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

# Créer une application Flask
app = Flask(__name__)
CORS(app)

# Configuration Selenium : fonction pour créer un driver
def creer_driver():
    options = Options()
    options.add_argument("--headless")  # Exécute Chrome en mode sans interface graphique
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options, executable_path='/path/to/chromedriver')  # Remplacez par le chemin vers votre driver
    return driver

# Fonction pour télécharger le contenu HTML d'une page, avec ou sans connexion
def recuperer_page_html(url):
    try:
        driver = creer_driver()
        driver.get(url)

        # Exemple : si une connexion est nécessaire, ajoutez le traitement ici
        if "login" in url:  # Vérifier si c'est une page de connexion
            username_field = driver.find_element(By.NAME, "username")  # Adaptez selon la page
            password_field = driver.find_element(By.NAME, "password")
            login_button = driver.find_element(By.NAME, "login")

            username_field.send_keys("votre_nom_utilisateur")
            password_field.send_keys("votre_mot_de_passe")
            login_button.click()
            time.sleep(3)  # Attendre que la page se charge

        # Attendre le chargement des éléments dynamiques (facultatif)
        time.sleep(3)

        # Récupérer le contenu HTML
        html_content = driver.page_source
        driver.quit()
        return html_content
    except Exception as e:
        print(f"Erreur lors de l'utilisation de Selenium : {e}")
        return None

# Fonction pour extraire les tables HTML et les convertir en DataFrames pandas
def extraire_tables_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')

    if not tables:
        print("Aucune table trouvée.")
        return None

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
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Veuillez fournir une URL valide."}), 400

    html_content = recuperer_page_html(url)
    if not html_content:
        return jsonify({"error": "Impossible de télécharger le contenu de l'URL."}), 500

    tables = extraire_tables_html(html_content)
    if not tables:
        return jsonify({"error": "Aucune table trouvée sur cette page."}), 404

    horodatage = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    nom_fichier = f"donnees-{horodatage}.xlsx"
    chemin_fichier = os.path.join("/tmp", nom_fichier)

    try:
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            for idx, table in enumerate(tables):
                table.to_excel(writer, sheet_name=f"Table_{idx+1}", index=False)

        download_url = f"{request.host_url}download/{nom_fichier}"
        return jsonify({
            "message": "Les données ont été exportées avec succès.",
            "download_link": download_url
        }), 200
    except Exception as e:
        print(f"Erreur lors de l'exportation : {e}")
        return jsonify({"error": f"Erreur lors de l'exportation des données : {str(e)}"}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join("/tmp", filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Fichier non trouvé."}), 404

@app.route('/')
def home():
    return "Bienvenue à l'API Flask avec Selenium !"

if __name__ == '__main__':
    app.run(debug=True)
