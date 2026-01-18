from django.db import models
from pgvector.django import VectorField

from arbitrage_agent.core.constants import EMBEDDING_SIZE

class NewsArticle(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    url = models.URLField(unique=True)
    published_at = models.DateTimeField()

    embedding = VectorField(dimensions=EMBEDDING_SIZE, null=True, blank=True)

    def __str__(self):
        return self.title
