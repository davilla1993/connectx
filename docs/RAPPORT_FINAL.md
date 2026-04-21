# Rapport de Projet : ConnectX
**Plateforme Sociale Avancée avec Interactions Temps Réel**

---

## Informations Générales
*   **Auteur** : [Votre Nom]
*   **Formation** : M1 IA & BIG DATA
*   **Projet** : Réseau social avancé (Groupe J)
*   **Technologies** : Django, Docker, Redis, PostgreSQL, WebSockets
*   **Date** : Avril 2026

---

## 1. Résumé
ConnectX est un réseau social complet développé avec le framework Django. L'objectif principal était de concevoir une plateforme capable de gérer des flux de données asynchrones et des interactions en temps réel. Le projet intègre un système d'authentification personnalisé, un fil d'actualité dynamique, une messagerie instantanée basée sur les WebSockets, et un système de notifications. L'application est conteneurisée avec Docker et déployée sur une infrastructure Cloud (Hetzner) via Coolify, garantissant ainsi une scalabilité et une portabilité optimales. Un accent particulier a été mis sur la sécurité avec un workflow de vérification d'email strict et une gestion robuste des réinitialisations de mots de passe.

---

## 2. Introduction
### 2.1 Contexte
Dans l'ère du Web social, l'instantanéité est devenue une norme. Les utilisateurs s'attendent à recevoir des messages et des notifications sans rafraîchir leur navigateur. ConnectX répond à cette problématique en utilisant des technologies modernes comme Django Channels et Redis.

### 2.2 Problématique
Comment construire une architecture robuste capable de lier des milliers d'utilisateurs, de gérer des relations asymétriques (abonnements) et de maintenir des connexions persistantes pour le chat, le tout dans un environnement sécurisé et performant ?

---

## 3. Cahier des Charges
### 3.1 Besoins Fonctionnels
*   **Authentification et Sécurité** : Inscription avec vérification d'email obligatoire, connexion sécurisée, réinitialisation de mot de passe par email.
*   **Profils** : Personnalisation avec avatar et bannière (cover image).
*   **Social** : Système de suivi (Follow/Unfollow) et suggestions d'amis.
*   **Publications** : Partage de textes et d'images multiples.
*   **Messagerie** : Chat en temps réel avec WebSockets.
*   **Notifications** : Alertes instantanées (toasts) pour les likes, follows et messages.

### 3.2 Captures de l'Interface
#### Connexion et Inscription
L'interface de connexion est épurée, mettant en avant la sécurité et la simplicité.

![Interface de Connexion](../docs/captures/1-connexion.png)
*Figure 1 : Formulaire de connexion sécurisé.*

![Interface d'Inscription](../docs/captures/2-inscription.png)
*Figure 2 : Formulaire d'inscription avec validation en temps réel.*

---

## 4. Architecture des Données (Détails Techniques)

L'un des points forts de ConnectX réside dans sa modélisation relationnelle utilisant **PostgreSQL**.

### 4.1 Analyse détaillée des Modèles

#### A. Le module `accounts` (Gestion Identité)
Nous avons implémenté un `CustomUser` pour nous affranchir des limitations du modèle `User` natif.
*   **is_email_verified** : Champ booléen indiquant si l'utilisateur a validé son adresse.
*   **is_active** : Utilisé pour bloquer le compte tant que l'email n'est pas vérifié.
*   **Public_id (UUID)** : Pour sécuriser les URLs publiques.
*   **Modèle Profile** : Gère l'avatar, la `cover_image` (bannière), la bio et la localisation.

#### B. Le module `posts` (Contenu)
*   **Modèle Post** : Texte et métadonnées.
*   **Modèle PostImage** : Permet d'attacher plusieurs images à un post (Relation 1:N).
*   **Modèle Like** : Contrainte d'unicité (User/Post) pour éviter les doublons.

#### C. Le module `social` (Relations)
Le système d'abonnements repose sur une table de liaison `Follow`.
*   **Requête de Feed optimisée** : `Post.objects.filter(author__follower_relations__follower=user)` permet de récupérer les publications des abonnements en une seule jointure SQL.

---

## 5. Sécurité et Workflow d'Authentification

C'est l'un des piliers techniques de ConnectX. Nous avons implémenté des protocoles de sécurité de niveau industriel.

### 5.1 Workflow de Vérification d'Email Strict
Pour éviter le spam et garantir l'identité des utilisateurs :
1.  **Inscription** : Le compte est créé avec `is_active = False`.
2.  **Token de Sécurité** : Django génère un token unique et temporaire envoyé par email via le serveur SMTP Brevo.
3.  **Validation** : L'utilisateur doit cliquer sur le lien (sécurisé en HTTPS) pour activer son compte. Tant que cette étape n'est pas franchie, la connexion est impossible.

### 5.2 Réinitialisation et Changement de Mot de Passe
*   **Password Reset** : Utilisation de tokens à usage unique envoyés par email. Si le lien est intercepté après usage, il devient caduc.
*   **Password Change** : Disponible dans les paramètres du profil, exigeant la connaissance du mot de passe actuel.

### 5.3 Protections CSRF et XSS
*   **CSRF_TRUSTED_ORIGINS** : Configuration spécifique pour autoriser les requêtes sécurisées derrière le reverse proxy de Coolify.
*   **XSS** : Échappement automatique des données utilisateur dans les templates.

---

## 6. La Couche Temps Réel (WebSockets)
### 6.1 Messagerie Instantanée
Utilisation de **Django Channels** et **Redis**.

![Interface de Messagerie](../docs/captures/6-conversation%20messagerie.png)
*Figure 3 : Interface de chat bidirectionnelle.*

### 6.2 Notifications
Système de push notification via WebSocket pour informer l'utilisateur de toute interaction sans rafraîchir la page.

![Notifications](../docs/captures/7-toast%20de%20notification.png)
*Figure 4 : Système de toast pour les notifications push.*

---

## 7. Déploiement et DevOps (Journal de Bord)

Le déploiement a été réalisé sur **Hetzner Cloud** via **Coolify**.

### 7.1 Résolution des problématiques techniques
*   **Pillow** : Installation des dépendances binaires dans le Dockerfile pour le traitement d'images.
*   **WhiteNoise** : Configuration du stockage `CompressedStaticFilesStorage` pour gérer les fichiers statiques de manière performante tout en ignorant les erreurs de fichiers `.map` manquants.
*   **SMTP Brevo** : Configuration fine séparant le login technique (`9bca68001@...`) de l'expéditeur réel (`contact@gfolly.com`) pour garantir la délivrabilité des emails.

---

## 8. Conclusion
ConnectX démontre la puissance du framework Django pour construire des applications complexes, sécurisées et scalables. L'intégration de Docker et des WebSockets place ce projet au niveau des standards du web moderne.

---

## Annexes : Configuration Docker
```yaml
services:
  web:
    build: .
    environment:
      - DATABASE_URL=postgres://...
      - REDIS_URL=redis://redis:6379/0
      - EMAIL_HOST=smtp-relay.brevo.com
```
