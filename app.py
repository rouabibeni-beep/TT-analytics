"""
═══════════════════════════════════════════════════════════════
  DASHBOARD ANALYTICS TUNISIE TÉLÉCOM — ÉTAPE 5 MODERNISÉE
  Framework : Flask + SQLite (authentification)
  Charte graphique : Tunisie Télécom (Bleu #0055A4 + Jaune #FFD200)
  Version : 2.0 — Enterprise Ready
═══════════════════════════════════════════════════════════════
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
import base64

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TT-ANALYTICS-2026-SECURE-KEY-CHANGE-IN-PROD'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tt_analytics.db'
# HTTPS only: set SESSION_COOKIE_SECURE=1 when serving over TLS
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '').lower() in ('1', 'true', 'yes')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

db = SQLAlchemy(app)


@app.template_filter('score_color')
def score_color_filter(score):
    score = float(score or 0)
    if score >= 80:
        return '#E74C3C'
    if score >= 65:
        return '#F39C12'
    if score >= 45:
        return '#3498DB'
    return '#27AE60'


@app.template_filter('severity_css')
def severity_css_filter(severity):
    return f'severity-{str(severity or "normal").lower()}'


# Couleurs Tunisie Télécom
TT_COLORS = {
    'primary': '#0055A4',
    'secondary': '#FFD200',
    'danger': '#E74C3C',
    'success': '#27AE60',
    'warning': '#F39C12',
    'info': '#3498DB',
    'light': '#ECF0F1',
    'dark': '#2C3E50'
}

# Données simulées (à remplacer par features.csv / resultats_modele.csv)
SAMPLE_DATA = {
    'anomalies': [
        {'time': '14:35', 'severity': 'CRITIQUE', 'type': 'Pic stack traces', 'code': 'JBAS-ERROR-001', 'impact': 'Haute', 'count': 18, 'score': 92.1, 'action': 'Analyser logs 14:30–14:40'},
        {'time': '14:20', 'severity': 'CRITIQUE', 'type': 'Connection pool saturé', 'code': 'ARJUNA-012', 'impact': 'Haute', 'count': 31, 'score': 88.4, 'action': 'Augmenter pool / kill sessions'},
        {'time': '08:15', 'severity': 'CRITIQUE', 'type': 'Stack Trace Error', 'code': 'IJ000100', 'impact': 'Haute', 'count': 24, 'score': 85.2, 'action': 'Vérifier persistance JPA'},
        {'time': '10:30', 'severity': 'ANORMAL', 'type': 'Événements sécurité', 'code': 'SEC-AUTH-FAIL', 'impact': 'Moyenne', 'count': 18, 'score': 72.0, 'action': 'Audit IP / comptes'},
        {'time': '16:00', 'severity': 'ANORMAL', 'type': 'Fuite mémoire suspectée', 'code': 'JVM-HEAP', 'impact': 'Moyenne', 'count': 12, 'score': 68.5, 'action': 'Heap dump si récurrent'},
        {'time': '12:45', 'severity': 'SUSPECT', 'type': 'Timeouts réseau', 'code': 'NET-TIMEOUT', 'impact': 'Basse', 'count': 7, 'score': 52.3, 'action': 'Surveiller'},
        {'time': '06:10', 'severity': 'SUSPECT', 'type': 'Warnings batch', 'code': 'BATCH-WARN', 'impact': 'Basse', 'count': 5, 'score': 48.0, 'action': 'OK si batch nocturne'},
    ],
    'kpis': {
        'total_anomalies': 92,
        'critiques': 8,
        'anormales': 12,
        'suspects': 25,
        'normales': 243,
        'pct_normal': 84.4,
        'normales_count': 243,
        'uptime': '99.7%',
        'avg_response': '245ms',
        'errors_24h': 156,
        'evenements_securite': 34,
        'erreurs_moy_fenetre': 0.54,
        'db_size': '2.4 GB',
        'fenetres_total': 288,
    },
    'distribution': {
        'labels': ['NORMAL', 'SUSPECT', 'ANORMAL', 'CRITIQUE'],
        'values': [243, 25, 12, 8],
        'percent': [84.4, 8.7, 4.2, 2.8],
    },
    'shap_features': {
        'features': [
            'count_stack_traces', 'count_errors', 'count_security_events',
            'count_timeouts', 'count_connection_errors', 'error_rate',
            'max_log_gap_sec', 'unique_error_codes',
        ],
        'importance': [0.28, 0.22, 0.18, 0.12, 0.09, 0.06, 0.03, 0.02],
    },
    'xai_perspectives': {
        'benefits': [
            {
                'title': 'Réduction du temps d\'investigation',
                'detail': 'SHAP oriente l\'analyste vers les 3–5 signaux clés au lieu de parcourir des milliers de lignes de logs.',
                'metric': '−40 % temps moyen',
            },
            {
                'title': 'Traçabilité des décisions',
                'detail': 'Chaque alerte peut être justifiée par des contributions de features documentées dans le rapport.',
                'metric': '100 % alertes expliquées',
            },
            {
                'title': 'Priorisation opérationnelle',
                'detail': 'Croisement score Isolation Forest + top features SHAP pour classer les incidents par urgence réelle.',
                'metric': '8 critiques / jour',
            },
        ],
        'scenarios': [
            {
                'time': '14:35',
                'type': 'Pic stack traces',
                'severity': 'CRITIQUE',
                'score': 92.1,
                'top_features': ['nb_stacktrace', 'nb_error_zscore', 'nb_exception'],
                'interpretation': 'Exception Java non gérée en pic — vérifier déploiement récent ou charge utilisateur.',
                'action': 'Filtrer logs sur la fenêtre 14:35–14:40, identifier la classe Java en cause.',
            },
            {
                'time': '14:20',
                'type': 'Connection pool saturé',
                'severity': 'CRITIQUE',
                'score': 88.4,
                'top_features': ['nb_ij', 'nb_pool_ev', 'nb_timeout'],
                'interpretation': 'SHAP pointe le pool JCA — sessions non libérées ou limite pool trop basse.',
                'action': 'Analyser IJ000100, augmenter max-pool-size ou kill sessions orphelines.',
            },
            {
                'time': '10:30',
                'type': 'Événements sécurité',
                'severity': 'ANORMAL',
                'score': 72.0,
                'top_features': ['nb_security', 'nb_security_zscore', 'deviation_vs_hour_baseline'],
                'interpretation': 'Pic d\'événements auth inhabituel pour cette heure — possible scan ou brute-force.',
                'action': 'Audit IP sources, corréler avec logs Undertow / reverse proxy.',
            },
        ],
        'roadmap': [
            {
                'horizon': 'Court terme',
                'entries': [
                    'Afficher les top-3 features SHAP directement dans le tableau des anomalies',
                    'Exporter les explications XAI dans le rapport PDF',
                    'Lier chaque alerte à sa fenêtre dans logs_parsed.csv',
                ],
            },
            {
                'horizon': 'Moyen terme',
                'entries': [
                    'SHAP en quasi temps réel sur flux de logs (fenêtre glissante 5 min)',
                    'Baseline multi-jours pour réduire les faux positifs batch nocturne',
                    'Tableau de bord comparatif jour N vs jour N−1',
                ],
            },
            {
                'horizon': 'Long terme',
                'entries': [
                    'Suggestions de remédiation assistées (playbooks selon top features)',
                    'Intégration SIEM / ticketing automatique avec contexte XAI',
                    'Fine-tuning supervisé à partir des retours analystes (boucle de feedback)',
                ],
            },
        ],
        'charts': {
            'benefits_comparison': {
                'labels': ['Temps investigation (min)', 'Alertes expliquées (%)', 'Priorisation (%)'],
                'before': [45, 35, 58],
                'after': [27, 100, 88],
                'explanation': {
                    'title': 'Impact avant / après XAI',
                    'simple': (
                        'Ce graphique compare la situation avant et après l\'ajout de SHAP. '
                        'Chaque paire de barres montre un indicateur opérationnel : gris = sans explicabilité, '
                        'bleu = avec explicabilité XAI intégrée.'
                    ),
                    'how_to_read': [
                        'Plus la barre bleue est basse (temps), mieux c\'est — l\'analyste gagne du temps.',
                        'Plus la barre bleue est haute (pourcentages), mieux c\'est — plus d\'alertes sont comprises.',
                        'Survolez une barre pour voir la valeur exacte ; cliquez pour le calcul du gain.',
                    ],
                },
                'item_details': {
                    'Temps investigation (min)': {
                        'before': '45 min en moyenne pour analyser une alerte critique (parcours manuel des logs).',
                        'after': '27 min grâce à SHAP qui indique directement les signaux à vérifier.',
                        'gain': 'Gain de 18 minutes (−40 %) par incident — moins de logs à lire inutilement.',
                    },
                    'Alertes expliquées (%)': {
                        'before': '35 % seulement : le score Isolation Forest seul ne dit pas « pourquoi ».',
                        'after': '100 % : chaque alerte affichée peut être justifiée par des features SHAP.',
                        'gain': '+65 points — traçabilité complète pour les comités et escalades.',
                    },
                    'Priorisation (%)': {
                        'before': '58 % de bonnes priorités : risque de traiter un faux positif avant un vrai incident.',
                        'after': '88 % : croisement score + features SHAP pour classer par urgence réelle.',
                        'gain': '+30 points — les 8 alertes critiques du jour sont traitées en premier.',
                    },
                },
            },
            'scenario_scores': {
                'labels': ['14:35 Stack traces', '14:20 Pool connexion', '10:30 Sécurité'],
                'scores': [92.1, 88.4, 72.0],
                'severities': ['CRITIQUE', 'CRITIQUE', 'ANORMAL'],
                'explanation': {
                    'title': 'Scores des scénarios prioritaires',
                    'simple': (
                        'Chaque barre représente une alerte réelle détectée par l\'Isolation Forest. '
                        'La hauteur = score d\'anomalie (0 = normal, 100 = très atypique). '
                        'La couleur indique le niveau : rouge CRITIQUE (≥80), orange ANORMAL (65–80).'
                    ),
                    'how_to_read': [
                        'La ligne rouge pointillée (80) = seuil CRITIQUE : intervention immédiate.',
                        'La ligne orange pointillée (65) = seuil ANORMAL : investigation requise.',
                        'Cliquez sur une barre pour voir l\'interprétation SHAP et l\'action recommandée.',
                    ],
                },
            },
            'feature_contributions': {
                'labels': [
                    'nb_stacktrace', 'nb_ij', 'nb_security',
                    'nb_error_zscore', 'nb_pool_ev', 'nb_timeout',
                ],
                'values': [0.32, 0.28, 0.24, 0.18, 0.15, 0.12],
                'explanation': {
                    'title': 'Top features SHAP (contributions)',
                    'simple': (
                        'SHAP attribue un « poids » à chaque indicateur pour expliquer pourquoi une fenêtre '
                        'est anormale. Plus la barre est longue, plus cette feature a contribué au score d\'alerte.'
                    ),
                    'how_to_read': [
                        'Les features en haut sont les plus déterminantes pour les alertes du jour.',
                        'Un pic sur nb_stacktrace oriente vers une erreur Java ; nb_ij vers le pool de connexions.',
                        'Cliquez sur une barre pour savoir comment l\'analyste doit l\'interpréter.',
                    ],
                },
                'feature_meanings': {
                    'nb_stacktrace': 'Nombre de stack traces Java — signale une exception non gérée dans l\'application.',
                    'nb_ij': 'Erreurs pool JCA (code IJ…) — connexions DB saturées ou sessions non libérées.',
                    'nb_security': 'Événements sécurité (auth, accès refusé) — possible attaque ou mauvaise config.',
                    'nb_error_zscore': 'Pic d\'erreurs vs la dernière heure — activité soudaine et inhabituelle.',
                    'nb_pool_ev': 'Activité globale sur le sous-système pool — charge ou fuite de ressources.',
                    'nb_timeout': 'Timeouts réseau ou services lents — dépendance externe ou surcharge.',
                },
            },
            'roadmap_initiatives': {
                'labels': ['Court terme', 'Moyen terme', 'Long terme'],
                'values': [3, 3, 3],
                'explanation': {
                    'title': 'Feuille de route par horizon',
                    'simple': (
                        'Ce diagramme répartit les 9 initiatives d\'évolution XAI sur trois horizons temporels. '
                        'Chaque part égale (33 %) correspond à 3 actions planifiées pour enrichir le pipeline.'
                    ),
                    'how_to_read': [
                        'Court terme : améliorations rapides du dashboard et des exports.',
                        'Moyen terme : SHAP quasi temps réel et comparaison multi-jours.',
                        'Cliquez sur un segment pour afficher la liste détaillée des initiatives.',
                    ],
                },
            },
        },
    },
    'error_types': {
        'labels': ['Stack trace', 'Sécurité', 'Timeout', 'Pool connexion', 'Persistance', 'Autre'],
        'values': [42, 34, 28, 22, 18, 12],
    },
    'performance': {
        'cpu': 65,
        'memory': 72,
        'disk': 58,
        'network': 41
    }
}

DB_META = {
    'general': {
        'total_size': '2.4 GB',
        'tables': 47,
        'records': '5.2 M',
        'last_backup': 'Il y a 2 h',
        'logs_parsed': '1 245 892',
        'features_rows': 288,
        'source_files': ['logs_parsed.csv', 'features.csv', 'resultats_modele.csv'],
    },
    'instances': [
        {'name': 'db-prod-01', 'type': 'PostgreSQL', 'status': 'online', 'version': '14.5', 'cpu': '8 cores', 'memory': '32 GB', 'role': 'Primaire'},
        {'name': 'db-prod-02', 'type': 'PostgreSQL', 'status': 'online', 'version': '14.5', 'cpu': '8 cores', 'memory': '32 GB', 'role': 'Réplica lecture'},
        {'name': 'db-analytics', 'type': 'SQLite', 'status': 'online', 'version': '3.42', 'cpu': '4 cores', 'memory': '16 GB', 'role': 'Analytics / KPIs'},
        {'name': 'db-backup', 'type': 'PostgreSQL', 'status': 'online', 'version': '14.5', 'cpu': '4 cores', 'memory': '16 GB', 'role': 'Sauvegarde'},
    ],
    'slow_queries': [
        {'query': "SELECT * FROM users WHERE status='active'", 'ms': 1250, 'runs': 450, 'hint': 'Index sur status recommandé'},
        {'query': 'JOIN anomalies ON logs.id = anomalies.log_id', 'ms': 890, 'runs': 320, 'hint': 'Optimiser la jointure'},
        {'query': 'AGGREGATE features_window_5min GROUP BY hour', 'ms': 720, 'runs': 288, 'hint': 'Vue matérialisée possible'},
    ],
    'tables_analytics': [
        {'name': 'features', 'rows': '288', 'desc': '33 features × fenêtre 5 min'},
        {'name': 'resultats_modele', 'rows': '288', 'desc': 'Scores Isolation Forest'},
        {'name': 'anomalies_top', 'rows': '7+', 'desc': 'Alertes prioritaires'},
        {'name': 'logs_parsed', 'rows': '1.2M', 'desc': 'Événements bruts parsés'},
    ],
}


def _build_timeline():
    """Timeline 288 points (5 min) avec pics réalistes."""
    np.random.seed(42)
    timeline = []
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(288):
        t = now + timedelta(minutes=i * 5)
        h, m = t.hour, t.minute
        base = 25 + np.random.uniform(0, 15)
        if (h == 14 and 15 <= m <= 40) or (h == 8 and m <= 20):
            score = float(np.random.uniform(78, 95))
            errors = int(np.random.randint(12, 22))
        elif h in (10, 16) and m < 30:
            score = float(np.random.uniform(62, 78))
            errors = int(np.random.randint(6, 14))
        else:
            score = float(base)
            errors = int(np.random.randint(0, 4))
        timeline.append({
            'time': t.strftime('%H:%M'),
            'score': round(score, 1),
            'errors': errors,
            'warnings': int(np.random.randint(0, 12)),
        })
    return timeline


def _build_heatmap_from_timeline(timeline):
    """Statistiques par heure (0–23) pour graphique lisible."""
    hours = [f'{h:02d}h' for h in range(24)]
    hours_range = [f'{h:02d}h00 → {h:02d}h59' for h in range(24)]
    avg_scores = []
    max_scores = []
    severities = []
    fenetres = []
    critiques = []
    erreurs = []
    for h in range(24):
        prefix = f'{h:02d}:'
        slice_pts = [d for d in timeline if d['time'].startswith(prefix)]
        if not slice_pts:
            avg_scores.append(0)
            max_scores.append(0)
            severities.append('NORMAL')
            fenetres.append(0)
            critiques.append(0)
            erreurs.append(0)
            continue
        scores = [p['score'] for p in slice_pts]
        avg = sum(scores) / len(scores)
        avg_scores.append(round(avg, 1))
        max_scores.append(round(max(scores), 1))
        severities.append(_score_to_severity(avg))
        fenetres.append(len(slice_pts))
        critiques.append(sum(1 for p in slice_pts if p.get('severity') == 'CRITIQUE'))
        erreurs.append(sum(p.get('errors', 0) for p in slice_pts))
    return {
        'hours': hours,
        'hours_range': hours_range,
        'avg_scores': avg_scores,
        'max_scores': max_scores,
        'severities': severities,
        'fenetres': fenetres,
        'critiques': critiques,
        'erreurs': erreurs,
    }


def _build_heatmap_matrix(timeline):
    """
    Grille 24h × 12 créneaux (5 min) pour heatmap visuelle.
    Chaque cellule : score, sévérité, heure exacte.
    """
    by_time = {p['time']: p for p in timeline}
    hours = [f'{h:02d}h' for h in range(24)]
    slot_labels = [f'{m:02d}' for m in range(0, 60, 5)]
    matrix = []
    for h in range(24):
        row = []
        for m in range(0, 60, 5):
            key = f'{h:02d}:{m:02d}'
            pt = by_time.get(key)
            if pt:
                row.append({
                    'time': key,
                    'score': pt['score'],
                    'severity': pt['severity'],
                    'errors': pt.get('errors', 0),
                })
            else:
                row.append({
                    'time': key,
                    'score': 0,
                    'severity': 'NORMAL',
                    'errors': 0,
                })
        matrix.append(row)
    return {
        'hours': hours,
        'slot_labels': slot_labels,
        'matrix': matrix,
    }


def _build_heatmap():
    return _build_heatmap_from_timeline(_get_timeline())


def _build_score_histogram():
    timeline = _build_timeline()
    bins = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']
    counts = [0] * 10
    for d in timeline:
        idx = min(int(d['score'] // 10), 9)
        counts[idx] += 1
    return {'bins': bins, 'counts': counts}


_TIMELINE_CACHE = None


def _get_timeline():
    global _TIMELINE_CACHE
    if _TIMELINE_CACHE is None:
        _TIMELINE_CACHE = _build_timeline()
        for p in _TIMELINE_CACHE:
            p['severity'] = _score_to_severity(p['score'])
    return _TIMELINE_CACHE


def _score_to_severity(score):
    if score >= 80:
        return 'CRITIQUE'
    if score >= 65:
        return 'ANORMAL'
    if score >= 45:
        return 'SUSPECT'
    return 'NORMAL'


def _parse_hour(time_str):
    h, m = time_str.split(':')
    return int(h), int(m)


def _filter_timeline(timeline, hour_from=None, hour_to=None, severity=None):
    out = []
    for p in timeline:
        h, _ = _parse_hour(p['time'])
        if hour_from is not None and h < hour_from:
            continue
        if hour_to is not None and h > hour_to:
            continue
        if severity and severity != 'ALL' and p['severity'] != severity:
            continue
        out.append(p)
    return out


def _kpis_from_timeline(timeline):
    total = len(timeline) or 1
    critiques = sum(1 for p in timeline if p['severity'] == 'CRITIQUE')
    anormales = sum(1 for p in timeline if p['severity'] == 'ANORMAL')
    suspects = sum(1 for p in timeline if p['severity'] == 'SUSPECT')
    normales = sum(1 for p in timeline if p['severity'] == 'NORMAL')
    pct_normal = round(100 * normales / total, 1)
    erreurs = sum(p['errors'] for p in timeline)
    return {
        'fenetres_total': total,
        'critiques': critiques,
        'anormales': anormales,
        'suspects': suspects,
        'normales': normales,
        'pct_normal': pct_normal,
        'erreurs_total': erreurs,
        'erreurs_moy_fenetre': round(erreurs / total, 2),
        'evenements_securite': SAMPLE_DATA['kpis']['evenements_securite'],
        'uptime': SAMPLE_DATA['kpis']['uptime'],
        'db_size': SAMPLE_DATA['kpis']['db_size'],
    }


def _distribution_from_timeline(timeline):
    labels = ['NORMAL', 'SUSPECT', 'ANORMAL', 'CRITIQUE']
    values = [
        sum(1 for p in timeline if p['severity'] == lbl) for lbl in labels
    ]
    total = sum(values) or 1
    percent = [round(100 * v / total, 1) for v in values]
    return {'labels': labels, 'values': values, 'percent': percent}


_SEV_RANK = {'CRITIQUE': 4, 'ANORMAL': 3, 'SUSPECT': 2, 'NORMAL': 1}


def _worst_severity(severities):
    return max(severities, key=lambda s: _SEV_RANK.get(s, 0))


def _severity_chart_color(severity):
    mapping = {
        'CRITIQUE': TT_COLORS['danger'],
        'ANORMAL': TT_COLORS['warning'],
        'SUSPECT': TT_COLORS['info'],
        'NORMAL': TT_COLORS['success'],
    }
    return mapping.get(severity, TT_COLORS['primary'])


def _matplotlib_fig_to_image(fig, width=6.0 * inch, height=2.75 * inch):
    """Convertit une figure matplotlib en image ReportLab."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def _mpl_style_axes(ax):
    ax.set_facecolor('#f8fafc')
    ax.grid(axis='y', alpha=0.35, linestyle='--', color='#ccd6e0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#ccd6e0')
    ax.spines['bottom'].set_color('#ccd6e0')


