from django.contrib import admin
from .models import Champion, RiotApiKey, Match, MatchBan, MatchChampion, ServerInfo, Queue, ServerLog


class ChampionAdmin(admin.ModelAdmin):
    list_display = ["champion_id", "name"]
    change_list_template = 'champions_change_list.html'


class QueueAdmin(admin.ModelAdmin):
    list_display = ["queue_id", "map", "description", "notes"]
    change_list_template = 'queues_change_list.html'


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


class ServerInfoAdmin(admin.ModelAdmin):
    list_display = ["id", "game_analyzed", "game_analyzed_from_start", "analyze_running", "analyze_info",
                    "tier_to_analyze", "division_to_analyze", "start_page", "end_page"]
    change_list_template = 'server_info_change_list.html'


class ServerLogAdmin(admin.ModelAdmin):
    list_display = ["id", "tier", "division", "page", "date_time", "note"]


admin.site.register(Champion, ChampionAdmin)
admin.site.register(Queue, QueueAdmin)
admin.site.register(RiotApiKey, RiotApiKeyAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(MatchBan, MatchBanAdmin)
admin.site.register(MatchChampion, MatchChampionAdmin)
admin.site.register(ServerInfo, ServerInfoAdmin)
admin.site.register(ServerLog, ServerLogAdmin)
