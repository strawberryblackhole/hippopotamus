from amulet.api.block import Block
import amulet_nbt
from amulet.api.block_entity import BlockEntity
from htmlParser import getFormatedArticle
from functools import partial
import multiprocessing
from multiprocessing.pool import Pool
from multiprocessing.pool import ThreadPool
from ZIMply.zimply import ZIMFile
import time

def getBlock(world, block):
    """turns a block object into a usable block object, no idea what this actually does"""
    tmp = world.world_wrapper.translation_manager.get_version(
                "java",
                (1, 15, 2)
            ).block.to_universal(
                block
            )[0]
    return world.palette.get_add_block(tmp)

def createBlocks(world):
    """generates all needed Block objects"""

    barrel = getBlock(world, Block("minecraft", "barrel", {"facing" : amulet_nbt.TAG_String("up"), "open" : amulet_nbt.TAG_String("false")}))

    wool = getBlock(world, Block("minecraft", "red_wool"))

    air = getBlock(world, Block("minecraft", "air"))

    stone = getBlock(world, Block("minecraft", "stone"))

    glowstone = getBlock(world, Block("minecraft", "glowstone"))

    lantern = getBlock(world, Block("minecraft", "lantern", {"hanging" : amulet_nbt.TAG_String("false")}))

    sign_north = getBlock(world, Block("minecraft", "acacia_wall_sign", {"facing" : amulet_nbt.TAG_String("north")}))
    sign_south = getBlock(world, Block("minecraft", "acacia_wall_sign", {"facing" : amulet_nbt.TAG_String("south")}))

    return [barrel, wool, glowstone, sign_north, sign_south, air, stone, lantern]


def generateBarrelPositionList():
    """Generates a list of coordinates in a chunk (16x16) where barrels should be"""
    barrels = []

    for row in [0,8]:
        for y in range(5,7):
            for x in range(1,8,2):
                subList = [(x, y, z) for z in range(1 + row, 7 + row)]
                barrels.extend(subList)
            for x in range(8,15,2):
                subList = [(x, y, z) for z in range(1 + row, 7 + row)]
                barrels.extend(subList)
    return barrels

def generateSignEntity(x, y, z, direction):
    """Generates the entity to make the sign display its position"""
    return BlockEntity("java", "acacia_wall_sign", x, y, z,\
                amulet_nbt.NBTFile(\
                    value = amulet_nbt.TAG_Compound(\
                        {\
                            "utags": amulet_nbt.TAG_Compound(\
                                {\
                                    "keepPacked": amulet_nbt.TAG_Byte(0),\
                                    "Text4": amulet_nbt.TAG_String("{\"text\":\"\"}"),\
                                    "Text3": amulet_nbt.TAG_String("{\"text\":\"\"}"),\
                                    "Text2": amulet_nbt.TAG_String("{\"text\":\"%d - %d\"}"%(z + direction, z + direction * 6)), \
                                    "Text1": amulet_nbt.TAG_String("{\"text\":\"%d\"}"%x)\
                                }),\
                            "Color": amulet_nbt.TAG_String("black")\
                        })))

def fillSigns(chunk, world, dimension, sign_north, sign_south):
    """Generates all signs in the chunk and fills them with text"""
    for z in [0, 8]:
        for x in list(range(1,8,2)) + list(range(8,15,2)):
            chunk.blocks[x,6,z] = sign_north
            chunk.block_entities.insert(generateSignEntity(x + chunk.cx * 16, 6, z + chunk.cz * 16, 1))

    for z in [7, 15]:
        for x in list(range(1,8,2)) + list(range(8,15,2)):
            chunk.blocks[x,6,z] = sign_south
            chunk.block_entities.insert(generateSignEntity(x + chunk.cx * 16, 6, z + chunk.cz * 16, -1))


