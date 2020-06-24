from htmlParser import getFormatedArticle
from chunkGenerator import *
from ZIMply.zimply import ZIMFile
from os import path
import math
import time

from amulet.world_interface import load_world

def generateChunkList(totalArticleCount, chunkBookCapacity, target_pos):
    #generate a square, that could fit (more than) all articles
    sideLength = math.ceil(math.sqrt(totalArticleCount/chunkBookCapacity))
    print("/forceload %d %d %d %d"%(target_pos[0], target_pos[1], target_pos[0] + (sideLength+2)*16, target_pos[1] + (sideLength+2)*16))#give it 2 more chunks just to be sure
    chunkList = []
    for x in range(sideLength):
        for z in range(sideLength):
            if len(chunkList) >= math.ceil(totalArticleCount/chunkBookCapacity): #stop if we have enough chunks
                break
            chunkList.append([x + target_pos[0] // 16, z + target_pos[1] // 16])
    return chunkList

def generateWallList(chunkList):
    wallChunkWithSlice = []
    for chunk in chunkList:
        #create chunk slices for the 4 chunks that would have walls to the center chunk
        potentialWalls = []
        potentialWalls.append([[1,0],  [0, slice(0,16)]])
        potentialWalls.append([[0,1],  [slice(0,16), 0]])
        potentialWalls.append([[-1,0], [15, slice(0,16)]])
        potentialWalls.append([[0,-1], [slice(0,16), 15]])

        #turn its local coordinates into world coordinates
        for potWall in potentialWalls:
            potWall[0][0] += chunk[0]
            potWall[0][1] += chunk[1]

        #only keep the wallchunk if its not in use
        for potWall in potentialWalls:
            if potWall[0] in chunkList:
                continue
            wallChunkWithSlice.append(potWall)

    return wallChunkWithSlice


def fill(world, booksPerBarrel, position, dimension = "overworld", skip = 0):
    filePath = path.dirname(path.realpath(__file__)) + "\\wikipedia_de_basketball_nopic_2020-04.zim"
    #filePath = path.dirname(path.realpath(__file__)) + "\\wikipedia_de_all_nopic_2020-04.zim"
    zimfile = ZIMFile(filePath,"utf-8")

    article = None
    for article in zimfile:
        pass
    totalArticleCount = article[2]
    print("articles: ", totalArticleCount)

    barrelPositionList = generateBarrelPositionList()
    barrelsPerChunk = len(barrelPositionList)
    chunkBookCapacity = barrelsPerChunk * booksPerBarrel
   
    chunkList = generateChunkList(totalArticleCount, chunkBookCapacity, position)
    wallChunkList = generateWallList(chunkList)

    totalChunkCount = len(chunkList) + len(wallChunkList)
    completedChunks = 0
    currentArticle = 0
    for chunkCoords in chunkList:
        if skip > 0:
            skip -= 1
            continue
        start = time.perf_counter()
        chunk = world.get_chunk(chunkCoords[0], chunkCoords[1], dimension)
        fillChunk(chunk, barrelPositionList, world, dimension, currentArticle, booksPerBarrel, filePath)
        currentArticle += booksPerBarrel * barrelsPerChunk

        world.save()

        completedChunks += 1
        print("loop time: ", (time.perf_counter() - start)/60)
        print("completed chunk: ", completedChunks)
        yield 100 * completedChunks / totalChunkCount

    for wallChunkCoords, orientation in wallChunkList:
        chunk = world.get_chunk(wallChunkCoords[0], wallChunkCoords[1], dimension)
        placeWall(chunk, orientation, world)

        completedChunks += 1
        yield 100 * completedChunks / totalChunkCount


if __name__ == "__main__":
    world = load_world(path.expandvars('%APPDATA%\\.minecraft\\saves\\New World (4)\\'))
    for x in fill(world, 9, [0, 0]):
        print(x)

    world.save()
