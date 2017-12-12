from django.conf import settings
from django.db import models
from django.utils import timezone


class Post(models.Model):
    author = models.ForeignKey('auth.User',related_name='posts_created')
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(
            default=timezone.now)
    published_date = models.DateTimeField(
            blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title

# many-to-many relationship ==> l'utilisateur peut aimer multiple poste
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                        related_name='posts_liked',
                                        blank=True)


class Comment(models.Model):
    post = models.ForeignKey('poste.Post', related_name='comments')
    author = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.text