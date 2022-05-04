from ast import Mod
import re
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.conf import settings
from rest_framework.renderers import JSONRenderer
import json
import os
import math
from PIL import Image

# Custom imports
from .models import Image as _Img
from .models import Scene, Hotspot, Popup
from .forms import ImageForm
from .serializers import SceneSerializer, HotspotSerializer

def getNounLexicon(request):

    # Get the number of symbols
    numSymbols = len(_Img.objects.all())

    nounLexicon = _morph.main(numSymbols, "EASY")

    return HttpResponse({"Success" : True})

def bulkImageUpload(request):

    form = ImageForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        images = request.FILES.getlist('images')
        count = 0
        for image in images:
            _Img.objects.create(name=count, imagefile=image)
            count = count + 1

    context= {
                'form': form,
              }
    
    return render(request, 'images.html', context)

def transparentImages(request):
    # Make all the images in the symbols DB transparent
    symbols = _Img.objects.all()
    for s in symbols:
        tmpImg = Image.open(s.imagefile)
        rgba = tmpImg.convert("RGBA")
        data = rgba.getdata()
        newData = []
        for channel in data:
            # Find all black pixels:
            if channel[0] == 0 and channel[1] == 0 and channel[2] == 0:
                # Make them transparent
                newData.append(channel)
            else:
                # Make them transparent white
                newData.append((255, 255, 255, 0))
        # Save the image
        rgba.putdata(newData)
        rgba.save(settings.MEDIA_ROOT + "/transparentSymbols/" + s.name + ".png")
        s.imagefile = 'transparentSymbols' + '/' + s.name + '.png'
        s.save()

    return(redirect('links'))

def makeImageTransparent(imgLink):

    rgba = imgLink.convert("RGBA")
    data = rgba.getdata()
    newData = []
    for channel in data:
        # Find all black pixels:
        if channel[0] == 0 and channel[1] == 0 and channel[2] == 0:
            # Make them transparent
            newData.append(channel)
        else:
            # Make them transparent white
            newData.append((106, 32, 200, 1))
    # Save the image
    rgba.putdata(newData)
    return rgba

def generateLexicon(request, mode):
    """Produce an image of the symbols next to eachother, representing the word in English, in symbols

    :param word: The word from the lexicon to be displayed
    :type word: str
    :return: HttpResponse
    :rtype: Django HttpResponse
    """
    # Need to first generate the Lexicon (this will eventually be read from the DB when I can set up with postgres)
    numSymbols = len(_Img.objects.all())
    # Get the lexicon objects
    lexiconQueryset = Word.objects.all() # NB we can filter this with .get(wordType="noun") or equivalent
    # Extract just the words
    lexiconKeys = [x.englishWord for x in lexiconQueryset] # list
    # Generate symbols
    lexicon = _morph.main(numSymbols-1, lexiconKeys, DIFFICULTY=mode.capitalize()) # Outputs dict

    scale = 0 

    # TODO: Obviously atm we're saving these to the DB, which of course won't scale. We can't have every user editing the DB
    #       every single time they launch the game, so these will actually need to be generated on the fly per game
    #
    #       In the meantime, using the DB is handy for debugging
    gameTableau.objects.all().delete()

    # Create all the symbol images
    for item in lexicon:

        background = Image.new('RGBA', (650, 150), (255, 255, 255, 0))
        bg_w, bg_h = background.size

        # Currently just does one single word, need it to do all
        for symbol in lexicon[item]:
            # Load from the DB
            imgObject = _Img.objects.get(name=symbol).imagefile
            img = Image.open(imgObject)
            img_w, img_h = img.size
            offset = ((math.floor((bg_w - img_w) / 10) + scale) , math.floor((bg_h - img_h) / 10))
            # offset = (300, 10)
            background.paste(img, offset)
            scale = scale + 90

        newBackground = makeImageTransparent(background)
            
        newBackground.save(settings.MEDIA_ROOT + "/words/" + item + ".png")

        gameTableau.objects.create(name=item, image="words/" + item + ".png")

        scale = 0
    
    return(redirect('displayAll', mode=mode))

def viewDictionary(request, mode):

    context = {
        "dictionary" : gameTableau.objects.all(),
        "mode" : mode,
    }

    print("New %s lexicon" % (mode))

    return render(request, 'dictionary.html', context)

