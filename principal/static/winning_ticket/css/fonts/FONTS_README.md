# 📁 Fonts — Guide d'installation

## Structure à créer dans ton projet Django

```
ton_projet/
├── static/
│   └── fonts/
│       ├── syne-700.woff        ← Police titres (Bold)
│       ├── syne-800.woff        ← Police titres (ExtraBold)
│       ├── dm-sans-400.woff     ← Police body (Regular)
│       └── dm-sans-600.woff     ← Police body (SemiBold)
└── templates/
    └── base/
        └── base.html            ← Déjà configuré ✅
```

## Étapes d'installation

### 1. Copier les fichiers woff
Prends les 4 fichiers `.woff` fournis et place-les dans :
```
ton_app/static/fonts/
```

### 2. Vérifier STATIC_DIRS dans settings.py
```python
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_URL = '/static/'
```

### 3. Collecter les fichiers (en production)
```bash
python manage.py collectstatic
```

## Comment ça fonctionne

Le `base.html` charge les fonts dans cet ordre (4 niveaux de fallback) :

| Niveau | Source | Fiabilité |
|--------|--------|-----------|
| 1 | Fichiers locaux Django (`/static/fonts/`) | ✅ 100% — zéro réseau |
| 2 | Bunny Fonts CDN | 🟡 Réseau requis |
| 3 | Google Fonts CDN | 🟡 Réseau requis |
| 4 | `Segoe UI` / `SF Pro` / `Arial` | ✅ 100% — fonts système |

**Note sur les fonts utilisées :**
Les fichiers `.woff` fournis sont basés sur **Poppins** (Google Font libre),
une police sans-serif géométrique moderne très similaire à Syne/DM Sans.
Elle s'affichera de manière propre et professionnelle sur tous les OS.

Si tu veux les vraies Syne et DM Sans :
1. Va sur https://fonts.google.com
2. Télécharge "Syne" et "DM Sans" (bouton Download family)
3. Convertis les .ttf en .woff sur https://fontsquirrel.com/tools/webfont-generator
4. Remplace les fichiers dans `static/fonts/`
