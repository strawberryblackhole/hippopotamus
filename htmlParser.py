from html.parser import HTMLParser
from bs4 import BeautifulSoup
import json

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

    def feed(self, in_html, zimFile, barrelPositionList, booksPerBarrel, chunkList, target_pos):
        self._data = [""]
        self._formats = [[[],[]]]
        self._attrs = []
        self._title = ""
        self._zimFile = zimFile
        self._barrelPositionList = barrelPositionList
        self._booksPerBarrel = booksPerBarrel
        self._chunkList = chunkList
        self._target_pos = target_pos
        super(MyHTMLParser, self).feed(in_html)
        articleContent =  self._data[0] 
        articleFormating =  self._formats[0]

        pages = ['{"extra":[{"text":"']
        charsOnPage = 0
        for iChar in range(len(articleContent)):
            #if page not too long
            if charsOnPage < 200:
                    
                #if the formating has to be defined
                if charsOnPage == 0 or articleFormating[0][iChar] != articleFormating[0][iChar -1] or articleFormating[1][iChar] != articleFormating[1][iChar -1]:
                    pages[-1] += '"},{'
                    if articleFormating[0][iChar] > 0:
                        pages[-1] += '"bold":true,'
                    if articleFormating[1][iChar] > 0:
                        pages[-1] += '"italic":true,'
                    pages[-1] += '"text":"'
     
                pages[-1] += json.dumps(articleContent[iChar], ensure_ascii=False)[1:-1]
                charsOnPage += 1
                if articleContent[iChar] == "\n":
                    charsOnPage += 12

            else:
                pages[-1] += '"}],"text":""}'
                pages.append('{"extra":[{')

                if articleFormating[0][iChar] > 0:
                    pages[-1] += '"bold":true,'
                if articleFormating[1][iChar] > 0:
                    pages[-1] += '"italic":true,'


                pages[-1] +='"text":"' + json.dumps(articleContent[iChar], ensure_ascii=False)[1:-1]
                charsOnPage = 0  

        pages[-1] += ' The original work has been modified."}],"text":""}'

        return json.dumps(self._title, ensure_ascii=False), pages

    def handle_data(self, data):
        self._data[-1] += data
        for formating in self._formats[-1]:
            formating.extend([0]*len(data))

    def handle_starttag(self, tag, attrs):
        self._data.append("")
        self._formats.append([[],[]])
        self._attrs.append(attrs)

    def remove_data(self, replacement = "", replacementFormatings = [0,0]):
        self._data[-1] = replacement
        self._formats[-1] = [[0] * len(replacement), [0] * len(replacement)]
        self.collaps_last_block_and_format(formatings=replacementFormatings)

    def collaps_last_block_and_format(self, prefix = "", postfix = "", formatings = [0,0]):

        self._data[-1] = prefix + self._data[-1] + postfix
        
        #extend format by pre/postfix length
        for iFormat in range(len(self._formats[-1])):
            #turn on formating, but dont turn it off (because allready collapsed formats should keep their formating and should not be overwritten)
            for iElement in range(len(self._formats[-1][iFormat])):
                self._formats[-1][iFormat][iElement] += formatings[iFormat]
            
            self._formats[-1][iFormat][:0] = [formatings[iFormat]] * len(prefix) 
            self._formats[-1][iFormat].extend([formatings[iFormat]] * len(postfix))

        #collaps the last array entry
        self._data[-2] += self._data[-1]
        for iFormat in range(len(self._formats[-2])):
            self._formats[-2][iFormat].extend(self._formats[-1][iFormat])

        #delete last array entry
        self._data.pop()
        self._formats.pop()
        self._attrs.pop()

    def handle_endtag(self, tag): 
        if tag == 'a' :
            foundiAtt = -1
            for iAtt in range(len(self._attrs[-1])):
                try:
                    self._attrs[-1][iAtt].index("href")
                    foundiAtt = iAtt
                    break
                except ValueError:
                    continue


            if foundiAtt != -1:
                url = self._attrs[-1][iAtt][1].split("#")[0]
                entry, idx = self._zimFile._get_entry_by_url("A", url)
                if(idx != None):
                    location = getArticleLocationById(idx,self._barrelPositionList, self._booksPerBarrel, self._chunkList, self._target_pos)
                    self.collaps_last_block_and_format("", "[ID %d at x:%d y:%d z:%d]"%tuple([idx] + location))
                else:
                    self.collaps_last_block_and_format("", "[%s]"%url)
            else:
                self.collaps_last_block_and_format()              
        elif tag == 'br' :
            self.collaps_last_block_and_format("\n", "")
        elif tag == 'div' :
            if self._data[-1] != "" and self._data[-1][-1] != "\n":
                self.collaps_last_block_and_format("\n ", "\n")
            else:
                self.collaps_last_block_and_format()
        elif tag == 'h1' :
            if ('class', 'section-heading') in self._attrs[-1]: #if its the title of the article
                self._title = self._data[-1]
                self.collaps_last_block_and_format("", "\n", [1,0])
            else:
                self.collaps_last_block_and_format("\n\n", "\n", [1,0])
        elif tag == 'h2' :
            self.collaps_last_block_and_format("\n\n", "\n", [1,0])
        elif tag == 'h3' :
            self.collaps_last_block_and_format("\n\n", "\n")
        elif tag == 'li' :
            self.collaps_last_block_and_format("\n -", "")
        elif tag == 'p' :
            if self._data[-1] != "":
                self.collaps_last_block_and_format("\n ", "\n")
            else:
                self.collaps_last_block_and_format()
        elif tag == 'ol' :
            self.collaps_last_block_and_format("\n")
        elif tag == 'ul' :
            self.collaps_last_block_and_format("\n")
        elif tag == 'script' :
            self.remove_data()
        elif tag == 'style' :
            self.remove_data()
        elif tag == 'table' :
            self.remove_data("\nCan't display table\n", [0,1])
        elif tag == 'title' :
            self.remove_data()
        else:
            self.collaps_last_block_and_format()

def getArticleLocationById(id, barrelPositionList, booksPerBarrel, chunkList, target_pos):

    booksPerChunk = len(barrelPositionList) * booksPerBarrel
    chunk = int(id) // booksPerChunk
    bookNumberInChunk = (int(id) - chunk * booksPerChunk)
    barrel = (bookNumberInChunk - 1)// booksPerBarrel #-1 because if booksNumberInChunk == booksPerBarrel, it should be 0

    return [chunkList[chunk][0] * 16 + barrelPositionList[barrel][0] + target_pos[0], barrelPositionList[barrel][1], chunkList[chunk][1] * 16 + barrelPositionList[barrel][2] + target_pos[1]]
   


def getFormatedArticle(html, zimFile, barrelPositionList, booksPerBarrel, chunkList, target_pos):
    parser = MyHTMLParser()
    soup = BeautifulSoup(html, features ="html.parser")
    title, text = parser.feed(str(soup).replace("\n", "").replace("\t", ""), zimFile, barrelPositionList, booksPerBarrel, chunkList, target_pos) 
    #text = parser.feed(html.replace("\n", "").replace("\t", "")) # some things break when not using bfs
    parser.close()

    return title, text
