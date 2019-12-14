from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
import requests
import json
from .models import Champion, RiotApiKey, Match, MatchBan, MatchChampion
from .serializers import ChampionSerializer


class GetChampionsList(APIView):

    @staticmethod
    def get(request):
        champions = Champion.objects.all()
        serializer = ChampionSerializer(champions, many=True)
        return Response(serializer.data)

    def post(self):
        pass


class ReloadChampions(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        champions_response = requests.get('http://ddragon.leagueoflegends.com/cdn/9.24.1/data/en_US/champion.json')
        if champions_response.status_code == 200:
            # delete old champions list
            for champion in Champion.objects.all():
                champion.delete()
            # create new champions list
            response_json = champions_response.json()
            for champion in response_json['data']:
                key = response_json['data'][champion]['key']
                name = response_json['data'][champion]['name']
                new_champion = Champion(champion_id=key, name=name)
                new_champion.save()
            # create response
            response_data['result'] = 'ok'
            response_data['message'] = 'champions reloaded successful'
        else:
            # create response
            response_data['result'] = 'error'
            response_data['message'] = 'status code ' + str(champions_response.status_code)

        return HttpResponse(json.dumps(response_data), content_type="application/json")

    def post(self):
        pass


class LoadDataFromRioApi(APIView):

    # TODO code review
    @staticmethod
    def get(request):
        response_data = {}
        # load ranked queue
        division = 'I'
        tier = 'GOLD'
        queue = 'RANKED_SOLO_5x5'
        ranked_queue_link = 'https://eun1.api.riotgames.com/lol/league/v4/entries/' + queue + '/' + tier + '/' + division + '?api_key=' + RiotApiKey.objects.all()[0].api_key
        ranked_queue_response = requests.get(ranked_queue_link)
        if ranked_queue_response.status_code == 200:
            ranked_queue_json = ranked_queue_response.json()
            for summoner in ranked_queue_json:
                summoner_name = summoner['summonerName']
                # load summoner account id
                summoner_link = 'https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + summoner_name + '?api_key=' + RiotApiKey.objects.all()[0].api_key
                summoner_response = requests.get(summoner_link)
                if summoner_response.status_code == 200:
                    summoner_response_json = summoner_response.json()
                    account_id = summoner_response_json['accountId']
                    # load summoner history
                    history_link = 'https://eun1.api.riotgames.com/lol/match/v4/matchlists/by-account/' + account_id + '?api_key=' + RiotApiKey.objects.all()[0].api_key
                    history_response = requests.get(history_link)
                    if history_response.status_code == 200:
                        history_json = history_response.json()
                        for match in history_json['matches']:
                            match_link = 'https://eun1.api.riotgames.com/lol/match/v4/matches/' + str(match['gameId']) + '?api_key=' + RiotApiKey.objects.all()[0].api_key
                            match_response = requests.get(match_link)
                            if match_response.status_code == 200:
                                match_response_json = match_response.json()
                                if match_response_json['queueId'] == 400 or match_response_json['queueId'] == 420: # normal and soloduo
                                    # create match
                                    game_id = match_response_json['gameId']
                                    queue_id = match_response_json['queueId']
                                    game_version = match_response_json['gameVersion']
                                    duration = match_response_json['gameDuration']
                                    new_match = Match(game_id=game_id, queue_id=queue_id, game_version=game_version, duration=duration)
                                    new_match.save()
                                    # save bans
                                    for team in match_response_json['teams']:
                                        for ban in team['bans']:
                                            banned_champion = Champion.objects.filter(champion_id=ban['championId'])[0]
                                            new_match_ban = MatchBan(match=new_match, champion=banned_champion)
                                            new_match_ban.save()
                                    # save champions statistics
                                    for participant in match_response_json['participants']:
                                        participant_stats = participant['stats']
                                        kills = participant_stats['kills']
                                        deaths = participant_stats['deaths']
                                        assists = participant_stats['assists']
                                        damage_defeat = participant_stats['totalDamageDealt']
                                        damage_to_objectives = participant_stats['damageDealtToObjectives']
                                        damage_taken = participant_stats['totalDamageTaken']
                                        gold_earned = participant_stats['goldEarned']
                                        vision_score = participant_stats['visionScore']
                                        total_heal = participant_stats['totalHeal']
                                        champion_level = participant_stats['champLevel']
                                        first_blood_kill = participant_stats['firstBloodKill']
                                        first_tower = participant_stats['firstTowerKill']
                                        lane = participant['timeline']['lane']
                                        stated_champion = Champion.objects.filter(champion_id=participant['championId'])[0]
                                        new_participant = MatchChampion(match=new_match, champion=stated_champion, kills=kills, deaths=deaths, assists=assists,
                                                                        damage_defeat=damage_defeat, damage_to_objectives=damage_to_objectives, damage_taken=damage_taken,
                                                                        gold_earned=gold_earned, vision_score=vision_score, total_heal=total_heal,
                                                                        champion_level= champion_level, first_blood_kill=first_blood_kill, first_tower=first_tower, lane=lane)
                                        new_participant.save()
                                    break

    def post(self):
        pass