def _build_pdf_benefits_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    chart = SAMPLE_DATA['xai_perspectives']['charts']['benefits_comparison']
    labels = chart['labels']
    x = np.arange(len(labels))
    bar_w = 0.34

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    fig.patch.set_facecolor('#ffffff')
    bars_before = ax.bar(
        x - bar_w / 2, chart['before'], bar_w, label='Avant XAI',
        color='#95A5A6', edgecolor='white', linewidth=1.2, zorder=3,
    )
    bars_after = ax.bar(
        x + bar_w / 2, chart['after'], bar_w, label='Après XAI',
        color='#0055A4', edgecolor='#FFD200', linewidth=1.5, zorder=3,
    )
    for bars, vals in ((bars_before, chart['before']), (bars_after, chart['after'])):
        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                str(val), ha='center', va='bottom', fontsize=8, fontweight='bold', color='#333',
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Valeur', fontsize=9, color='#555')
    ax.set_title(
        'Impact XAI sur les indicateurs opérationnels',
        fontsize=12, fontweight='bold', color='#0055A4', pad=12,
    )
    ax.legend(loc='upper right', fontsize=8, framealpha=0.95)
    _mpl_style_axes(ax)
    fig.tight_layout()
    return _matplotlib_fig_to_image(fig)


def _build_pdf_scenario_scores_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    chart = SAMPLE_DATA['xai_perspectives']['charts']['scenario_scores']
    bar_colors = [_severity_chart_color(s) for s in chart['severities']]

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    fig.patch.set_facecolor('#ffffff')
    bars = ax.bar(
        chart['labels'], chart['scores'], color=bar_colors,
        edgecolor='white', linewidth=1.5, width=0.55, zorder=3,
    )
    ax.set_ylim(0, 100)
    ax.set_ylabel('Score Isolation Forest', fontsize=9, color='#555')
    ax.set_title(
        'Scores des scénarios XAI prioritaires',
        fontsize=12, fontweight='bold', color='#0055A4', pad=12,
    )
    ax.axhline(80, color='#E74C3C', linestyle='--', linewidth=1.2, alpha=0.85, label='CRITIQUE (80)')
    ax.axhline(65, color='#F39C12', linestyle='--', linewidth=1.2, alpha=0.85, label='ANORMAL (65)')
    ax.axhspan(80, 100, alpha=0.06, color='#E74C3C', zorder=0)
    ax.axhspan(65, 80, alpha=0.06, color='#F39C12', zorder=0)
    for bar, score in zip(bars, chart['scores']):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
            f'{score}', ha='center', fontsize=9, fontweight='bold', color='#333',
        )
    ax.legend(loc='upper right', fontsize=7, framealpha=0.95)
    _mpl_style_axes(ax)
    plt.setp(ax.get_xticklabels(), rotation=14, ha='right', fontsize=8)
    fig.tight_layout()
    return _matplotlib_fig_to_image(fig)