def fillbarrels(chunk, barrelPositionList, barrelBlock, currentArticle, booksPerBarrel, zimfilePath):
    """Generates all barrels in the chunk and fills them with books/articles"""
    
    for barrelPos in barrelPositionList:
        books = []
        titles = []


        start = time.perf_counter()

        if booksPerBarrel > 999: #for big wikis processes do not seem to have an advantage over threads. with a full barrel a thread needs 100 ms per book, process 150 ms
            pool = Pool(processes=multiprocessing.cpu_count())
        else:
            pool = ThreadPool(processes=multiprocessing.cpu_count())
        outputs = pool.map(partial(tryGetArticle, zimFilePath = zimfilePath), range(currentArticle, currentArticle + booksPerBarrel))
        pool.close()
        currentArticle += booksPerBarrel
        for output in outputs:
            if output[0] == None:
                continue
            titles.append(output[1])
            books.append(output[0])

        stop = time.perf_counter()
        print("generating a book", (stop-start)/booksPerBarrel)




        chunk.blocks[barrelPos] = barrelBlock
        barrelEntity = BlockEntity("java", "barrel", barrelPos[0] + chunk.cx * 16, barrelPos[1], barrelPos[2] + chunk.cz * 16,\
            amulet_nbt.NBTFile(\
                value = amulet_nbt.TAG_Compound(\
                {\
                    "utags": amulet_nbt.TAG_Compound(\
                    {\
                        "keepPacked": amulet_nbt.TAG_Byte(0),\
                        "isMovable": amulet_nbt.TAG_Byte(1),\
                        "Findable": amulet_nbt.TAG_Byte(0),\
                        "CustomName": amulet_nbt.TAG_String("{\"text\":\"x:%d z:%d\"}"%(barrelPos[0] + chunk.cx * 16, barrelPos[2] + chunk.cz * 16)),\
                        "Items": amulet_nbt.TAG_List(\
                            value = [
                                amulet_nbt.TAG_Compound(\
                                {\
                                    "Slot": amulet_nbt.TAG_Byte(iBook),\
                                    "Count": amulet_nbt.TAG_Byte(1),\
                                    "id": amulet_nbt.TAG_String("minecraft:written_book"),\
                                    "tag": amulet_nbt.TAG_Compound(\
                                    {
                                        "pages": amulet_nbt.TAG_List(\
                                            value=[amulet_nbt.TAG_String(page) for page in books[iBook]],\
                                            list_data_type = 8\
                                        ),\
                                        "title": amulet_nbt.TAG_String(titles[iBook]),\
                                        "author": amulet_nbt.TAG_String("x:%d y:%d z:%d, %d"%(barrelPos[0] + chunk.cx * 16, barrelPos[1], barrelPos[2] + chunk.cz * 16, iBook)),
                                    })
                                })
                                for iBook in range(len(books))                            
                            ], list_data_type = 9\
                        )
                    })\
                })))
        chunk.block_entities.insert(barrelEntity)


def tryGetArticle(id, zimFilePath):
    """Tries to find the article with the given id, returns [False, False] if no article was found, else article and its title are returned"""

    start = time.perf_counter()
    zimFile = ZIMFile(zimFilePath,"utf-8")

    stop = time.perf_counter()
    #print("some overhead ", stop - start)

    start = time.perf_counter()
    article = zimFile._get_article_by_index(id)
    if article != None and "image" not in article.mimetype:
        articleContent = getFormatedArticle(article.data.decode("utf-8"))
        stop = time.perf_counter()  
        #print("parsing ", stop - start)

        return articleContent, article.title
    return None, None


def fillChunk(chunk, barrelPositionList, world, dimension, currentArticle, booksPerBarrel, zimfilePath):
    """Fills the chunk with all blocks and content"""
    barrel, wool, glowstone, sign_north, sign_south, air, stone, lantern = createBlocks(world)

    chunk.blocks[:,5:9:,:] = air

    chunk.blocks[:,3,:] = stone
    chunk.blocks[:,9,:] = stone

    for innerRow in [1,5,14,10]:
        for positionInRow in [6,9]:
            chunk.blocks[innerRow,7,positionInRow] = lantern
    for outerRow in [3,7,8,12]:
        for positionInRow in [1,14]:
            chunk.blocks[outerRow,7,positionInRow] = lantern

    fillSigns(chunk, world, dimension, sign_north, sign_south)

    chunk.blocks[:,4,:] = wool

    chunk.blocks[0,4,7:9] = glowstone
    chunk.blocks[0,4,0] = glowstone
    chunk.blocks[0,4,15] = glowstone
    chunk.blocks[15,4,7:9] = glowstone
    chunk.blocks[15,4,0] = glowstone
    chunk.blocks[15,4,15] = glowstone

    fillbarrels(chunk, barrelPositionList, barrel, currentArticle, booksPerBarrel, zimfilePath)

    chunk.changed = True

def placeWall(chunk, orientation, world):
    """Places a wall on the wanted side of the chunk"""
    barrel, wool, glowstone, sign_north, sign_south, air, stone, lantern = createBlocks(world)
    chunk.blocks[orientation[0],3:9,orientation[1]] = stone
    chunk.changed = True