"""LolStatsServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import GetChampionsList, ReloadChampions, GetStatisticsFromChampion, GetStatisticsFromUser, \
    StartAnalyzeGames, StopAnalyzeGames, ReloadQueues, GetGameVersion, ReloadRunes

urlpatterns = [
    path('', admin.site.urls),
    path('api/admin/champions/reload', ReloadChampions.as_view()),
    path('api/admin/queues/reload', ReloadQueues.as_view()),
    path('api/admin/runes/reload', ReloadRunes.as_view()),
    path('api/admin/analyze/start', StartAnalyzeGames.as_view()),
    path('api/admin/analyze/stop', StopAnalyzeGames.as_view()),
    path('api/champions', GetChampionsList.as_view()),
    path('api/game_version', GetGameVersion.as_view()),
    path('api/statistics/champion', GetStatisticsFromChampion.as_view()),
    path('api/statistics/summoner', GetStatisticsFromUser.as_view())
]
