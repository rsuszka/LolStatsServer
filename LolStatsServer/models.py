from django.db import models


class Champion(models.Model):
    champion_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Champion"
        verbose_name_plural = "Champions"


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

    class Meta:
        verbose_name = "MatchChampion"
        verbose_name_plural = "MatchChampions"


class ServerInfo(models.Model):
    game_analyzed = models.IntegerField()
    game_analyzed_from_start = models.IntegerField()
    analyze_running = models.BooleanField()
    analyze_info = models.CharField(max_length=10000)

    class Meta:
        verbose_name = "ServerInfo"
        verbose_name_plural = "ServerInfo"
