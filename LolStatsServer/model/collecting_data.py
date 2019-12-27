from background_task import background
import time
import subprocess
from background_task.models import Task, CompletedTask
from riotwatcher import RiotWatcher
from LolStatsServer.models import Champion, RiotApiKey, Match, MatchBan, MatchChampion, ServerInfo


class CollectData:
    process: subprocess

    def __init__(self):
        self.process = None

    @background(schedule=10)
    def __background_analyze():
        try:
            # load ranked queue
            watcher = RiotWatcher(RiotApiKey.objects.all()[0].api_key)
            region = 'eun1'
            division = 'I'
            tier = 'GOLD'
            queue = 'RANKED_SOLO_5x5'
            # analyze 10 pages of summoners (each page contains 204 summoners)
            for page in range(1, 11):
                ranked_queue = watcher.league.entries(region, queue, tier, division, page)
                for summoner in ranked_queue:
                    try:
                        summoner_name = summoner['summonerName']
                        # load summoner account id
                        summoner_info = watcher.summoner.by_name(region, summoner_name)
                        account_id = summoner_info['accountId']
                        # load summoner history
                        summoner_history = watcher.match.matchlist_by_account(region, account_id)
                        match_by_summoner_counter = 0
                        for match in summoner_history['matches']:
                            try:
                                match_id = match['gameId']
                                analyzed_match = watcher.match.by_id(region, match_id)
                                queue_id = analyzed_match['queueId']
                                duration = analyzed_match['gameDuration']
                                game_id = analyzed_match['gameId']
                                match_in_database = Match.objects.filter(game_id=game_id)
                                if (queue_id == 400 or queue_id == 420) and duration > 250 and len(match_in_database) == 0:  # draft or soloduo
                                    # create match
                                    game_version = analyzed_match['gameVersion']
                                    new_match = Match(game_id=game_id, queue_id=queue_id, game_version=game_version, duration=duration)
                                    new_match.save()
                                    # save bans
                                    for team in analyzed_match['teams']:
                                        for ban in team['bans']:
                                            banned_champion_id = ban['championId']
                                            if banned_champion_id != -1:
                                                banned_champion = Champion.objects.filter(champion_id=banned_champion_id)[0]
                                                new_match_ban = MatchBan(match=new_match, champion=banned_champion)
                                                new_match_ban.save()
                                    # save champions statistics
                                    for participant in analyzed_match['participants']:
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
                                        new_participant = MatchChampion(match=new_match, champion=stated_champion, kills=kills,
                                                                        deaths=deaths, assists=assists,
                                                                        damage_defeat=damage_defeat,
                                                                        damage_to_objectives=damage_to_objectives,
                                                                        damage_taken=damage_taken,
                                                                        gold_earned=gold_earned, vision_score=vision_score,
                                                                        total_heal=total_heal,
                                                                        champion_level=champion_level,
                                                                        first_blood_kill=first_blood_kill,
                                                                        first_tower=first_tower,
                                                                        lane=lane, win=win)
                                        new_participant.save()

                                    match_by_summoner_counter += 1
                                    # actualize collecting statistics
                                    server_info = ServerInfo.objects.all()[0]
                                    server_info.game_analyzed += 1
                                    server_info.game_analyzed_from_start += 1
                                    server_info.save()
                                    # sleep not to exceed the query limit
                                    time.sleep(1)
                                    if match_by_summoner_counter > 1:
                                        break

                            # error in match
                            except Exception as err:
                                a = 5
                                # TODO add logs

                    # error in loading summoner account or history
                    except Exception as err:
                        a = 5
                        # TODO add logs

            # actualize server info
            server_info = ServerInfo.objects.all()[0]
            server_info.analyze_running = False
            server_info.analyze_info = 'Algorithm end'
            server_info.save()

        # error in loading league
        except Exception as err:
            server_info = ServerInfo.objects.all()[0]
            server_info.analyze_running = False
            server_info.analyze_info = 'Error. Server error'
            server_info.save()

    def start_analyze(self, schedule: int):
        self.__background_analyze(schedule=schedule)
        self.process = subprocess.Popen(['python', 'manage.py', 'process_tasks'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop_analyze(self):
        self.process.terminate()
        self.process = None
        Task.objects.all().delete()
        CompletedTask.objects.all().delete()