def generatePopups(request):
    """
    Summary:
            The flow is:
            1) Load in our popups
            2) Get the base image
            3) Get each of the words to be shown with their associated coordinates
            4) Each word has an associated image that shows the symbols --> superimpose this image onto the base image at the specified coords
            5) Save the base image to the popups class

    # TODO profile this for time and memory allocation, will be run once at the start of every game so don't want it to be incredibly slow

    NB Before this can be run, need to make sure we've generated all our symbols!
    """

    # Load in the popups
    popupQs = Popup.objects.all()
    # Iterate over them:
    for p in popupQs:
        # Get the base image
        baseImage = Image.open(p.showImageBase)
        # Since it's chars, we need to seperate the single long string by ','
        wordList = p.wordsList.split(", ")
        # Do the same for coords
        xList = p.wordsListX.split(", ")
        yList = p.wordsListY.split(", ")
        # And modifiers
        # TODO: Make it so you don't need modifiers
        modifiers = p.modifierList.split(", ")
        # Need to check if we even have numbers
        if p.numsList == None:
            numsList = [None for _ in range(len(wordList))]
            xNumsList = numsList
            yNumsList = numsList
            applyNums = False
        else:
            numsList = p.numsList.split(", ")
            xNumsList = p.numsListX.split(", ")
            yNumsList = p.numsListY.split(", ")
            applyNums = True
        # Get all words and numbers and superimpose on the base image
        # TODO: probably better splitting this process up
        for entry, x, y, num, nx, ny, m in zip(wordList, xList, yList, numsList, xNumsList, yNumsList, modifiers):
            # Get this particular word
            newWord = gameTableau.objects.filter(name = entry).last()
            # Get this particular number
            if applyNums:
                newNum = Number.objects.filter(value = num).last()
                numberImage = Image.open(newNum.imagefile)
                numberImage = numberImage.resize((90, 90))
            # Get the symbol image:
            wordImage = Image.open(newWord.image)
            """
            TODO:
                !!! This here is where we should apply our modifiers !!!
                We can call a function that takes in the word, reads in the modifiers we want for it, and applies them, then returns
                an image we can paste onto the background
            """
            if m != "0":
                print("Applying modifier")
                wordImage = applyModifier(wordImage, m)
            # Paste the number and word symbols onto the base image
            baseImage.paste(wordImage, (int(x), int(y)), wordImage)
            if applyNums:
                baseImage.paste(numberImage, (int(nx), int(ny)), numberImage)
        # And save the image to this popup. TODO: Saving it also to the hotspot parent is the most useful thing to do.
        baseImage.save(settings.MEDIA_ROOT + "/popups/" + p.sceneParent + "_" + p.hotspotParent + "_popup.png")
        p.finalImage = "/popups/" + p.sceneParent + "_" + p.hotspotParent + "_popup.png"
        p.save()
        # And get the corresponding hotspot object
        # TODO exception catch for if there's an issue with getting the hotspot
        hotspot = Hotspot.objects.get(popupNum=p.num)
        hotspot.ShowImage = p.finalImage
        hotspot.save()
        # This works with the current saving method, but for x users, will create x replicas of every game object and is unnecessary
        # So make it ephemeral!!
        # That should be everything done for that, we can do the generation and then start the game

    return(redirect('links'))

def applyModifier(wordImage, modifierID):

    # Find modifier in dictionary from ID
    modifierObject = Modifier.objects.filter(num = modifierID).last()
    modifierImage = Image.open(modifierObject.imagefile)
    modifierImage = modifierImage.resize((150, 100))

    # Get combined size of the word and modifier images (plus headroom)
    bgSize = (wordImage.size[0] + modifierImage.size[0] + 50, wordImage.size[1] + modifierImage.size[1] + 50)

    # Create background image for the base word and the modifier
    background = Image.new('RGBA', bgSize, (255, 255, 255, 0))

    # Paste it onto the wordImage in some way - perhaps with instructions from the modifier object
    background.paste(wordImage, (0, 0), wordImage)
    # TODO: Could sub in a mapping here like position=TOP and top is at 0, 0, BOTTOM is 0, wordImage.size[1] etc. - gives us another parameter we can vary
    background.paste(modifierImage, (40, 10), modifierImage)

    background.show()
    
    # return the new image
    return background

def linksView(request):

    return render(request, 'linksPage.html', context={})

def startGameView(request, mode):

    # Load in and serialize the tableaus
    allTableausSerialized = json.dumps([{x.name : TableauBaseSerializer(x).data} for x in TableauBase.objects.all()])

    # Get the hotspots as nested dictionaries of parent:{children}
    allHotspotsSerialized = {}
    for x in TableauBase.objects.all():
        allHotspotsSerialized[x.name] = {}
        for y in Hotspot.objects.filter(parent = x.name):
            allHotspotsSerialized[x.name][y.num] = HotspotSerializer(y).data
    allHotspotsSerialized = json.dumps(allHotspotsSerialized)

    # And do the same for the hotspots:
    # allHotspotsSerialized = json.dumps([{x.parent + "_" + x.num : HotspotSerializer(x).data} for x in Hotspot.objects.all()])

    context = {
                "mode" : mode.lower(),
                "tableauJson" : allTableausSerialized,
                "hotspotsJson" : allHotspotsSerialized
    }

    return render(request, 'game.html', context)

"""
TODO:
    - Build image caching function -- > preloadjs library?
    - Make symbols transparent
    - Build popup function --> Works but needs tweaking and polishing to best render the image
    - Build backend function for adding symbols to images --> Done!


Thoughts:
    - Map of player exploration vs. optimal path as a measure of efficiency, but also a measure of tendancy for exploration
        It's almost less of a direct intelligence measure and more of a profile of the person, like those circular plots
        that show tendancy towards certain personality traits etc
"""