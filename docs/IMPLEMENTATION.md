# ConnectX - Architecture globale et modèles principaux

Je te propose de partir sur une architecture Django en apps métiers séparées. Comme ton projet est encore très propre au départ, on peut construire quelque chose de modulaire dès le début, sans dette technique inutile.

## Architecture globale

Structure recommandée :

```text
connectx/
├── manage.py
├── config/                      # ou garder "connectx/" comme dossier config
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/                # utilisateurs, profils, auth
│   ├── posts/                   # publications, likes, commentaires
│   ├── social/                  # follow / unfollow
│   ├── chat/                    # conversations, messages, websocket
│   ├── notifications/           # bonus temps réel
│   └── stories/                 # bonus
├── media/                       # images uploadées
├── static/
├── templates/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── .env
```

Découpage conseillé des apps :

- `accounts` : `CustomUser`, `Profile`, inscription, connexion, page profil.
- `posts` : publications, images, likes, commentaires.
- `social` : système de follow/followers/following.
- `chat` : conversations privées, messages, WebSockets avec Django Channels.
- `notifications` : notifications de like, commentaire, follow, message.
- `stories` : publications temporaires si tu veux le bonus plus tard.

## Pourquoi cette architecture est bonne

- Chaque app a une responsabilité claire.
- Tu peux faire évoluer une fonctionnalité sans casser tout le projet.
- C’est plus simple à tester et à maintenir.
- C’est compatible avec une montée en complexité future.

## Modèles principaux

Je te recommande fortement un `CustomUser` dès le début, pour éviter les limites du `User` natif plus tard.

### 1. `accounts`

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    is_online = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username
```

Option plus propre encore : garder `User` léger et mettre le reste dans `Profile`.

```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"
```

Recommandation :

- `User` : identité/authentification.
- `Profile` : infos sociales et affichage.

### 2. `posts`

```python
from django.conf import settings
from django.db import models


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    def __str__(self):
        return f"Post {self.id} by {self.author}"
```

Pour les images, mieux vaut un modèle séparé :

```python
class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="posts/")
    alt_text = models.CharField(max_length=255, blank=True)
```

Like :

```python
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
```

Commentaire :

```python
class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3. `social`

```python
from django.conf import settings
from django.db import models


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
```

Règles métier importantes :

- Un utilisateur ne peut pas se follow lui-même.
- Une relation `follower -> following` doit être unique.

### 4. `chat`

Pour une messagerie propre et scalable, évite un simple modèle `Message` sans conversation. Il vaut mieux structurer ainsi :

```python
class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

```python
class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
```

Pourquoi ce modèle est meilleur :

- Il permet la discussion privée à 2 utilisateurs.
- Il pourra aussi supporter les groupes plus tard.
- Il s’intègre très bien avec Django Channels.

## Relations principales

Résumé simple :

- `User 1---1 Profile`
- `User 1---N Post`
- `Post 1---N PostImage`
- `User N---N Post` via `Like`
- `Post 1---N Comment`
- `User N---N User` via `Follow`
- `Conversation N---N User`
- `Conversation 1---N Message`
- `User 1---N Message` comme expéditeur

## Ordre de développement recommandé

Je te conseille cet ordre pour rester progressif :

1. `accounts`
   - CustomUser
   - inscription / connexion / profil

2. `posts`
   - création de post
   - affichage feed
   - upload image

3. `likes` et `comments`
   - interactions de base

4. `social`
   - follow / unfollow
   - liste followers/following

5. `chat`
   - conversations
   - messages classiques
   - puis WebSockets avec Channels

6. bonus
   - notifications
   - stories
   - recommandations
   - analytics

## Bonnes pratiques dès maintenant

- Utiliser `AUTH_USER_MODEL` partout, jamais `User` en dur.
- Séparer les apps par domaine métier.
- Prévoir `created_at` / `updated_at` sur les modèles importants.
- Ajouter des contraintes d’unicité pour éviter les doublons.
- Utiliser un modèle séparé pour les images d’un post.
- Préparer `asgi.py` proprement pour Django Channels.
- Utiliser PostgreSQL si possible, surtout pour un projet sérieux.
- Stocker secrets et config dans `.env`.
- Commencer simple côté frontend, mais garder une API/architecture propre.

## Ma recommandation concrète

Commence avec ces 4 apps obligatoires :

- `accounts`
- `posts`
- `social`
- `chat`

Puis ajoute `notifications` plus tard.

Si tu veux, à l’étape suivante je peux te construire le squelette exact du projet Django avec :

- la liste des apps à créer,
- les commandes Django,
- les modèles complets,
- et l’ordre précis des fichiers à coder en premier.


Pour l'audit, je propose la création d'une classe BaseEntity dont héritera toutes les classes. Voici un extrait de code Java
que j'utilise dans tous mes projets. Tu peux t'en inspirer. On n'exposera pas le id séquentiel dans notre application. A la place,
on exposera le publicId :

public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @JsonIgnore
    private Long id;

    @Column(name = "public_id", nullable = false, unique = true, updatable = false)
    private String publicId = UUID.randomUUID().toString();

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @CreatedBy
    @Column(name = "created_by", updatable = false)
    private String createdBy;

    @LastModifiedBy
    @Column(name = "updated_by")
    private String updatedBy;

    @Column(nullable = false)
    private Boolean deleted = false;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @Column(name = "deleted_by")
    private String deletedBy;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (updatedAt == null) {
            updatedAt = LocalDateTime.now();
        }
        if (publicId == null) {
            publicId = UUID.randomUUID().toString();
        }
        if (deleted == null) {
            deleted = false;
        }
        if (createdBy == null) {
            createdBy = "SYSTEM";
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
