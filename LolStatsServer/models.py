from django.db import models


class Champion(models.Model):
    champion_id = models.IntegerField()
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Champion"
        verbose_name_plural = "Champions"

    def __str__(self):
        return self.name


class RiotApiKey(models.Model):
    api_key = models.CharField(max_length=50)

    class Meta:
        verbose_name = "RiotApiKey"
        verbose_name_plural = "RiotApiKeys"

    def __str__(self):
        return self.api_key
