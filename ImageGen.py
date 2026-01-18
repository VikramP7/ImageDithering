import math
import numpy as np
from PIL import Image
import sys
import random
import copy


def GetPath():
    """Prompts the user to provide a path to an image file"""
    badImagePath = True
    path = ""
    while badImagePath:
        badImagePath = False
        path = input("What is the path for your image (include extension): ")
        try:
            image = Image.open(path)
            image.close()
        except TypeError:
            badImagePath = True
            print("File not parsable.")
        except FileNotFoundError:
            badImagePath = True
            print("No file found at path.")
    return path


def ColourRound(colour, colour_space=None):
    if colour_space == None:
        return 1 if colour > 0.5 else 0
    elif type(colour_space) == float:
        return 1 if colour > colour_space else 0
    smallest_error = 255*3
    best_index = 0
    for i in range(len(colour_space)):
        cur_error=0
        for rgb in range(3):
            cur_error += abs(colour[rgb]-colour_space[i][rgb])
        if cur_error < smallest_error:
            best_index = i
            smallest_error = cur_error
    return colour_space[best_index]


def TestTranspose(imgArr):
    imageHeight = len(imgArr)
    imageWidth = len(imgArr[0])
    imageRatio = imageWidth / imageHeight
    displayRatio = width / height
    transpose = (displayRatio > 1) ^ (
        imageRatio > 1
    )  # XOR as only if they differ then transpose
    if transpose:
        imgArr = np.transpose(imgArr, (1, 0, 2))
        
    return imgArr

def ResizeImage(imgArr, width=-1, height=-1, colour=False, allowTranspose=False):
    imageHeight = len(imgArr)
    imageWidth = len(imgArr[0])

    width = min(width, imageWidth)
    height = min(height, imageHeight)
    
    if allowTranspose:
        imgArr = TestTranspose(imgArr=imgArr)
        imageHeight = len(imgArr)
        imageWidth = len(imgArr[0])

    # set result image
    resizeImg = []
    resizeImgAveCount=[]
    for y in range(0, height):
        resizeImg.append([])
        resizeImgAveCount.append([])
        for x in range(0, width):
            if not colour:
                resizeImg[y].append(0.0)
            else:
                resizeImg[y].append([])
                for rgb in range(3):
                    resizeImg[y][x].append(0.0)
            resizeImgAveCount[y].append(0)
    
    # Better Down scaling
    widthFactor = width/imageWidth
    heightFactor = height/imageHeight
    for y in range(imageHeight):
        if y % int(imageHeight/100) == 0:
            print(f"{round((y/imageHeight)*100)}% Downscaling completed                     ", end="\r")
        for x in range(imageWidth):
            smallX = min(round(x*(widthFactor)), width-1)
            smallY = min(round(y*(heightFactor)), height-1)
            try:
                for rgb in range(3):
                    if not colour:
                        resizeImg[smallY][smallX] += imgArr[y][x][rgb]
                    else:
                        resizeImg[smallY][smallX][rgb] += imgArr[y][x][rgb]
            except IndexError:
                if not colour:
                    resizeImg[smallY][smallX] += imgArr[y][x]
                else:
                    for rgb in range(3):
                        resizeImg[smallY][smallX][rgb] += imgArr[y][x]
            resizeImgAveCount[smallY][smallX] += 1
    
    for y in range(height):
        for x in range(width):
            if not colour:
                resizeImg[y][x] = resizeImg[y][x]/(resizeImgAveCount[y][x]*3.0 * 255.0)
            else:
                for rgb in range(3):
                    resizeImg[y][x][rgb] = resizeImg[y][x][rgb]/(resizeImgAveCount[y][x])
    
    return resizeImg

