from django.contrib import admin

from .models import Image, gameTableau, TableauBase, Word, Hotspot, Popup, Number, Modifier
# Register your models here.

admin.site.register(Image)
admin.site.register(gameTableau)
admin.site.register(TableauBase)
admin.site.register(Word)
admin.site.register(Hotspot)
admin.site.register(Popup)
admin.site.register(Number)
admin.site.register(Modifier)