from django.contrib import admin
from .models import Porcelain, VideoGame,VinylRecord,BoardGame,Book

admin.site.register(Porcelain)
admin.site.register(VideoGame)
admin.site.register(Book)
admin.site.register(VinylRecord)
admin.site.register(BoardGame)