from django.contrib import admin
from .models import Champion
from .models import RiotApiKey

admin.site.register(Champion)
admin.site.register(RiotApiKey)