def ReturnDitheredImage(path, width=-1, height=-1, colour=False, colour_space=None, allowTranspose=False, returnNoDitherToo=False):
    """
    Uses the provided path to parse an image file. Then it's scaled it to fit width and height.
    Finally the scaled image is converted to bitmap unsigned ints for lcd.

    :param path: (String) The path to the image file
    :param width: (int) width of result image in pixels
    :param height: (int) height of result image in pixels
    :return: A string of a 2D c array for pasting into lcd program
    """

    # open image and convert to 3d array
    image = Image.open(path)
    imgArr = np.asarray(image)
    image.close()

    imageHeight = len(imgArr)
    imageWidth = len(imgArr[0])

    if width == -1:
        width = imageWidth
    if height == -1:
        height = imageHeight

    resizeImg = ResizeImage(imgArr=imgArr, width=width, height=height, colour=colour, allowTranspose=allowTranspose)

    if returnNoDitherToo:
        resizeImgNoDither = copy.deepcopy(resizeImg)

    kernelFloydSteinberg=[[0, 0, 7],
                          [3, 5, 1]]
    
    for y in range(len(kernelFloydSteinberg)):
        for x in range(len(kernelFloydSteinberg[y])):
            kernelFloydSteinberg[y][x] /= 16
    
    kernelJarvis=[[0,0,0,7,5],
                  [3,5,7,5,3],
                  [1,3,5,3,1]]
    
    for y in range(len(kernelJarvis)):
        for x in range(len(kernelJarvis[y])):
            kernelJarvis[y][x] /= 48
            #kernelJarvis[y][x] /= 0.8
    
    kernelRandom = []
    for y in range(2):
        kernelRandom.append([])
        for x in range(3):
            kernelRandom[y].append(random.random())
    kernelRandom[0][0]=0
    kernelRandom[0][1]=0

    kernel = kernelJarvis
    zeroOffset=2

    maxQError = 200
    #maxQError = 150
    #maxQError = 20

    # Dithering Algorithm:
    for y in range(0, height - zeroOffset):
        if y % int(height/100) == 0:
            print(f"{round((y/height)*100)}% Dithering Completed                 ", end="\r")
        for x in range(0, width - zeroOffset):
            oldPixel = resizeImg[y][x]
            newPixel = ColourRound(resizeImg[y][x], colour_space)
            if not colour:
                quantError = (oldPixel - newPixel)
                for kernelY in range(len(kernel)):
                    for kernelX in range(len(kernel[kernelY])):
                        resizeImg[y+kernelY][x+kernelX-zeroOffset] += quantError * kernel[kernelY][kernelX]
            else:
                for rbg in range(3):
                    quantError = max(-maxQError,min(oldPixel[rbg] - newPixel[rbg], maxQError))
                    for kernelY in range(len(kernel)):
                        for kernelX in range(len(kernel[kernelY])):
                            resizeImg[y+kernelY][x+kernelX-zeroOffset][rbg] += quantError * kernel[kernelY][kernelX]

    if not colour:
        # round to binary
        threshold = 0.5
        for y in range(0, height):
            for x in range(0, width):
                #threshold = (0.2+random.random()*0.8)
                resizeImg[y][x] = 0 if resizeImg[y][x] > threshold else 1
                if returnNoDitherToo:
                    resizeImgNoDither[y][x] = 0 if resizeImgNoDither[y][x] > threshold else 1
    else:
        for y in range(0, height):
            for x in range(0, width):
                resizeImg[y][x] = ColourRound(resizeImg[y][x], colour_space=colour_space)
                if returnNoDitherToo:
                    resizeImgNoDither[y][x] = ColourRound(resizeImgNoDither[y][x], colour_space=colour_space)

    if returnNoDitherToo:
        return resizeImg, resizeImgNoDither

    return resizeImg


def saveImage(image, fileName, colour=False):
    if not colour:
        npImage = (np.asarray(image)^1)* 255
    else:
        npImage = abs(np.asarray(image))
    display = Image.fromarray(npImage.astype(np.uint8))
    display.save(fileName)

def printHelpMessage():
    #print("Error With width-height arguments")
    print("Please use \"ImageGen.py [path] [width] [height] [inColour] [saveNonDithered]\"")
    print("Or use \"ImageGen.py [path]\" for default parameters")
    print("[path]: string to image including extension\n[width/height]: number of pixels, -1 for original\n[inColour/saveNonDithered]: 1 or 0")



