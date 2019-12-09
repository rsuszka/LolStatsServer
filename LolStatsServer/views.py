from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
import requests
import json
from .models import Champion as Champions
from .serializers import ChampionSerializer


class GetChampionsList(APIView):

    @staticmethod
    def get(request):
        champions = Champions.objects.all()
        serializer = ChampionSerializer(champions, many=True)
        return Response(serializer.data)

    def post(self):
        pass


class ReloadChampions(APIView):

    @staticmethod
    def get(request):
        response_data = {}
        champions_response = requests.get('http://ddragon.leagueoflegends.com/cdn/9.23.1/data/en_US/champion.json')
        if champions_response.status_code == 200:
            # delete old champions list
            for champion in Champions.objects.all():
                champion.delete()
            # create new champions list
            response_json = champions_response.json()
            for champion in response_json['data']:
                key = response_json['data'][champion]['key']
                name = response_json['data'][champion]['name']
                Champions.objects.create(champion_id=key, name=name)
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
