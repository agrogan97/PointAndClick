from rest_framework import serializers

class SceneSerializer(serializers.Serializer):
    num = serializers.CharField(max_length=500)
    BackgroundImage = serializers.ImageField()
    ConnectedScenes = serializers.CharField(max_length=12)
    NumHotspots = serializers.IntegerField()

class HotspotSerializer(serializers.Serializer):
    num =serializers.CharField(max_length=12)
    parent =serializers.CharField(max_length=12)
    x =serializers.IntegerField()
    y =serializers.IntegerField()
    Teleport =serializers.BooleanField()
    TeleportToScene =serializers.IntegerField()
    ShowImage =serializers.ImageField()