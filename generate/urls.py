from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.getNounLexicon),
    path('bulkUpload/', views.bulkImageUpload),
    path('newLexicon/<str:mode>/', views.generateLexicon, name='newLexicon'),
    path('game/<str:mode>/', views.startGameView, name='start'),
    path('displayAll/<str:mode>/', views.viewDictionary, name="displayAll"),
    path('popups/', views.generatePopups, name='popups'),
    path('transparent/', views.transparentImages, name='transparent'),
    path('links/', views.linksView, name='links'),
]