from htmlParser import getFormatedArticle
from chunkGenerator import *
from ZIMply.zimply import ZIMFile
from os import path
import math
import time
import argparse

from amulet.world_interface import load_world

def generateChunkList(totalArticleCount, chunkBookCapacity, target_pos, outputForceload = False):
    #generate a square, that could fit (more than) all articles
    sideLength = math.ceil(math.sqrt(totalArticleCount/chunkBookCapacity))
    if outputForceload:
        command = "/chunkgenerator:generatechunks %d %d %d %d"%(target_pos[0] - 1, target_pos[1] - 1, target_pos[0] + sideLength + 1, target_pos[1] + sideLength + 1)#+- 1 to include the outer border of the library
        print(command)
        return

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


def getLastArticleId(zimfile):
    article = None
    for article in zimfile:
        pass
    return article[2]

def fill(       booksPerBarrel, 
                position, 
                world = False, 
                dimension = "overworld", 
                skipChunk = 0, 
                 skipArticles = 0, 
                 filePath = path.dirname(path.realpath(__file__)) + "\\wikipedia_de_all_nopic_2020-04.zim"):
    zimfile = ZIMFile(filePath,"utf-8")

    totalArticleCount = getLastArticleId(zimfile)

    barrelPositionList = generateBarrelPositionList()
    barrelsPerChunk = len(barrelPositionList)
    chunkBookCapacity = barrelsPerChunk * booksPerBarrel
   
    chunkList = generateChunkList(totalArticleCount, chunkBookCapacity, position, world == False)
    if world:

        wallChunkList = generateWallList(chunkList)

        totalChunkCount = len(chunkList) + len(wallChunkList)
        completedChunks = 0
        currentArticle = skipArticles
        for chunkCoords in chunkList:
            if skipChunk > 0:
                skipChunk -= 1
                continue
            start = time.perf_counter()
            chunk = world.get_chunk(chunkCoords[0], chunkCoords[1], dimension)
            fillChunk(chunk, barrelPositionList, world, dimension, currentArticle, booksPerBarrel, filePath)
            currentArticle += booksPerBarrel * barrelsPerChunk

            world.save()

            completedChunks += 1
            print("chunk time (m): ", (time.perf_counter() - start)/60)
            print("completed chunk: ", completedChunks)
            yield 100 * completedChunks / totalChunkCount

        for wallChunkCoords, orientation in wallChunkList:
            chunk = world.get_chunk(wallChunkCoords[0], wallChunkCoords[1], dimension)
            placeWall(chunk, orientation, world)

            completedChunks += 1
            yield 100 * completedChunks / totalChunkCount
        world.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Puts a wiki into a Minecraft world')
    parser.add_argument('-wiki', type=str, help='Location of the wiki file', default=path.dirname(path.realpath(__file__)) + "\\wikipedia_de_all_nopic_2020-04.zim")
    #parser.add_argument('-wiki', type=str, help='Location of the wiki file', default=path.dirname(path.realpath(__file__)) + "\\wikipedia_de_basketball_nopic_2020-04.zim")
    parser.add_argument('-world', type=str, help='Location of the world file. You may use %%APPDATA%%')
    parser.add_argument('-booksPerBarrel', type=int, help='Number of books to put in a barrel', default=27)
    parser.add_argument('-chunkSkip', type=int, help='Number of chunks to skip', default=0)
    parser.add_argument('-pos', metavar=("X","Z"),type=int, help='X Z coordinates of the starting chunk (block coordinates)', default=[0,0], nargs=2)
    
    args = parser.parse_args()

    #debug vars
    bookSkip = 0
    args.world = '%APPDATA%\\.minecraft\\saves\\world\\'
    

    if args.world is not None:
        world = load_world(path.expandvars(args.world))
        for progress in fill(args.booksPerBarrel,
                            args.pos,
                            world = world,
                            skipArticles = bookSkip,
                            skipChunk = args.chunkSkip,
                            filePath = args.wiki):
            print(progress)
    else:
        for progress in fill(args.booksPerBarrel,
                            args.pos,
                            world = False,
                            skipArticles = bookSkip,
                            skipChunk = args.chunkSkip,
                            filePath = args.wiki):
            pass

