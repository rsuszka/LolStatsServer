from django.db.models import Count
from LolStatsServer.models import MatchChampion, Match, MatchBan


class ChampionStatistics:
    # initialize empty statistics
    champion_name = ""
    average_kills = 0.0
    average_deaths = 0.0
    average_assists = 0.0
    average_damage_defeat = 0.0
    average_damage_to_objectives = 0.0
    average_damage_taken = 0.0
    average_gold_earned = 0.0
    average_vision_score = 0.0
    average_total_heal = 0.0
    average_champion_level = 0.0
    first_blood_kill = 0.0
    first_tower = 0.0
    lane = ""
    win_rate = 0.0
    average_game_duration = 0.0
    play_rate = 0.0
    ban_rate = 0.0
    analyzed_games = 0
    cs_per_minute = 0.0
    first_item_id = 0

    def __init__(self, champion_name):
        self.champion_name = champion_name

    def calculate(self):
        # method variables
        kills = 0
        deaths = 0
        assists = 0
        damage_defeat = 0
        damage_to_objectives = 0
        damage_taken = 0
        gold_earned = 0
        vision_score = 0
        total_heal = 0
        champion_level = 0
        first_blood_kill_counter = 0
        first_tower_counter = 0
        win_game_counter = 0
        game_duration = 0
        cs = 0

        champion_matches = MatchChampion.objects.filter(champion__name=self.champion_name)

        for matchChampion in champion_matches:
            kills += matchChampion.kills
            deaths += matchChampion.deaths
            assists += matchChampion.assists
            damage_defeat += matchChampion.damage_defeat
            damage_to_objectives += matchChampion.damage_to_objectives
            damage_taken += matchChampion.damage_taken
            gold_earned += matchChampion.gold_earned
            vision_score += matchChampion.vision_score
            total_heal += matchChampion.total_heal
            champion_level += matchChampion.champion_level
            if matchChampion.first_blood_kill:
                first_blood_kill_counter += 1
            if matchChampion.first_tower:
                first_tower_counter += 1
            if matchChampion.win:
                win_game_counter += 1
            game_duration += matchChampion.match.duration
            cs += matchChampion.cs

        number_of_matches = champion_matches.__len__()
        number_of_all_matches = Match.objects.all().__len__()
        number_of_bans = MatchBan.objects.filter(champion__name=self.champion_name).__len__()

        # most played lane
        lane_query_set = MatchChampion.objects.filter(champion__name=self.champion_name).values('lane').annotate(lane_count=Count('lane')).order_by('-lane_count')

        # first item
        first_item_query_set = MatchChampion.objects.filter(champion__name=self.champion_name).values('first_item_id').annotate(first_item_count=Count('first_item_id')).order_by('-first_item_count')

        # calculate statistics
        self.average_kills = kills / number_of_matches
        self.average_deaths = deaths / number_of_matches
        self.average_assists = assists / number_of_matches
        self.average_damage_defeat = damage_defeat / number_of_matches
        self.average_damage_to_objectives = damage_to_objectives / number_of_matches
        self.average_damage_taken = damage_taken / number_of_matches
        self.average_gold_earned = gold_earned / number_of_matches
        self.average_vision_score = vision_score / number_of_matches
        self.average_total_heal = total_heal / number_of_matches
        self.average_champion_level = champion_level / number_of_matches
        self.first_blood_kill = (first_blood_kill_counter / number_of_matches) * 100
        self.first_tower = (first_tower_counter / number_of_matches) * 100
        if lane_query_set.__len__() > 0:
            self.lane = lane_query_set[0]['lane']
        self.win_rate = (win_game_counter / number_of_matches) * 100
        self.average_game_duration = game_duration / number_of_matches
        self.play_rate = (number_of_matches / number_of_all_matches) * 100
        self.ban_rate = (number_of_bans / number_of_all_matches) * 100
        self.analyzed_games = number_of_matches
        self.cs_per_minute = cs / (game_duration / 60)
        if first_item_query_set.__len__() > 0:
            self.first_item_id = first_item_query_set[0]['first_item_id']
