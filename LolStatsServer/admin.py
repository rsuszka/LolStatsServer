from django.contrib import admin
from .models import Champion, RiotApiKey, Match, MatchBan, MatchChampion


class ChampionAdmin(admin.ModelAdmin):
    list_display = ["champion_id", "name"]


class RiotApiKeyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in RiotApiKey._meta.get_fields()]


class MatchAdmin(admin.ModelAdmin):
    list_display = ["id", "game_id", "queue_id", "game_version", "duration"]


class MatchBanAdmin(admin.ModelAdmin):
    list_display = ["id", "match_id", "champion_id"]


class MatchChampionAdmin(admin.ModelAdmin):
    list_display = ["id", "match_id", "champion_id", "kills", "deaths", "assists", "damage_defeat",
                    "damage_to_objectives", "damage_taken", "gold_earned", "vision_score", "total_heal",
                    "champion_level", "first_blood_kill", "first_tower", "lane"]


admin.site.register(Champion, ChampionAdmin)
admin.site.register(RiotApiKey, RiotApiKeyAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(MatchBan, MatchBanAdmin)
admin.site.register(MatchChampion, MatchChampionAdmin)
