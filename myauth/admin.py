from django.contrib import admin

from myauth.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'agreement_accepted')
