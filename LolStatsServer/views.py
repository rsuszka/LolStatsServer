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
            # collecting summoner data from riot api
            watcher = RiotWatcher(RiotApiKey.objects.all()[0].api_key)
            account_data = watcher.summoner.by_name(region, summoner_name)
            mastery_data = watcher.champion_mastery.by_summoner(region, account_data['id'])
            mastery_scores_data = watcher.champion_mastery.scores_by_summoner(region, account_data['id'])
            summoner_history = watcher.match.matchlist_by_account(region, account_data['accountId'])
            leagues_data = watcher.league.by_summoner(region, account_data['id'])

            # process data
            # process last 5 history games
            history_game_counter = 1
            match_table = []
            for history_game in summoner_history['matches']:
                game_object = {}
                game = watcher.match.by_id(region, history_game['gameId'])
                game_object['game_duration'] = game['gameDuration']
                game_object['map_id'] = game['mapId']  # TODO change id to name
                participant_id = 1
                for participant_identities in game['participantIdentities']:
                    if participant_identities['player']['summonerName'].lower() == summoner_name.lower():
                        participant_id = participant_identities['participantId']
                        break
                champion_info = game['participants'][participant_id - 1]['stats']
                game_object['kills'] = champion_info['kills']
                game_object['deaths'] = champion_info['deaths']
                game_object['assists'] = champion_info['assists']
                game_object['cs'] = champion_info['totalMinionsKilled']
                game_object['win'] = champion_info['win']
                game_object['champion_name'] = Champion.objects.filter(champion_id=game['participants'][participant_id - 1]['championId'])[0].name
                match_table.append(game_object)
                history_game_counter += 1
                if history_game_counter > 5:
                    break

            mastery_table = []
            for champion_mastery in mastery_data:
                mastery_object = {
                    'champion_name': Champion.objects.filter(champion_id=champion_mastery['championId'])[0].name,
                    'champion_level': champion_mastery['championLevel'],
                    'champion_points': champion_mastery['championPoints'],
                    'chest granted': champion_mastery['chestGranted'],
                    'tokens_earned': champion_mastery['tokensEarned']}
                mastery_table.append(mastery_object)

            leagues_table = []
            for champion_league in leagues_data:
                league_object = {'queue_type': champion_league['queueType'].replace('_', ' '),
                                 'tier': champion_league['tier'],
                                 'rank': champion_league['rank'],
                                 'lp': champion_league['leaguePoints'],
                                 'played': champion_league['wins'] + champion_league['losses'],
                                 'wins': champion_league['wins'],
                                 'losses': champion_league['losses'],
                                 'win_rate': champion_league['wins'] / (champion_league['wins'] + champion_league['losses']) * 100}
                leagues_table.append(league_object)

            # create response
            response_data['name'] = account_data['name']
            response_data['profile_icon_id'] = account_data['profileIconId']
            response_data['summoner_level'] = account_data['summonerLevel']
            response_data['mastery_score'] = mastery_scores_data
            response_data['masteries'] = mastery_table
            response_data['history'] = match_table
            response_data['rankeds'] = leagues_table
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
                response_data['message'] = 'Other api error [' + str(err.response.status_code) + ']'
                return HttpResponse(json.dumps(response_data), content_type="application/json", status=500)

        except Exception:
            response_data['message'] = 'Other server error'
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=501)


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