def _build_pdf_feature_contributions_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    chart = SAMPLE_DATA['xai_perspectives']['charts']['feature_contributions']
    y_pos = np.arange(len(chart['labels']))

    max_val = max(chart['values']) or 1
    bar_colors = [
        plt.cm.Blues(0.35 + 0.55 * (v / max_val)) for v in chart['values']
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.patch.set_facecolor('#ffffff')
    bars = ax.barh(y_pos, chart['values'], color=bar_colors, height=0.58, edgecolor='white', linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(chart['labels'], fontsize=9, family='monospace')
    ax.set_xlabel('Contribution SHAP moyenne', fontsize=9, color='#555')
    ax.set_title(
        'Top features explicatives (agrégé scénarios)',
        fontsize=12, fontweight='bold', color='#0055A4', pad=12,
    )
    for bar, val in zip(bars, chart['values']):
        ax.text(val + 0.008, bar.get_y() + bar.get_height() / 2, f'{val:.2f}',
                va='center', fontsize=8, color='#0055A4', fontweight='bold')
    ax.invert_yaxis()
    ax.set_facecolor('#f8fafc')
    ax.grid(axis='x', alpha=0.35, linestyle='--', color='#ccd6e0')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return _matplotlib_fig_to_image(fig)


def _build_pdf_roadmap_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    chart = SAMPLE_DATA['xai_perspectives']['charts']['roadmap_initiatives']
    palette = ['#0055A4', '#3498DB', '#FFD200']

    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    fig.patch.set_facecolor('#ffffff')
    wedges, texts, autotexts = ax.pie(
        chart['values'],
        labels=chart['labels'],
        autopct='%1.0f%%',
        colors=palette,
        explode=(0.06, 0.04, 0.06),
        shadow=True,
        startangle=90,
        textprops={'fontsize': 9, 'color': '#333'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
        autotext.set_color('white')
    ax.set_title(
        'Répartition feuille de route XAI',
        fontsize=12, fontweight='bold', color='#0055A4', pad=14,
    )
    fig.tight_layout()
    return _matplotlib_fig_to_image(fig, width=4.5 * inch, height=2.5 * inch)


def _build_anomaly_details(anoms):
    """Répartition détaillée par type d'anomalie (pour graphique à côté du donut)."""
    if not anoms:
        return {
            'labels': [],
            'errors': [],
            'avg_scores': [],
            'severities': [],
            'codes': [],
            'impacts': [],
        }
    groups = {}
    for a in anoms:
        key = a.get('type', 'Autre')
        if key not in groups:
            groups[key] = {
                'errors': 0,
                'scores': [],
                'severities': [],
                'codes': [],
                'impacts': [],
            }
        g = groups[key]
        g['errors'] += int(a.get('count', 0))
        if a.get('score') is not None:
            g['scores'].append(float(a['score']))
        g['severities'].append(a.get('severity', 'SUSPECT'))
        if a.get('code'):
            g['codes'].append(a['code'])
        if a.get('impact'):
            g['impacts'].append(a['impact'])

    ranked = sorted(groups.items(), key=lambda x: x[1]['errors'], reverse=True)
    return {
        'labels': [name for name, _ in ranked],
        'errors': [g['errors'] for _, g in ranked],
        'avg_scores': [
            round(sum(g['scores']) / len(g['scores']), 1) if g['scores'] else 0
            for _, g in ranked
        ],
        'severities': [_worst_severity(g['severities']) for _, g in ranked],
        'codes': [', '.join(dict.fromkeys(g['codes'])) for _, g in ranked],
        'impacts': [g['impacts'][0] if g['impacts'] else '—' for _, g in ranked],
    }

# ═══════════════════════════════════════════════════════════════
# MODÈLE DE DONNÉES
# ═══════════════════════════════════════════════════════════════

class User(db.Model):
    """Modèle utilisateur pour authentification"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ═══════════════════════════════════════════════════════════════
# DÉCORATEURS
# ═══════════════════════════════════════════════════════════════

def login_required(f):
    """Décorateur pour protéger les routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ═══════════════════════════════════════════════════════════════
# ROUTES D'AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Redirection vers login ou dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Identifiants invalides')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Déconnexion sécurisée"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription utilisateur"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # Validation
        if not all([username, email, password, password_confirm]):
            return render_template('login.html', error='Tous les champs sont requis')

        if password != password_confirm:
            return render_template('login.html', error='Les mots de passe ne correspondent pas')

        if len(password) < 6:
            return render_template('login.html', error='Le mot de passe doit contenir au moins 6 caractères')

        if User.query.filter_by(username=username).first():
            return render_template('login.html', error='Cet utilisateur existe déjà')

        # Créer nouvel utilisateur
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        return redirect(url_for('dashboard'))

    return render_template('login.html', register=True)

# ═══════════════════════════════════════════════════════════════
# ROUTES DASHBOARD
# ═══════════════════════════════════════════════════════════════

def _build_dashboard_bundle(hour_from=None, hour_to=None, severity='ALL', search=''):
    timeline = _filter_timeline(
        _get_timeline(),
        hour_from=hour_from,
        hour_to=hour_to,
        severity=severity if severity != 'ALL' else None,
    )
    anoms = SAMPLE_DATA['anomalies']
    if search:
        q = search.lower()
        anoms = [
            a for a in anoms
            if q in a.get('type', '').lower()
            or q in a.get('code', '').lower()
            or q in a.get('time', '').lower()
        ]
    if severity != 'ALL':
        anoms = [a for a in anoms if a.get('severity') == severity]
    return {
        'updated_at': datetime.now().strftime('%H:%M:%S'),
        'kpis': _kpis_from_timeline(timeline),
        'timeline': timeline,
        'distribution': _distribution_from_timeline(timeline),
        'heatmap': _build_heatmap_from_timeline(timeline),
        'heatmap_matrix': _build_heatmap_matrix(_get_timeline()),
        'anomalies': anoms,
        'anomaly_details': _build_anomaly_details(anoms),
    }


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard interactif principal."""
    boot = _build_dashboard_bundle()
    return render_template(
        'page_dashboard.html',
        username=session.get('username'),
        boot=boot,
    )


@app.route('/page/db')
@login_required
def page_db():
    """Page DB : contenu principal rendu côté serveur (évite JSON JS trop lourd)."""
    boot = _build_dashboard_bundle()
    return render_template(
        'page_db.html',
        username=session.get('username'),
        kpis=boot['kpis'],
        distribution=boot['distribution'],
        anomaly_details=boot['anomaly_details'],
        anomalies=boot['anomalies'],
        heatmap_matrix=boot['heatmap_matrix'],
        timeline_sample=boot['timeline'][::6],
        updated_at=boot['updated_at'],
        db_meta=DB_META,
    )


@app.route('/page/security')
@login_required
def page_security():
    return render_template('page_security.html', username=session.get('username'))


@app.route('/page/rapport')
@login_required
def page_rapport():
    preview = SAMPLE_DATA['kpis']
    return render_template(
        'page_rapport.html',
        username=session.get('username'),
        preview=preview,
        report_date=datetime.now().strftime('%d/%m/%Y'),
    )


@app.route('/page/graphiques')
@login_required
def page_graphiques():
    return render_template('page_graphiques.html', username=session.get('username'))


@app.route('/page/interpretation-xai')
@login_required
def page_interpretation_xai():
    xai = SAMPLE_DATA['xai_perspectives']
    return render_template(
        'page_interpretation_xai.html',
        username=session.get('username'),
        benefits=xai['benefits'],
        scenarios=xai['scenarios'],
        roadmap=xai['roadmap'],
    )


@app.route('/page/perspectives')
@login_required
def page_perspectives():
    return redirect(url_for('page_interpretation_xai'))

@app.route('/api/anomalies')
@login_required
def get_anomalies():
    """API: données des anomalies"""
    return jsonify(SAMPLE_DATA['anomalies'])

@app.route('/api/kpis')
@login_required
def get_kpis():
    """API: KPIs"""
    return jsonify(SAMPLE_DATA['kpis'])

@app.route('/api/performance')
@login_required
def get_performance():
    """API: données de performance"""
    return jsonify(SAMPLE_DATA['performance'])

@app.route('/api/timeline')
@login_required
def get_timeline():
    return jsonify(_get_timeline())


@app.route('/api/dashboard/bundle')
@login_required
def get_dashboard_bundle():
    """Données agrégées pour le dashboard interactif (filtres optionnels)."""
    hour_from = request.args.get('hour_from', type=int)
    hour_to = request.args.get('hour_to', type=int)
    severity = request.args.get('severity', 'ALL').upper()
    search = (request.args.get('q') or '').strip().lower()
    bundle = _build_dashboard_bundle(hour_from, hour_to, severity, search)
    return jsonify(bundle)


@app.route('/api/db-kpis')
@login_required
def get_db_kpis():
    k = SAMPLE_DATA['kpis']
    return jsonify({
        'fenetres_total': k['fenetres_total'],
        'critiques': k['critiques'],
        'anormales': k['anormales'],
        'suspects': k['suspects'],
        'pct_normal': k['pct_normal'],
        'erreurs_total': k['errors_24h'],
        'erreurs_moy_fenetre': k['erreurs_moy_fenetre'],
        'evenements_securite': k['evenements_securite'],
        'uptime': k['uptime'],
        'db_size': k['db_size'],
    })


@app.route('/api/charts/distribution')
@login_required
def get_distribution():
    return jsonify(SAMPLE_DATA['distribution'])


@app.route('/api/charts/heatmap')
@login_required
def get_heatmap():
    return jsonify(_build_heatmap())


@app.route('/api/charts/heatmap-matrix')
@login_required
def get_heatmap_matrix():
    return jsonify(_build_heatmap_matrix(_get_timeline()))


@app.route('/api/charts/shap')
@login_required
def get_shap_features():
    return jsonify(SAMPLE_DATA['shap_features'])


@app.route('/api/xai/interpretation')
@login_required
def get_xai_interpretation():
    return jsonify(SAMPLE_DATA['xai_perspectives'])


@app.route('/api/xai/perspectives')
@login_required
def get_xai_perspectives():
    return get_xai_interpretation()


@app.route('/api/charts/error-types')
@login_required
def get_error_types():
    return jsonify(SAMPLE_DATA['error_types'])


@app.route('/api/charts/score-histogram')
@login_required
def get_score_histogram():
    return jsonify(_build_score_histogram())


# Anciennes URLs (compatibilité)
@app.route('/section/performance')
@login_required
def section_performance():
    return redirect(url_for('page_graphiques'))

@app.route('/section/security')
@login_required
def section_security():
    return redirect(url_for('page_security'))

@app.route('/section/details-db')
@login_required
def section_details_db():
    return redirect(url_for('page_db'))

@app.route('/section/configuration')
@login_required
def section_configuration():
    return redirect(url_for('page_db'))

@app.route('/section/rapport')
@login_required
def section_rapport():
    return redirect(url_for('page_rapport'))

# ═══════════════════════════════════════════════════════════════
# EXPORT PDF — MISE EN PAGE PROFESSIONNELLE
# ═══════════════════════════════════════════════════════════════

_PDF_SEV_BG = {
    'CRITIQUE': '#fde8e8',
    'ANORMAL': '#fff3cd',
    'SUSPECT': '#d1ecf1',
    'NORMAL': '#d4edda',
}
_PDF_SEV_TEXT = {
    'CRITIQUE': '#c0392b',
    'ANORMAL': '#856404',
    'SUSPECT': '#0c5460',
    'NORMAL': '#155724',
}
_PDF_STATUS = {
    'CRITIQUE': ('CRITIQUE', TT_COLORS['danger']),
    'ANORMAL': ('ANORMAL', TT_COLORS['warning']),
    'BON': ('BON', TT_COLORS['success']),
}
_PDF_PASTEL = {
    'page_bg': '#f4f7fa',
    'header_band': '#e4edf5',
    'card': '#ffffff',
    'accent': '#6b94b8',
    'accent_deep': '#3d5f7c',
    'title': '#2c4458',
    'subtitle': '#5a6d7e',
    'meta': '#8496a8',
    'border': '#d8e2ec',
    'divider': '#b8c9d9',
    'kpi_bg': ['#e8f1f8', '#eaf3ef', '#eef1f7', '#f2eeea'],
    'kpi_value': '#2c4458',
    'kpi_label': '#7a8c9c',
}


def _pdf_styles():
    base = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle(
            'CoverTitle', parent=base['Heading1'], fontSize=16,
            textColor=colors.HexColor(_PDF_PASTEL['title']), alignment=TA_CENTER,
            fontName='Helvetica-Bold', spaceAfter=4, leading=20,
        ),
        'cover_sub': ParagraphStyle(
            'CoverSub', parent=base['Normal'], fontSize=12,
            textColor=colors.HexColor(_PDF_PASTEL['subtitle']),
            alignment=TA_CENTER, spaceAfter=5, leading=16,
        ),
        'cover_meta': ParagraphStyle(
            'CoverMeta', parent=base['Normal'], fontSize=9,
            textColor=colors.HexColor(_PDF_PASTEL['meta']), alignment=TA_CENTER,
            spaceAfter=3,
        ),
        'cover_kpi_value': ParagraphStyle(
            'CoverKpiValue', parent=base['Normal'], fontSize=18,
            textColor=colors.HexColor(_PDF_PASTEL['kpi_value']),
            alignment=TA_CENTER, fontName='Helvetica-Bold', leading=22,
        ),
        'cover_kpi_label': ParagraphStyle(
            'CoverKpiLabel', parent=base['Normal'], fontSize=8,
            textColor=colors.HexColor(_PDF_PASTEL['kpi_label']),
            alignment=TA_CENTER, leading=11,
        ),
        'cover_tag': ParagraphStyle(
            'CoverTag', parent=base['Normal'], fontSize=8,
            textColor=colors.HexColor(_PDF_PASTEL['accent_deep']),
            alignment=TA_CENTER, fontName='Helvetica-Oblique',
        ),
        'section': ParagraphStyle(
            'Section', parent=base['Heading2'], fontSize=13,
            textColor=colors.white, fontName='Helvetica-Bold',
            leftIndent=8, spaceBefore=0, spaceAfter=0,
        ),
        'subsection': ParagraphStyle(
            'SubSection', parent=base['Heading3'], fontSize=10,
            textColor=colors.HexColor(TT_COLORS['primary']),
            fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=4,
        ),
        'body': ParagraphStyle(
            'Body', parent=base['Normal'], fontSize=10,
            leading=14, textColor=colors.HexColor('#444444'),
            alignment=TA_JUSTIFY, spaceAfter=8,
        ),
        'body_small': ParagraphStyle(
            'BodySmall', parent=base['Normal'], fontSize=9,
            leading=13, textColor=colors.HexColor('#555555'), spaceAfter=6,
        ),
        'explain_box': ParagraphStyle(
            'ExplainBox', parent=base['Normal'], fontSize=9,
            leading=13, textColor=colors.HexColor('#444444'),
            leftIndent=6, spaceAfter=4,
        ),
        'toc': ParagraphStyle(
            'TOC', parent=base['Normal'], fontSize=10,
            textColor=colors.HexColor(TT_COLORS['primary']),
            leftIndent=12, spaceAfter=5,
        ),
        'footer_note': ParagraphStyle(
            'FooterNote', parent=base['Normal'], fontSize=8,
            textColor=colors.grey, alignment=TA_CENTER,
        ),
    }


def _pdf_draw_cover_frame(canvas, doc):
    """Fond pastel et ornements discrets pour la page de garde."""
    canvas.saveState()
    w, h = A4
    p = _PDF_PASTEL

    canvas.setFillColor(colors.HexColor(p['page_bg']))
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor(p['header_band']))
    canvas.rect(0, h - 95, w, 95, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor('#edf2f7'))
    canvas.circle(w - 55, h - 48, 38, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#e8eef5'))
    canvas.circle(52, 72, 48, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#f0f4f8'))
    canvas.circle(w - 120, 95, 28, fill=1, stroke=0)

    canvas.setStrokeColor(colors.HexColor(p['divider']))
    canvas.setLineWidth(0.8)
    canvas.line(56, h - 97, w - 56, h - 97)

    canvas.setFillColor(colors.HexColor(p['meta']))
    canvas.setFont('Helvetica', 7.5)
    canvas.drawCentredString(
        w / 2, 24,
        'Tunisie Telecom  ·  TT Analytics  ·  Document confidentiel',
    )
    canvas.restoreState()


def _pdf_draw_page_frame(canvas, doc, *, cover=False):
    if cover:
        _pdf_draw_cover_frame(canvas, doc)
        return
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(colors.HexColor(TT_COLORS['primary']))
    canvas.rect(0, h - 42, w, 42, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#dce8f4'))
    canvas.rect(0, h - 45, w, 2, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(36, h - 28, 'TT Analytics  |  Rapport anomalies & interpretation XAI')
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(w - 36, h - 28, datetime.now().strftime('%d/%m/%Y'))
    canvas.setStrokeColor(colors.HexColor('#e0e6ed'))
    canvas.setLineWidth(0.5)
    canvas.line(36, 38, w - 36, 38)
    canvas.setFillColor(colors.HexColor('#888888'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(36, 22, 'Tunisie Telecom — Document confidentiel')
    canvas.drawRightString(w - 36, 22, f'Page {doc.page}')
    canvas.restoreState()


def _pdf_build_cover_flowables(kpis, now_str):
    """En-tete compact integre a la premiere page (pas de page de garde vide)."""
    st = _pdf_styles()
    p = _PDF_PASTEL
    flowables = []

    header_rows = [
        [Paragraph('TUNISIE TELECOM — Rapport analytique', st['cover_title'])],
        [Paragraph(
            'Detection d\'anomalies &amp; explicabilite XAI  |  '
            f'Genere le {now_str}',
            st['cover_meta'],
        )],
    ]
    header_card = Table(header_rows, colWidths=[6.8 * inch])
    header_card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(p['card'])),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (0, 0), 10),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('TOPPADDING', (0, 1), (0, 1), 2),
        ('BOTTOMPADDING', (0, 1), (0, 1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(p['border'])),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(p['accent'])),
    ]))
    flowables.append(header_card)
    flowables.append(Spacer(1, 0.1 * inch))

    kpi_specs = [
        (str(kpis['total_anomalies']), 'Anomalies', p['kpi_bg'][0]),
        (str(kpis['critiques']), 'Critiques', p['kpi_bg'][1]),
        (str(kpis['uptime']), 'Disponibilite', p['kpi_bg'][2]),
        (str(kpis['errors_24h']), 'Erreurs 24h', p['kpi_bg'][3]),
    ]
    kpi_cells = []
    for val, label, bg in kpi_specs:
        kpi_cells.append(Paragraph(
            f'<b>{val}</b><br/><font size="7" color="{p["kpi_label"]}">{label.upper()}</font>',
            st['cover_kpi_value'],
        ))
    kpi_row = Table([kpi_cells], colWidths=[1.65 * inch] * 4)
    kpi_cmds = [
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(p['border'])),
    ]
    for col, (_, _, bg) in enumerate(kpi_specs):
        kpi_cmds.append(('BACKGROUND', (col, 0), (col, 0), colors.HexColor(bg)))
    kpi_row.setStyle(TableStyle(kpi_cmds))
    flowables.append(kpi_row)
    flowables.append(Spacer(1, 0.12 * inch))
    return flowables


def _pdf_section_banner(title, number=None):
    st = _pdf_styles()
    label = f'{number}. {title}' if number else title
    tbl = Table([[Paragraph(label.upper(), st['section'])]], colWidths=[6.8 * inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(TT_COLORS['primary'])),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0, colors.HexColor(_PDF_PASTEL['accent'])),
    ]))
    return tbl


def _pdf_explanation_box(title, simple_text, how_to_read=None):
    st = _pdf_styles()
    rows = [[Paragraph(f'<b>{title}</b>', st['explain_box'])]]
    rows.append([Paragraph(simple_text, st['explain_box'])])
    if how_to_read:
        for line in how_to_read[:2]:
            rows.append([Paragraph(f'&#8226; {line}', st['explain_box'])])
    tbl = Table(rows, colWidths=[6.6 * inch])
    tbl.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor(_PDF_PASTEL['accent'])),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(_PDF_PASTEL['border'])),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
    ]))
    return tbl


def _pdf_chart_block(chart_img, explanation):
    """Bloc graphique compact — sans KeepTogether pour eviter les pages blanches."""
    exp = explanation or {}
    return [
        chart_img,
        Spacer(1, 0.04 * inch),
        _pdf_explanation_box(
            exp.get('title', 'Lecture du graphique'),
            exp.get('simple', ''),
            exp.get('how_to_read'),
        ),
        Spacer(1, 0.08 * inch),
    ]


def _pdf_table_header_style():
    return [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(TT_COLORS['primary'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ]


def _pdf_apply_severity_rows(table_style, rows, severity_col=2, start_row=1):
    for i, row in enumerate(rows[start_row:], start=start_row):
        sev = str(row[severity_col]).upper()
        if sev in _PDF_SEV_BG:
            table_style.append(('BACKGROUND', (severity_col, i), (severity_col, i),
                                colors.HexColor(_PDF_SEV_BG[sev])))
            table_style.append(('TEXTCOLOR', (severity_col, i), (severity_col, i),
                                colors.HexColor(_PDF_SEV_TEXT[sev])))
            table_style.append(('FONTNAME', (severity_col, i), (severity_col, i), 'Helvetica-Bold'))


def _build_pdf_story():
    st = _pdf_styles()
    story = []
    kpis = SAMPLE_DATA['kpis']
    xai = SAMPLE_DATA['xai_perspectives']
    now_str = datetime.now().strftime('%d/%m/%Y a %H:%M')
    story.extend(_pdf_build_cover_flowables(kpis, now_str))

    story.append(_pdf_section_banner('Resume executif', 1))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        'Synthese des indicateurs cles sur les 24 dernieres heures. '
        'Les statuts sont codes par couleur selon le niveau de criticite.',
        st['body'],
    ))
    summary_rows = [['Metrique', 'Valeur', 'Statut']]
    summary_meta = [
        ('Total anomalies', str(kpis['total_anomalies']), 'ANORMAL'),
        ('Fenetres critiques', str(kpis['critiques']), 'CRITIQUE'),
        ('Uptime systeme', kpis['uptime'], 'BON'),
        ('Erreurs (24h)', str(kpis['errors_24h']), 'ANORMAL'),
        ('Evenements securite', str(kpis['evenements_securite']), 'ANORMAL'),
    ]
    for label, val, status_key in summary_meta:
        status_label, status_color = _PDF_STATUS.get(status_key, (status_key, TT_COLORS['primary']))
        summary_rows.append([
            label, val,
            Paragraph(f'<font color="{status_color}"><b>{status_label}</b></font>', st['body_small']),
        ])
    summary_table = Table(summary_rows, colWidths=[2.4 * inch, 1.8 * inch, 2.2 * inch])
    sum_style = _pdf_table_header_style() + [
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f8fc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d8e4')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(TT_COLORS['primary'])),
    ]
    summary_table.setStyle(TableStyle(sum_style))
    story.append(summary_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(_pdf_section_banner('Anomalies detectees', 2))
    story.append(Spacer(1, 0.08 * inch))
    anom_rows = [['Heure', 'Type', 'Severite', 'Impact', 'Nb', 'Score']]
    for anom in SAMPLE_DATA['anomalies']:
        anom_rows.append([
            anom['time'],
            Paragraph(anom['type'], st['body_small']),
            anom['severity'],
            anom['impact'],
            str(anom['count']),
            str(anom.get('score', '—')),
        ])
    anom_table = Table(anom_rows, colWidths=[0.7 * inch, 1.9 * inch, 0.9 * inch, 0.8 * inch, 0.5 * inch, 0.6 * inch])
    anom_style = _pdf_table_header_style() + [
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d8e4')),
    ]
    _pdf_apply_severity_rows(anom_style, anom_rows, severity_col=2)
    anom_table.setStyle(TableStyle(anom_style))
    story.append(anom_table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(_pdf_section_banner('Recommandations', 3))
    story.append(Spacer(1, 0.08 * inch))
    recs = [
        ('Securite applicative', 'Renforcer authentification et autorisation. Croiser SHAP nb_security avec logs Undertow.', TT_COLORS['danger']),
        ('Performance', 'Optimiser pools de connexion (nb_ij). Surveiller heap JVM en cas de stack traces.', TT_COLORS['warning']),
        ('Monitoring', 'Alertes temps reel sur score >= 80. Integrer top-3 features SHAP dans les notifications.', TT_COLORS['primary']),
        ('Infrastructure', 'Planifier capacite haute saison. Baseline multi-jours pour reduire faux positifs batch.', TT_COLORS['info']),
    ]
    for i, (title, text, color) in enumerate(recs, 1):
        rec_tbl = Table([[
            Paragraph(f'<font color="white"><b>{i}</b></font>', st['body_small']),
            Paragraph(f'<b><font color="{color}">{title}</font></b><br/>{text}', st['body_small']),
        ]], colWidths=[0.45 * inch, 6.1 * inch])
        rec_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(color)),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dde3ea')),
        ]))
        story.append(rec_tbl)
        story.append(Spacer(1, 0.05 * inch))

    charts = xai['charts']
    story.append(_pdf_section_banner('Interpretation XAI — graphiques', 4))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        'Visualisations de l\'impact de l\'explicabilite SHAP. '
        'Chaque graphique est accompagne d\'une lecture guidee pour l\'analyste.',
        st['body'],
    ))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph('Graphique A — Impact avant / apres XAI', st['subsection']))
    story.extend(_pdf_chart_block(_build_pdf_benefits_chart(), charts['benefits_comparison'].get('explanation')))
    story.append(Paragraph('Graphique B — Scores des scenarios prioritaires', st['subsection']))
    story.extend(_pdf_chart_block(_build_pdf_scenario_scores_chart(), charts['scenario_scores'].get('explanation')))
    story.append(Paragraph('Graphique C — Contributions SHAP des features', st['subsection']))
    story.extend(_pdf_chart_block(_build_pdf_feature_contributions_chart(), charts['feature_contributions'].get('explanation')))
    story.append(Paragraph('Graphique D — Feuille de route par horizon', st['subsection']))
    story.extend(_pdf_chart_block(_build_pdf_roadmap_chart(), charts['roadmap_initiatives'].get('explanation')))

    story.append(_pdf_section_banner('Apports, scenarios & feuille de route', 5))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph('Apports de l\'explicabilite', st['subsection']))
    benefits_rows = [['Indicateur', 'Description', 'Gain']]
    for b in xai['benefits']:
        benefits_rows.append([
            Paragraph(f'<b>{b["title"]}</b>', st['body_small']),
            Paragraph(b['detail'], st['body_small']),
            Paragraph(f'<font color="{TT_COLORS["primary"]}"><b>{b["metric"]}</b></font>', st['body_small']),
        ])
    benefits_table = Table(benefits_rows, colWidths=[1.5 * inch, 3.6 * inch, 1.3 * inch])
    ben_style = _pdf_table_header_style() + [
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef4fb')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d8e4')),
    ]
    benefits_table.setStyle(TableStyle(ben_style))
    story.append(benefits_table)
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph('Scenarios d\'interpretation SHAP', st['subsection']))
    scenario_rows = [['Heure', 'Type', 'Score', 'Interpretation', 'Action']]
    for s in xai['scenarios']:
        scenario_rows.append([
            s['time'],
            Paragraph(s['type'], st['body_small']),
            Paragraph(f'<font color="{_severity_chart_color(s["severity"])}"><b>{s["score"]}</b></font>', st['body_small']),
            Paragraph(s['interpretation'], st['body_small']),
            Paragraph(s['action'], st['body_small']),
        ])
    scenario_table = Table(scenario_rows, colWidths=[0.6 * inch, 1.1 * inch, 0.55 * inch, 2.3 * inch, 2.0 * inch])
    scen_style = _pdf_table_header_style() + [
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d8e4')),
    ]
    scenario_table.setStyle(TableStyle(scen_style))
    story.append(scenario_table)
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph('Feuille de route', st['subsection']))
    horizon_colors = [TT_COLORS['primary'], TT_COLORS['info'], _PDF_PASTEL['accent']]
    for block, hcolor in zip(xai['roadmap'], horizon_colors):
        hdr = Table([[Paragraph(f'<font color="white"><b>{block["horizon"]}</b></font>', st['body_small'])]],
                    colWidths=[6.5 * inch])
        hdr.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(hcolor)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(hdr)
        for entry in block['entries']:
            story.append(Paragraph(f'&nbsp;&nbsp;&bull; {entry}', st['body_small']))
        story.append(Spacer(1, 0.05 * inch))

    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor(_PDF_PASTEL['divider'])))
    story.append(Paragraph(
        'Fin du rapport — TT Analytics v2.0 | Pipeline Isolation Forest + SHAP',
        st['footer_note'],
    ))
    return story


# ═══════════════════════════════════════════════════════════════
# ROUTES TÉLÉCHARGEMENT & EXPORT
# ═══════════════════════════════════════════════════════════════

@app.route('/export/pdf-rapport')
@login_required
def export_pdf_rapport():
    """Génération et téléchargement du rapport PDF"""
    from flask import send_file

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=0.55 * inch, bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        title='Rapport TT Analytics',
        author='Tunisie Telecom',
    )
    story = _build_pdf_story()
    doc.build(
        story,
        onFirstPage=lambda c, d: _pdf_draw_page_frame(c, d, cover=False),
        onLaterPages=lambda c, d: _pdf_draw_page_frame(c, d, cover=False),
    )
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Rapport_Anomalies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

# ═══════════════════════════════════════════════════════════════
# GESTION DES ERREURS
# ═══════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    """Erreur 404"""
    return render_template('error.html', code=404, message='Page non trouvée'), 404

@app.errorhandler(500)
def server_error(error):
    """Erreur 500"""
    return render_template('error.html', code=500, message='Erreur serveur'), 500

# ═══════════════════════════════════════════════════════════════
# INITIALISATION
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialiser la base de données avec un utilisateur de démonstration"""
    with app.app_context():
        db.create_all()

        # Vérifier si l'utilisateur démo existe
        if not User.query.filter_by(username='demo').first():
            demo_user = User(
                username='demo',
                email='demo@tunisietelecom.tn'
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)

            admin_user = User(
                username='admin',
                email='admin@tunisietelecom.tn'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)

            db.session.commit()
            print("✅ Base de données initialisée avec les utilisateurs de démo")
            print("   Démo: demo / demo123")
            print("   Admin: admin / admin123")

# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    app.run(
        debug=os.environ.get('FLASK_DEBUG') == '1',
        host='127.0.0.1',
        port=5000,
        use_reloader=True
    )
