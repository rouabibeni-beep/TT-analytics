#!/usr/bin/env python3
"""
Script d'installation automatique des templates
Crée tous les fichiers HTML nécessaires pour le dashboard TT Analytics
"""

import os
import sys

# Templates HTML
TEMPLATES = {
    'login.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Tunisie Télécom Analytics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0055A4 0%, #003a73 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 85, 164, 0.3);
            width: 100%;
            max-width: 420px;
            padding: 40px;
        }

        .logo-section {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo {
            font-size: 36px;
            font-weight: bold;
            color: #0055A4;
            margin-bottom: 10px;
        }

        .logo-subtitle {
            color: #666;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }

        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        input:focus {
            outline: none;
            border-color: #0055A4;
            box-shadow: 0 0 0 3px rgba(0, 85, 164, 0.1);
        }

        .error-message {
            background: #fee;
            border-left: 4px solid #E74C3C;
            color: #c33;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        button {
            width: 100%;
            padding: 12px;
            background: #0055A4;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }

        button:hover {
            background: #003a73;
        }

        .demo-credentials {
            background: #f0f8ff;
            border-left: 4px solid #FFD200;
            padding: 12px;
            border-radius: 4px;
            margin-top: 20px;
            font-size: 13px;
            color: #333;
        }

        .demo-credentials strong {
            color: #0055A4;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-section">
            <div class="logo">📊 TT Analytics</div>
            <div class="logo-subtitle">Tunisie Télécom - Dashboard d'Anomalies</div>
        </div>

        {% if error %}
        <div class="error-message">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <h2 style="margin-bottom: 25px; color: #333; font-size: 24px;">Connexion</h2>

            <div class="form-group">
                <label for="username">Nom d'utilisateur</label>
                <input type="text" id="username" name="username" required>
            </div>

            <div class="form-group">
                <label for="password">Mot de passe</label>
                <input type="password" id="password" name="password" required>
            </div>

            <button type="submit">Se connecter</button>

            <div class="demo-credentials">
                <strong>📝 Identifiants de test :</strong><br>
                User: <strong>demo</strong> | Pass: <strong>demo123</strong><br>
                Admin: <strong>admin</strong> | Pass: <strong>admin123</strong>
            </div>
        </form>
    </div>
</body>
</html>''',

    'dashboard.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Tunisie Télécom Analytics</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; }
        .navbar-brand { font-size: 24px; font-weight: bold; }
        .logout-btn { background: #FFD200; color: #0055A4; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; }
        .sidebar { width: 250px; background: white; height: calc(100vh - 80px); position: fixed; left: 0; top: 80px; border-right: 1px solid #e0e0e0; }
        .sidebar-menu { list-style: none; padding: 20px 0; }
        .sidebar-menu li a { display: block; padding: 15px 20px; color: #666; text-decoration: none; }
        .sidebar-menu li.active a { color: #0055A4; font-weight: 600; border-left: 4px solid #FFD200; background: #f9f9f9; }
        .main-content { margin-left: 250px; margin-top: 80px; padding: 40px; }
        .page-title { font-size: 32px; font-weight: bold; margin-bottom: 30px; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }
        .kpi-card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
        .kpi-label { font-size: 13px; color: #999; text-transform: uppercase; margin-bottom: 10px; }
        .kpi-value { font-size: 28px; font-weight: bold; color: #0055A4; }
        .content-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
        .section-title { font-size: 20px; font-weight: bold; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #FFD200; }
        .chart-container { position: relative; height: 400px; margin-bottom: 20px; }
        .anomalies-table { width: 100%; border-collapse: collapse; }
        .anomalies-table th { background: #f9f9f9; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e0e0e0; }
        .anomalies-table td { padding: 12px; border-bottom: 1px solid #e0e0e0; }
        .btn { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-right: 10px; }
        .btn-primary { background: #0055A4; color: white; }
        .btn-secondary { background: #FFD200; color: #0055A4; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="navbar-brand">📊 TT Analytics Dashboard</div>
        <form method="POST" action="{{ url_for('logout') }}" style="margin: 0;">
            <button type="submit" class="logout-btn">Déconnexion</button>
        </form>
    </div>

    <div class="sidebar">
        <ul class="sidebar-menu">
            <li class="active"><a href="#">🏠 Dashboard</a></li>
            <li><a href="{{ url_for('section_performance') }}">⚡ Performance</a></li>
            <li><a href="{{ url_for('section_security') }}">🔒 Sécurité</a></li>
            <li><a href="{{ url_for('section_details_db') }}">💾 Base de Données</a></li>
            <li><a href="{{ url_for('section_configuration') }}">⚙️ Configuration</a></li>
            <li><a href="{{ url_for('section_rapport') }}">📋 Rapports</a></li>
        </ul>
    </div>

    <div class="main-content">
        <h1 class="page-title">Dashboard Analytics</h1>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Anomalies</div>
                <div class="kpi-value" id="total-anomalies">-</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Critiques</div>
                <div class="kpi-value" id="critiques">-</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Uptime</div>
                <div class="kpi-value" id="uptime">-</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Erreurs (24h)</div>
                <div class="kpi-value" id="errors-24h">-</div>
            </div>
        </div>

        <div class="content-section">
            <h2 class="section-title">📈 Timeline Anomalies (24h)</h2>
            <div class="chart-container">
                <canvas id="timeline-chart"></canvas>
            </div>
        </div>

        <div class="content-section">
            <h2 class="section-title">🚨 Anomalies Détectées</h2>
            <table class="anomalies-table">
                <thead><tr><th>Heure</th><th>Type</th><th>Sévérité</th><th>Impact</th><th>Nombre</th></tr></thead>
                <tbody id="anomalies-body"></tbody>
            </table>
        </div>

        <div class="content-section">
            <button class="btn btn-primary" onclick="location.href='{{ url_for('export_pdf_rapport') }}'">📥 Télécharger Rapport PDF</button>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                const kpis = await fetch('{{ url_for("get_kpis") }}').then(r => r.json());
                document.getElementById('total-anomalies').textContent = kpis.total_anomalies;
                document.getElementById('critiques').textContent = kpis.critiques;
                document.getElementById('uptime').textContent = kpis.uptime;
                document.getElementById('errors-24h').textContent = kpis.errors_24h;

                const anomalies = await fetch('{{ url_for("get_anomalies") }}').then(r => r.json());
                let html = '';
                anomalies.forEach(a => {
                    html += `<tr><td>${a.time}</td><td>${a.type}</td><td>${a.severity}</td><td>${a.impact}</td><td>${a.count}</td></tr>`;
                });
                document.getElementById('anomalies-body').innerHTML = html;

                const timeline = await fetch('{{ url_for("get_timeline") }}').then(r => r.json());
                const ctx = document.getElementById('timeline-chart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timeline.map(t => t.time),
                        datasets: [{
                            label: 'Score Santé',
                            data: timeline.map(t => t.score),
                            borderColor: '#0055A4',
                            backgroundColor: 'rgba(0, 85, 164, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            } catch (error) {
                console.error('Erreur:', error);
            }
        }
        window.onload = loadData;
    </script>
</body>
</html>''',

    'error.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erreur - Tunisie Télécom Analytics</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .error-container { background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0, 85, 164, 0.3); max-width: 500px; padding: 60px 40px; text-align: center; }
        .error-code { font-size: 80px; font-weight: bold; color: #0055A4; margin-bottom: 20px; }
        .error-message { font-size: 24px; color: #333; margin-bottom: 20px; }
        .back-button { display: inline-block; background: #0055A4; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">{{ code }}</div>
        <div class="error-message">{{ message }}</div>
        <a href="{{ url_for('dashboard') }}" class="back-button">Accueil</a>
    </div>
</body>
</html>'''
}

SECTION_TEMPLATES = {
    'performance.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Performance - Tunisie Télécom Analytics</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; }
        .sidebar { width: 250px; background: white; height: calc(100vh - 80px); position: fixed; left: 0; top: 80px; border-right: 1px solid #e0e0e0; }
        .sidebar-menu li a { display: block; padding: 15px 20px; color: #666; text-decoration: none; }
        .sidebar-menu li.active a { color: #0055A4; font-weight: 600; border-left: 4px solid #FFD200; }
        .main-content { margin-left: 250px; margin-top: 80px; padding: 40px; }
        .back-link { color: #0055A4; text-decoration: none; font-weight: 600; margin-bottom: 20px; display: inline-block; }
        .content-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div>📊 TT Analytics Dashboard</div>
        <form method="POST" action="{{ url_for('logout') }}"><button type="submit" style="background: #FFD200; color: #0055A4; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Déconnexion</button></form>
    </div>
    <div class="sidebar">
        <ul style="list-style: none; padding: 20px 0;">
            <li><a href="{{ url_for('dashboard') }}">🏠 Dashboard</a></li>
            <li class="active"><a href="#">⚡ Performance</a></li>
            <li><a href="{{ url_for('section_security') }}">🔒 Sécurité</a></li>
            <li><a href="{{ url_for('section_details_db') }}">💾 Base de Données</a></li>
            <li><a href="{{ url_for('section_configuration') }}">⚙️ Configuration</a></li>
            <li><a href="{{ url_for('section_rapport') }}">📋 Rapports</a></li>
        </ul>
    </div>
    <div class="main-content">
        <a href="{{ url_for('dashboard') }}" class="back-link">← Retour</a>
        <h1 style="margin-bottom: 30px;">⚡ Analyse de Performance</h1>
        <div class="content-section">
            <h2 style="border-bottom: 2px solid #FFD200; padding-bottom: 15px; margin-bottom: 20px;">Métriques en Temps Réel</h2>
            <p>Temps de réponse moyen: <strong>245 ms</strong></p>
            <p>Taux d'erreur: <strong>0.15%</strong></p>
            <p>Disponibilité: <strong>99.7%</strong></p>
        </div>
    </div>
</body>
</html>''',

    'security.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Sécurité - Tunisie Télécom Analytics</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; }
        .sidebar { width: 250px; background: white; height: calc(100vh - 80px); position: fixed; left: 0; top: 80px; border-right: 1px solid #e0e0e0; }
        .sidebar-menu li a { display: block; padding: 15px 20px; color: #666; text-decoration: none; }
        .sidebar-menu li.active a { color: #0055A4; font-weight: 600; border-left: 4px solid #FFD200; }
        .main-content { margin-left: 250px; margin-top: 80px; padding: 40px; }
        .content-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div>📊 TT Analytics Dashboard</div>
        <form method="POST" action="{{ url_for('logout') }}"><button type="submit" style="background: #FFD200; color: #0055A4; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Déconnexion</button></form>
    </div>
    <div class="sidebar">
        <ul style="list-style: none; padding: 20px 0;">
            <li><a href="{{ url_for('dashboard') }}">🏠 Dashboard</a></li>
            <li><a href="{{ url_for('section_performance') }}">⚡ Performance</a></li>
            <li class="active"><a href="#">🔒 Sécurité</a></li>
            <li><a href="{{ url_for('section_details_db') }}">💾 Base de Données</a></li>
            <li><a href="{{ url_for('section_configuration') }}">⚙️ Configuration</a></li>
            <li><a href="{{ url_for('section_rapport') }}">📋 Rapports</a></li>
        </ul>
    </div>
    <div class="main-content">
        <h1 style="margin-bottom: 30px;">🔒 Analyse de Sécurité</h1>
        <div class="content-section">
            <h2 style="border-bottom: 2px solid #FFD200; padding-bottom: 15px; margin-bottom: 20px;">Score de Sécurité Global</h2>
            <div style="font-size: 48px; font-weight: bold; color: #27AE60; text-align: center; padding: 20px;">92/100 ✅</div>
            <p style="text-align: center; color: #666;">Excellent - Continuer la surveillance</p>
        </div>
    </div>
</body>
</html>''',

    'details_db.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Base de Données - Tunisie Télécom Analytics</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; }
        .sidebar { width: 250px; background: white; height: calc(100vh - 80px); position: fixed; left: 0; top: 80px; border-right: 1px solid #e0e0e0; }
        .sidebar-menu li a { display: block; padding: 15px 20px; color: #666; text-decoration: none; }
        .sidebar-menu li.active a { color: #0055A4; font-weight: 600; border-left: 4px solid #FFD200; }
        .main-content { margin-left: 250px; margin-top: 80px; padding: 40px; }
        .content-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div>📊 TT Analytics Dashboard</div>
        <form method="POST" action="{{ url_for('logout') }}"><button type="submit" style="background: #FFD200; color: #0055A4; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Déconnexion</button></form>
    </div>
    <div class="sidebar">
        <ul style="list-style: none; padding: 20px 0;">
            <li><a href="{{ url_for('dashboard') }}">🏠 Dashboard</a></li>
            <li><a href="{{ url_for('section_performance') }}">⚡ Performance</a></li>
            <li><a href="{{ url_for('section_security') }}">🔒 Sécurité</a></li>
            <li class="active"><a href="#">💾 Base de Données</a></li>
            <li><a href="{{ url_for('section_configuration') }}">⚙️ Configuration</a></li>
            <li><a href="{{ url_for('section_rapport') }}">📋 Rapports</a></li>
        </ul>
    </div>
    <div class="main-content">
        <h1 style="margin-bottom: 30px;">💾 Détails Base de Données</h1>
        <div class="content-section">
            <h2 style="border-bottom: 2px solid #FFD200; padding-bottom: 15px; margin-bottom: 20px;">Informations Générales</h2>
            <p>Taille Totale: <strong>2.4 GB</strong></p>
            <p>Tables Actives: <strong>47</strong></p>
            <p>Enregistrements: <strong>5.2M</strong></p>
            <p>Dernière Sauvegarde: <strong>Il y a 2h</strong></p>
        </div>
    </div>
</body>
</html>''',

    'configuration.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Configuration - Tunisie Télécom Analytics</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; }
        .sidebar { width: 250px; background: white; height: calc(100vh - 80px); position: fixed; left: 0; top: 80px; border-right: 1px solid #e0e0e0; }
        .sidebar-menu li a { display: block; padding: 15px 20px; color: #666; text-decoration: none; }
        .sidebar-menu li.active a { color: #0055A4; font-weight: 600; border-left: 4px solid #FFD200; }
        .main-content { margin-left: 250px; margin-top: 80px; padding: 40px; }
        .content-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div>📊 TT Analytics Dashboard</div>
        <form method="POST" action="{{ url_for('logout') }}"><button type="submit" style="background: #FFD200; color: #0055A4; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Déconnexion</button></form>
    </div>
    <div class="sidebar">
        <ul style="list-style: none; padding: 20px 0;">
            <li><a href="{{ url_for('dashboard') }}">🏠 Dashboard</a></li>
            <li><a href="{{ url_for('section_performance') }}">⚡ Performance</a></li>
            <li><a href="{{ url_for('section_security') }}">🔒 Sécurité</a></li>
            <li><a href="{{ url_for('section_details_db') }}">💾 Base de Données</a></li>
            <li class="active"><a href="#">⚙️ Configuration</a></li>
            <li><a href="{{ url_for('section_rapport') }}">📋 Rapports</a></li>
        </ul>
    </div>
    <div class="main-content">
        <h1 style="margin-bottom: 30px;">⚙️ Configuration Système</h1>
        <div class="content-section">
            <h2 style="border-bottom: 2px solid #FFD200; padding-bottom: 15px; margin-bottom: 20px;">Paramètres Généraux</h2>
            <p>Mode Debug: <strong>Désactivé</strong></p>
            <p>Alertes Email: <strong>Activé</strong></p>
            <p>Audit Logging: <strong>Activé</strong></p>
        </div>
    </div>
</body>
</html>''',

    'rapport.html': '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapports - Tunisie Télécom Analytics</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #0055A4 0%, #003a73 100%); color: white; padding: 20px 40px; display: flex; justify-content: space-between; }
        .sidebar { width: 250px; background: white; height: calc(100vh - 80px); position: fixed; left: 0; top: 80px; border-right: 1px solid #e0e0e0; }
        .sidebar-menu li a { display: block; padding: 15px 20px; color: #666; text-decoration: none; }
        .sidebar-menu li.active a { color: #0055A4; font-weight: 600; border-left: 4px solid #FFD200; }
        .main-content { margin-left: 250px; margin-top: 80px; padding: 40px; }
        .content-section { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div>📊 TT Analytics Dashboard</div>
        <form method="POST" action="{{ url_for('logout') }}"><button type="submit" style="background: #FFD200; color: #0055A4; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Déconnexion</button></form>
    </div>
    <div class="sidebar">
        <ul style="list-style: none; padding: 20px 0;">
            <li><a href="{{ url_for('dashboard') }}">🏠 Dashboard</a></li>
            <li><a href="{{ url_for('section_performance') }}">⚡ Performance</a></li>
            <li><a href="{{ url_for('section_security') }}">🔒 Sécurité</a></li>
            <li><a href="{{ url_for('section_details_db') }}">💾 Base de Données</a></li>
            <li><a href="{{ url_for('section_configuration') }}">⚙️ Configuration</a></li>
            <li class="active"><a href="#">📋 Rapports</a></li>
        </ul>
    </div>
    <div class="main-content">
        <h1 style="margin-bottom: 30px;">📋 Gestion des Rapports</h1>
        <div class="content-section">
            <h2 style="border-bottom: 2px solid #FFD200; padding-bottom: 15px; margin-bottom: 20px;">Rapports Disponibles</h2>
            <p>✅ Rapport Anomalies - Mai 2026 | <a href="{{ url_for('export_pdf_rapport') }}" style="color: #0055A4;">Télécharger PDF</a></p>
            <p>✅ Rapport Performance - Semaine 18</p>
            <p>✅ Rapport Sécurité - Q2 2026</p>
        </div>
    </div>
</body>
</html>'''
}

def setup_templates():
    """Crée la structure des templates"""
    print("🔧 Création de la structure des templates...")
    
    # Créer le dossier templates
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("✅ Dossier 'templates' créé")
    
    # Créer le dossier sections
    if not os.path.exists('templates/sections'):
        os.makedirs('templates/sections')
        print("✅ Dossier 'templates/sections' créé")
    
    # Créer les fichiers principaux
    for filename, content in TEMPLATES.items():
        filepath = os.path.join('templates', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {filename} créé")
    
    # Créer les fichiers des sections
    for filename, content in SECTION_TEMPLATES.items():
        filepath = os.path.join('templates/sections', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ sections/{filename} créé")
    
    print("\n" + "="*50)
    print("🎉 SUCCÈS ! Tous les templates ont été créés")
    print("="*50)
    print("\n📂 Structure créée:")
    print("templates/")
    print("├── login.html")
    print("├── dashboard.html")
    print("├── error.html")
    print("└── sections/")
    print("    ├── performance.html")
    print("    ├── security.html")
    print("    ├── details_db.html")
    print("    ├── configuration.html")
    print("    └── rapport.html")
    print("\n🚀 Vous pouvez maintenant lancer: python app.py")

if __name__ == '__main__':
    setup_templates()
