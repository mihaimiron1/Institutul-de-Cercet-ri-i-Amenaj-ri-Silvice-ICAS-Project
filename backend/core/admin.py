from django.contrib import admin
from .models import Reserve, Species, Association, Occurrence, ReserveAssociationYear

admin.site.register(Reserve)
admin.site.register(Species)
admin.site.register(Association)
admin.site.register(Occurrence)
admin.site.register(ReserveAssociationYear)
