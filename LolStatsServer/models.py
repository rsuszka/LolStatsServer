from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Champion(models.Model):
    champion_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Champion"
        verbose_name_plural = "Champions"


class Queue(models.Model):
    queue_id = models.IntegerField(primary_key=True)
    map = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    notes = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Queue"
        verbose_name_plural = "Queues"


class Rune(models.Model):
    rune_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    key = models.CharField(max_length=50)
    icon = models.CharField(max_length=300)

    class Meta:
        verbose_name = "Rune"
        verbose_name_plural = "Runes"


class RiotApiKey(models.Model):
    api_key = models.CharField(max_length=50)

    class Meta:
        verbose_name = "RiotApiKey"
        verbose_name_plural = "RiotApiKeys"


class Match(models.Model):
    game_id = models.IntegerField()
    queue_id = models.IntegerField()
    game_version = models.CharField(max_length=50)
    duration = models.IntegerField()

    class Meta:
        verbose_name = "Match"
        verbose_name_plural = "Matches"


class MatchBan(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "MatchBan"
        verbose_name_plural = "MatchBans"


class MatchChampion(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE)
    kills = models.IntegerField()
    deaths = models.IntegerField()
    assists = models.IntegerField()
    damage_defeat = models.IntegerField()
    damage_to_objectives = models.IntegerField()
    damage_taken = models.IntegerField()
    gold_earned = models.IntegerField()
    vision_score = models.IntegerField()
    total_heal = models.IntegerField()
    champion_level = models.IntegerField()
    first_blood_kill = models.BooleanField()
    first_tower = models.BooleanField()
    lane = models.CharField(max_length=50)
    win = models.BooleanField()
    cs = models.IntegerField()
    first_item_id = models.IntegerField()
    rune_id = models.IntegerField()

    class Meta:
        verbose_name = "MatchChampion"
        verbose_name_plural = "MatchChampions"


class ServerInfo(models.Model):
    TIER_CHOICE = (
        ('IRON', 'IRON'),
        ('BRONZE', 'BRONZE'),
        ('SILVER', 'SILVER'),
        ('GOLD', 'GOLD'),
        ('PLATINUM', 'PLATINUM'),
        ('DIAMOND', 'DIAMOND'),
    )
    DIVISION_CHOICE = (
        ('I', 'I'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
    )
    game_analyzed = models.IntegerField()
    game_analyzed_from_start = models.IntegerField()
    analyze_running = models.BooleanField()
    analyze_info = models.CharField(max_length=10000)
    tier_to_analyze = models.CharField(max_length=8, choices=TIER_CHOICE)
    division_to_analyze = models.CharField(max_length=3, choices=DIVISION_CHOICE)
    start_page = models.IntegerField(default=1, validators=[MaxValueValidator(100), MinValueValidator(1)])
    end_page = models.IntegerField(default=1, validators=[MaxValueValidator(100), MinValueValidator(1)])

    class Meta:
        verbose_name = "ServerInfo"
        verbose_name_plural = "ServerInfo"


class ServerLog(models.Model):
    tier = models.CharField(max_length=8)
    division = models.CharField(max_length=3)
    page = models.IntegerField()
    note = models.CharField(max_length=10000)
    date_time = models.DateTimeField()

    class Meta:
        verbose_name = "ServerLog"
        verbose_name_plural = "ServerLogs"
