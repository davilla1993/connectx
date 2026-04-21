from django.conf import settings
from django.db import models

from core.models import BaseModel


class Post(BaseModel):
    """
    Publication principale.
    author : auteur du contenu (domaine métier)
    created_by : qui a créé l'objet en BDD (audit, hérité de BaseModel)
    Les deux sont souvent identiques, mais created_by permet de tracer
    une création via admin ou script.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(max_length=2000)
    is_edited = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'
        ordering = ['-created_at']

    def __str__(self):
        return f'Post #{self.id} — {self.author}'

    @property
    def likes_count(self):
        return self.likes.filter(is_deleted=False).count()

    @property
    def comments_count(self):
        return self.comments.filter(is_deleted=False).count()


class PostImage(BaseModel):
    """Image attachée à un post. Séparé pour supporter plusieurs images."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='posts/')
    alt_text = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Image de publication'
        verbose_name_plural = 'Images de publication'

    def __str__(self):
        return f'Image du post #{self.post_id}'


class Like(BaseModel):
    """
    Like d'un utilisateur sur un post.
    unique_together garanti en BDD. Le soft delete permet de
    "unliker" sans perdre l'historique.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        verbose_name = 'Like'
        verbose_name_plural = 'Likes'
        unique_together = ('user', 'post')

    def __str__(self):
        return f'{self.user} ❤ Post #{self.post_id}'


class Tag(BaseModel):
    """Hashtag normalisé (lowercase, sans #)."""
    name = models.CharField(max_length=64, unique=True, db_index=True)

    class Meta:
        verbose_name = 'Hashtag'
        verbose_name_plural = 'Hashtags'

    def __str__(self):
        return f'#{self.name}'


class PostTag(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='post_tags')

    class Meta:
        unique_together = ('post', 'tag')


class Mention(BaseModel):
    """Mention @username dans un post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mentions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentions_received',
    )

    class Meta:
        unique_together = ('post', 'user')


class SavedPost(BaseModel):
    """Post sauvegardé par un utilisateur."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_posts',
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='savers')

    class Meta:
        verbose_name = 'Post sauvegardé'
        verbose_name_plural = 'Posts sauvegardés'
        unique_together = ('user', 'post')


class Reaction(BaseModel):
    """Réaction étendue (like / love / haha / wow / sad / angry)."""
    LIKE = 'like'
    LOVE = 'love'
    HAHA = 'haha'
    WOW  = 'wow'
    SAD  = 'sad'
    ANGRY = 'angry'
    TYPES = [
        (LIKE, '👍'), (LOVE, '❤️'), (HAHA, '😂'),
        (WOW, '😮'), (SAD, '😢'), (ANGRY, '😡'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reactions',
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    type = models.CharField(max_length=8, choices=TYPES, default=LIKE)

    class Meta:
        unique_together = ('user', 'post')


class Comment(BaseModel):
    """Commentaire sur un post."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    is_edited = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['created_at']

    def __str__(self):
        return f'Commentaire de {self.author} sur Post #{self.post_id}'
