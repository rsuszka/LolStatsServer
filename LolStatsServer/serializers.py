from rest_framework import serializers
from .models import Champion


class ChampionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Champion
        fields = '__all__'


class ChampionStatisticsSerializer(serializers.Serializer):
    champion_name = serializers.CharField()
    average_kills = serializers.FloatField()
    average_deaths = serializers.FloatField()
    average_assists = serializers.FloatField()
    average_damage_defeat = serializers.FloatField()
    average_damage_to_objectives = serializers.FloatField()
    average_damage_taken = serializers.FloatField()
    average_gold_earned = serializers.FloatField()
    average_vision_score = serializers.FloatField()
    average_total_heal = serializers.FloatField()
    average_champion_level = serializers.FloatField()
    first_blood_kill = serializers.FloatField()
    first_tower = serializers.FloatField()
    lane = serializers.CharField()
    win_rate = serializers.FloatField()
    average_game_duration = serializers.FloatField()
    play_rate = serializers.FloatField()
    ban_rate = serializers.FloatField()
    analyzed_games = serializers.IntegerField()
    cs_per_minute = serializers.FloatField()
    first_item_id = serializers.IntegerField()
    rune_id = serializers.IntegerField()
    rune_link = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
