from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
import json
from .models import Champion, RiotApiKey, MatchChampion, ServerInfo
from .serializers import ChampionSerializer, ChampionStatisticsSerializer
from LolStatsServer.model.statistics import ChampionStatistics
from LolStatsServer.model.collecting_data import CollectData
from riotwatcher import RiotWatcher, ApiError


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


# collecting data object
collectData = CollectData()


class StartAnalyzeGames(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        # initialize object if not exists
        if ServerInfo.objects.all().__len__() == 0:
            server_info = ServerInfo(game_analyzed=0, game_analyzed_from_start=0, analyze_running=True, analyze_info='Admin started analyze')
            server_info.save()
        # run background task
        if collectData.process is None:
            server_info = ServerInfo.objects.all()[0]
            server_info.game_analyzed_from_start = 0
            server_info.analyze_running = True
            server_info.analyze_info = 'Admin started analyze'
            server_info.save()
            collectData.start_analyze(5)
            response_data['message'] = 'Analyze was started'
        else:
            response_data['message'] = 'Analyze already running!'

        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)


class StopAnalyzeGames(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        if collectData.process is not None:
            # stop background task
            collectData.stop_analyze()
            server_info = ServerInfo.objects.all()[0]
            server_info.analyze_running = False
            server_info.analyze_info = 'Admin stopped analyze'
            server_info.save()
            response_data['message'] = 'Analyze was stopped'
        else:
            response_data['message'] = 'Analyze is not started!'

        return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
