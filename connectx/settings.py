import os
import sys
from pathlib import Path
import environ

# Initialisation d'environ
env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Lecture du fichier .env s'il existe
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Ajoute apps/ au chemin Python pour référencer les apps sans préfixe
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Force psycopg2 à recevoir les messages PostgreSQL en UTF-8
os.environ.setdefault('PGCLIENTENCODING', 'UTF8')
os.environ.setdefault('PGSSLMODE', 'prefer')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-9gu-@^oxsc)%^qt3m=ksz_#%ve7j+^s8+k*(!f6)1a!y9_4w%^')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])


# Application definition

INSTALLED_APPS = [
    # Daphne doit être en premier (avant staticfiles)
    'daphne',

    # Jazzmin doit être avant django.contrib.admin
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'channels',
    'crispy_forms',
    'crispy_bootstrap5',

    # Apps ConnectX
    'core',
    'accounts',
    'posts',
    'social',
    'chat',
    'notifications',
    'stories',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise pour les fichiers statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'connectx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'chat.context_processors.unread_messages_count',
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'connectx.wsgi.application'
ASGI_APPLICATION = 'connectx.asgi.application'

# Channel layer
if env('REDIS_URL', default=None):
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [env('REDIS_URL')],
            },
        }
    }
else:
    # Channel layer en mémoire (dev uniquement)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }


# Base de données
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgresql://postgres:toor@localhost:5432/connectx_db')
}


# Authentification

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:profile'
LOGOUT_REDIRECT_URL = 'accounts:login'


# Validation des mots de passe

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalisation

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True


# Fichiers statiques

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Création du dossier static s'il n'existe pas pour éviter l'avertissement W004
if not os.path.exists(STATIC_ROOT):
    os.makedirs(STATIC_ROOT)

# Optimisation WhiteNoise
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Empêche WhiteNoise de planter si un fichier référencé (ex: .map) est manquant
WHITENOISE_MANIFEST_STRICT = False


# Fichiers media (images uploadées)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# ─── Jazzmin — Dashboard Admin ────────────────────────────────────────────────

JAZZMIN_SETTINGS = {
    # Titre et branding
    'site_title': 'ConnectX Admin',
    'site_header': 'ConnectX',
    'site_brand': 'ConnectX',
    'site_logo': None,
    'login_logo': None,
    'site_icon': None,
    'welcome_sign': 'Bienvenue dans le panneau d\'administration ConnectX',
    'copyright': 'ConnectX — Tous droits réservés',

    # Recherche globale dans ces modèles
    'search_model': ['accounts.User', 'posts.Post'],

    # Champ affiché pour l'utilisateur connecté
    'user_avatar': None,

    # Menu latéral
    'topmenu_links': [
        {'name': 'Accueil', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'Voir le site', 'url': '/', 'new_window': True},
    ],

    'usermenu_links': [
        {'name': 'Voir le site', 'url': '/', 'new_window': True},
    ],

    # Sidebar
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],

    # Ordre des apps dans la sidebar
    'order_with_respect_to': [
        'accounts', 'posts', 'social', 'chat', 'auth',
    ],

    # Icônes par app et modèle (Font Awesome 5)
    'icons': {
        'auth':                     'fas fa-users-cog',
        'auth.Group':               'fas fa-layer-group',
        'accounts.User':            'fas fa-user',
        'accounts.Profile':         'fas fa-id-card',
        'posts.Post':               'fas fa-newspaper',
        'posts.Comment':            'fas fa-comments',
        'posts.Like':               'fas fa-heart',
        'posts.PostImage':          'fas fa-images',
        'social.Follow':            'fas fa-user-plus',
        'chat.Conversation':        'fas fa-envelope',
        'chat.Message':             'fas fa-comment-dots',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',

    # Interface
    'related_modal_active': True,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': False,
    'show_ui_builder': False,

    # Formulaires
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'auth.user': 'collapsible',
        'auth.group': 'vertical_tabs',
    },
}

JAZZMIN_UI_TWEAKS = {
    # Thème général
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-danger',       # rouge ConnectX
    'accent': 'accent-danger',
    'navbar': 'navbar-dark',
    'no_navbar_border': True,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-danger',      # sidebar sombre rouge
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'flatly',                     # thème Bootstrap clair
    'dark_mode_theme': 'flatly',
    'button_classes': {
        'primary':   'btn-primary',
        'secondary': 'btn-secondary',
        'info':      'btn-info',
        'warning':   'btn-warning',
        'danger':    'btn-danger',
        'success':   'btn-success',
    },
}
