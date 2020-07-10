This project aims to provide a tool that generates a structure in a minecraft world that contains every single wikipedia article.


## Installation
Install https://github.com/Amulet-Team/Amulet-Map-Editor from source 
Latest known working commit is a0b729f0ee3767cf0b583a94eddf9d412d2cd0a3

## Usage
First you need to get a ZIM file of the wiki that you want to integrate into minecraft. You can find some here:
Then you need to find out how many chunks this will occupy. For this run the program without specifying a world. It will stop after it has loaded the wiki file (which can take a few minutes if its big) and provide you with the corner chunks of the square area that will be occupied.
These chunks have to be present in your world file. If you havent visited them, they are not. To make sure that they are present, fly over them or use a tool like https://github.com/strawberryblackhole/ChunkGenerator (If you use a world file from the spigot server and run into problems opening it with Amulet, try opening an saving it once with the Minecraft client.
Afterwards run the command again and it will start filling the chunks. It can take a few minutes per chunk. It prints you the status, so that you can resume after a break or crash.
