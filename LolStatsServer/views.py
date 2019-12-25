from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
import requests
import json
from .models import Champion, RiotApiKey, Match, MatchBan, MatchChampion, ServerInfo
from .serializers import ChampionSerializer, ChampionStatisticsSerializer
from .statistics import ChampionStatistics
from riotwatcher import RiotWatcher, ApiError
from background_task import background
import time
import subprocess
from background_task.models import Task, CompletedTask


class ProcessMemory:
    process = None

    def __init__(self, process):
        self.process = process


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
        try:
            response_data = {}
            region = 'euw1'
            watcher = RiotWatcher(RiotApiKey.objects.all()[0].api_key)
            version_json = watcher.data_dragon.versions_for_region(region)
            champions_version = version_json['n']['champion']
            champions_json = watcher.data_dragon.champions(champions_version)
            # delete old champions list
            Champion.objects.all().delete()
            # create new champions list
            for champion in champions_json['data']:
                key = champions_json['data'][champion]['key']
                name = champions_json['data'][champion]['name'].lower()
                new_champion = Champion(champion_id=key, name=name)
                new_champion.save()
            # create response
            response_data['message'] = 'Champions reloaded successful'
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

        except ApiError:
            response_data['message'] = 'Other server error'
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)


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
                                        win = participant_stats['win']
                                        stated_champion = Champion.objects.filter(champion_id=participant['championId'])[0]
                                        new_participant = MatchChampion(match=new_match, champion=stated_champion, kills=kills, deaths=deaths, assists=assists,
                                                                        damage_defeat=damage_defeat, damage_to_objectives=damage_to_objectives, damage_taken=damage_taken,
                                                                        gold_earned=gold_earned, vision_score=vision_score, total_heal=total_heal,
                                                                        champion_level=champion_level, first_blood_kill=first_blood_kill, first_tower=first_tower,
                                                                        lane=lane, win=win)
                                        new_participant.save()
                        break

    def post(self):
        pass


class GetStatisticsFromChampion(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        try:
            champion_name = request.GET['name'].lower()
            if MatchChampion.objects.filter(champion__name=champion_name).__len__() > 0:
                # calculate champion statistics
                champion_statistics = ChampionStatistics(champion_name=champion_name)
                champion_statistics.calculate()
                champion_statistics_serializer = ChampionStatisticsSerializer(champion_statistics)
                return Response(champion_statistics_serializer.data)
            else:
                response_data['message'] = 'Wrong champion name'
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=404)

        except MultiValueDictKeyError:
            response_data['message'] = 'Required String parameter "name" is not present'
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        except:
            response_data['message'] = 'Other server error'
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)


class GetStatisticsFromUser(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        try:
            summoner_name = request.GET['name']
            region = request.GET['region']
            watcher = RiotWatcher(RiotApiKey.objects.all()[0].api_key)
            account_data = watcher.summoner.by_name(region, summoner_name)
            mastery_data = watcher.champion_mastery.by_summoner(region, account_data['id'])
            mastery_scores_data = watcher.champion_mastery.scores_by_summoner(region, account_data['id'])
            summoner_history = watcher.match.matchlist_by_account(region, account_data['accountId'])
            response_data['name'] = account_data['name']
            response_data['profile_icon_id'] = account_data['profileIconId']
            response_data['summoner_level'] = account_data['summonerLevel']
            response_data['mastery_score'] = mastery_scores_data
            response_data['masteries'] = mastery_data
            response_data['history'] = summoner_history['matches']
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

        except MultiValueDictKeyError:
            response_data['message'] = 'Required String parameters "name" and "region" are not present'
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        except ApiError as err:
            if err.response.status_code == 429:
                response_data['message'] = 'Riot Api server is unavailable. Try later'
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=429)
            elif err.response.status_code == 404:
                response_data['message'] = 'Wrong summoner name or region'
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=404)
            else:
                response_data['message'] = 'Other server error'
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)


processMemory = ProcessMemory(None)


class StartAnalyzeGames(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        # initialize object if not exists
        if ServerInfo.objects.all().__len__() == 0:
            server_info = ServerInfo(game_analyzed=0, game_analyzed_from_start=0, analyze_running=True, analyze_info='Admin started analyze')
            server_info.save()
        # run background task
        if processMemory.process is None:
            server_info = ServerInfo.objects.all()[0]
            server_info.game_analyzed_from_start = 0
            server_info.analyze_running = True
            server_info.analyze_info = 'Admin started analyze'
            server_info.save()
            start_analyze(schedule=5)
            process = subprocess.Popen(['python', 'manage.py', 'process_tasks'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processMemory.process = process
            response_data['message'] = 'Analyze was started'
        else:
            response_data['message'] = 'Analyze already running!'

        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)


class StopAnalyzeGames(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        if processMemory.process is not None:
            # stop background task
            processMemory.process.terminate()
            processMemory.process = None
            server_info = ServerInfo.objects.all()[0]
            server_info.analyze_running = False
            server_info.analyze_info = 'Admin stopped analyze'
            server_info.save()
            Task.objects.all().delete()
            CompletedTask.objects.all().delete()
            response_data['message'] = 'Analyze was stopped'
        else:
            response_data['message'] = 'Analyze is not started!'

        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)


@background(schedule=10)
def start_analyze():
    current_server_info = ServerInfo.objects.all()[0]
    while True:
        current_server_info.game_analyzed += 1
        current_server_info.game_analyzed_from_start += 1
        current_server_info.save()
        current_server_info = ServerInfo.objects.all()[0]
        time.sleep(1)
