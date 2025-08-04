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


def ReturnImageColourSpace(path, space_size=5):
    """
    Uses the provided path to parse an image file. Each colour present in the image is grouped into the space_size number of groups.
    The average of the group is reported as the colour.

    :param path: (String) The path to the image file
    :param space_size: (int) The total number of colours in the space
    """
    # open image and convert to 3d array
    image = Image.open(path)
    imgArr = np.asarray(image).tolist()
    image.close()

    imageHeight = len(imgArr)
    imageWidth = len(imgArr[0])

    colours = []

    colours.append(imgArr[0][0])

    for y in range(0, imageHeight, 10):
        print(round(y*100/imageHeight), end="%                \r")
        for x in range(0, imageWidth, 10):
            close_enough = False
            cur_colour = 0
            while cur_colour < len(colours):
                if FindColourDistance(imgArr[y][x], colours[cur_colour]) < 10:
                    close_enough = True
                    cur_colour = len(colours)
                cur_colour += 1
            if not close_enough:
                colours.append(imgArr[y][x])

    original_len = len(colours)
    while(len(colours)>space_size):
        # find closest colour
        closest1 = 0
        closest2 = 1
        distance = 442 # mathematically the largest distance between 0-255 rgb colour vectors = math.sqrt(255**2 + 255**2 + 255**2)
        for i in range(len(colours)):
            for j in range(i+1, len(colours)):
                cur_dist = FindColourDistance(colours[i], colours[j])
                if cur_dist < distance:
                    closest1 = i
                    closest2 = j
                    distance = cur_dist
        closests_ave = []
        for rgb in range(3):
            closests_ave.append(colours[closest2][rgb])
            #closests_ave.append((colours[closest1][rgb]+colours[closest2][rgb])/2)
        
        for rgb in range(3):
            colours[closest1][rgb] = closests_ave[rgb]
        
        colours.pop(closest2)
        print(len(colours), end=" | ")
        print(round((original_len-len(colours)-space_size)*100/original_len), end="%                    \r")
    
    for i in range(len(colours)):
        for rgb in range(3):
            colours[i][rgb]=round(colours[i][rgb])
    
    arr_str = "["
    for colour in colours:
        arr_str += '['
        for rgb in range(3):
            arr_str += str(colour[rgb])
            arr_str += ', '
        arr_str = arr_str[:-2]
        arr_str += '],'
    arr_str = arr_str[:-1]
    arr_str += ']'
    print(arr_str)

    link="https://coolors.co/"
    for colour in colours:
        for rgb in range(3):
            link += IntTo2DigitHex(colour[rgb])
        link += "-"
    print(link[:-1])

    return colours

def IntTo2DigitHex(val):
    text = hex(val)[2:]
    text = "0" + text
    return text[-2:]

def FindColourDistance(colour1, colour2):
    try:
        if len(colour1) < 3 or len(colour2) < 3:
            return -1            
    except TypeError:
        return -1
    
    val = 0
    for rgb in range(3):
        val += (colour1[rgb]-colour2[rgb])**2
        
    return math.sqrt(val)


if __name__ == "__main__":

    path = GetPath()
    ReturnImageColourSpace(path)
