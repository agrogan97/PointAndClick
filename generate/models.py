from django.db import models

class Image(models.Model):
    name= models.CharField(max_length=500)
    imagefile= models.FileField(upload_to='images/', null=True, verbose_name="")

    def __str__(self):
        return self.name + ": " + str(self.imagefile)

class Scene(models.Model):
    num = models.CharField(max_length=500)
    BackgroundImage = models.ImageField()
    ConnectedScenes = models.CharField(max_length=12)
    NumHotspots = models.IntegerField()

class Hotspot(models.Model):
    parent = models.CharField(max_length=12)
    num = models.CharField(max_length=12)
    x = models.IntegerField()
    y = models.IntegerField()
    Teleport = models.BooleanField()
    TeleportToScene = models.IntegerField(null=True, blank=True)
    ShowImage = models.ImageField(null=True, blank=True)
    popupNum = models.IntegerField(null=True, blank=True)

class Popup(models.Model):
    # What appears on the popups within the game
    num = models.IntegerField()
    sceneParent = models.CharField(max_length=12)
    hotspotParent = models.CharField(max_length=12)
    showImageBase = models.ImageField()