if __name__ == "__main__":
    
    purpleRed = [[184, 225, 255], [186, 27, 29], [246, 245, 174], [151, 115, 144], [47, 72, 88]]
    beach = [[229, 212, 237], [143, 57, 133], [246, 245, 174], [249, 105, 0], [184, 225, 255]]
    lime = [[214, 255, 121], [176, 255, 146], [255, 242, 241], [160, 155, 231], [95, 0, 186]]
    brownp = [[147, 56, 36], [63, 13, 18], [237, 184, 139], [214, 58, 249], [147, 91, 30]]
    brownr = [[1, 0, 1], [43, 5, 4], [135, 64, 0], [188, 95, 4], [244, 68, 46]]
    electric = [[0, 255, 197], [173, 245, 255], [72, 22, 32], [213, 86, 114], [81, 0, 251]]
    blueOrange =[[0x39, 0x00, 0x99], [0x9e, 0x00, 0x59], [0xff, 0x00, 0x54], [0xff, 0x54, 0x00], [0xff, 0xbd, 0x00]]
    tanPurple =[[249, 219, 189], [252, 161, 125], [218, 98, 125], [154, 52, 142], [13, 6, 40]]
    pearl = [[25, 20, 10],[72, 76, 74],[180, 171, 159],[236, 226, 200],[108, 129, 155]]
    sonofman = [[231, 194, 167],[155, 145, 138],[137, 62, 30],[36, 20, 17],[210, 162, 55]]
    sonofmaninv = [[24, 61, 88],[100, 110, 117],[118, 193, 225],[219, 235, 238],[45, 93, 200]]
    pan = [[79, 79, 92],[237, 224, 215],[146, 107, 102],[190, 172, 170],[47, 27, 28]]
    paninv = [[176, 176, 163],[18, 31, 40],[109, 148, 153],[65, 83, 85],[208, 228, 227]]
    ljb = [[120, 137, 31],[149, 150, 181],[193, 250, 255],[86, 83, 138],[231, 226, 126]]
    ljb2 = [[226, 232, 218],[143, 168, 195],[60, 75, 42],[156, 132, 85],[213, 226, 120]]
    stary = [[47, 21, 22],[66, 96, 184],[225, 230, 148],[152, 124, 0],[189, 152, 84]]
    paint = [[51, 105, 129],[169, 115, 25],[10, 38, 52],[255, 248, 239],[209, 144, 122]]
    green = [[99, 88, 157],[0, 3, 16],[168, 184, 26],[177, 70, 78],[184, 249, 251]]
    bwrgb = [[0,0,255], [0,255,0], [255,0,0], [255,255,255], [0,0,0]]
    bw = [[0,0,0],[255,255,255]]

    my_colour_space = tanPurple

    n = len(sys.argv)
    path = ""
    width = 324 #128
    height = 244 #64
    BWToo = False
    colour = False
    if n == 2:
        path = str(sys.argv[1])
        help = (path.lower().find("help") != -1) or (path.lower().find("-h") != -1)
        if help:
            printHelpMessage()
            sys.exit(0)
        width = -1
        height = -1
        BWToo = True
        colour = True
    elif n ==3:
        path = sys.argv[1]
        width = -1
        height = -1
        colour = True
        BWToo = False
    elif n >= 4:
        path = sys.argv[1]
        try:
            width = int(sys.argv[2])
            height = int(sys.argv[3])
        except (TypeError, IndexError):
            printHelpMessage()
        if n >= 5:
            colour = sys.argv[4] != '0'
            if n == 6:
                BWToo = sys.argv[5] != '0'
    else:
        path = GetPath()
        width = -1
        height = -1
    
    print("Image Path: ", path)
    print("Display Width: ", ("Original" if width == -1 else width))
    print("Display Height: ", ("Original" if height == -1 else height))
    print("In Reduced Colour Space" if colour else "In Black and White")
    print("Saving non-dithered image aswell" if BWToo else "")
    print()
    

    if not colour:
        my_colour_space = None

    savePath=path[:path.index('.')]+("_Colour" if colour else "BW")
    if BWToo:
        ditheredImage, BWImage = ReturnDitheredImage(path, width, height, colour=colour, colour_space=my_colour_space, returnNoDitherToo=True)
        saveImage(ditheredImage, savePath+"_Dithered.png", colour=colour)
        saveImage(BWImage, savePath+"_NoDither.png", colour=colour)
        print(f"Image Saved: {savePath+"_Dithered.png"}")
        print(f"Image Saved: {savePath+"_NoDither.png"}")
    else:
        ditheredImage = ReturnDitheredImage(path, width, height, colour=colour, colour_space=my_colour_space, returnNoDitherToo=False)
        saveImage(ditheredImage, savePath+"_Dithered.png", colour=colour)
        print(f"Image Saved: {savePath+"_Dithered.png"}")
