from html.parser import HTMLParser
from bs4 import BeautifulSoup


class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

    def feed(self, in_html):
        self._data = [""]
        self._formats = [[]]
        self._attrs = []
        super(MyHTMLParser, self).feed(in_html)
        articleContent =  self._data[0] 

        pages = ['{"extra":[{"text":"']#'{"text":"","color":"red"}'
        charsOnPage = 0
        for iChar in range(len(articleContent)):
            if charsOnPage < 200:
                formating = [x for x in self._formats[0] if x[0] == iChar]
                if len(formating) > 0:
                    if len(formating) > 1:
                        if formating[0][1] == formating[1][1]:
                            raise Exception()
                        continue

                    if formating[0][1] == "bt":
                        pages[-1] += '"},{"bold":true,"text":"'
                    elif formating[0][1] == "bf":
                        pages[-1] += '"},{"text":"'
     
                pages[-1] += articleContent[iChar]
                charsOnPage += 1
                if articleContent[iChar] == "\n":
                    charsOnPage += 12


            else:
                pages[-1] += '"}],"text":""}'
                pages.append('{"extra":[{')

                formating = [x for x in self._formats[0] if x[0] == iChar]
                if len(formating) > 0:
                    if len(formating) > 1:
                        if formating[0][1] == formating[1][1]:
                            raise Exception()
                        pages[-1] +='"text":"' + articleContent[iChar]
                        charsOnPage = 0  
                        continue

                    if formating[0][1] == "bt":
                        pages[-1] += '"bold":true,'
                    elif formating[0][1] == "bf":
                        pass


                pages[-1] +='"text":"' + articleContent[iChar]
                charsOnPage = 0  

        pages[-1] += ' The original work has been modified."}],"text":""}'

        return  pages

    def handle_data(self, data):
        self._data[-1] += data

    def handle_starttag(self, tag, attrs):
        self._data.append("")
        self._formats.append([])
        self._attrs.append(attrs)

    def remove_data(self, replacement = ""):
        self._data[-2] += replacement
        self._data.pop()
        self._formats.pop()
        self._attrs.pop()

    def collapse_last_block(self, prefix = "", postfix = ""):
        for element in self._formats[-1]:
            element[0] += len(prefix) + len(self._data[-2])

        self._data[-2] += prefix + self._data[-1] + postfix
        self._formats[-2].extend(self._formats[-1])

        self._data.pop()
        self._formats.pop()
        self._attrs.pop()

    def collapse_last_block_and_format(self, prefix = "", postfix = "", formating = ""):
        if formating != "":
            self._formats[-1].append([-len(prefix), formating + "t"])#undo / dont do what will be done when collapsing the string
            self._formats[-1].append([len(self._data[-1]) + len(postfix), formating + "f"])

        self.collapse_last_block(prefix, postfix)

    def handle_endtag(self, tag): 
        if tag == 'p' :
            if self._data[-1] != "":
                self.collapse_last_block("\n ", "\n")
            else:
                self.collapse_last_block()
        elif tag == 'ul' :
            self.collapse_last_block("\n")
        elif tag == 'ol' :
            self.collapse_last_block("\n")
        elif tag == 'div' :
            if self._data[-1] != "" and self._data[-1][-1] != "\n":
                self.collapse_last_block("\n ", "\n")
            else:
                self.collapse_last_block()
        elif tag == 'h3' :
            self.collapse_last_block_and_format("\n\n", "\n", "")
        elif tag == 'h2' :
            self.collapse_last_block_and_format("\n\n", "\n", "b")
        elif tag == 'h1' :
            if ('class', 'section-heading') in self._attrs[-1]: #if its the title of the article
                self.collapse_last_block_and_format("", "\n", "b")
            else:
                self.collapse_last_block_and_format("\n\n", "\n", "")
        elif tag == 'li' :
            self.collapse_last_block("\n -", "")
        elif tag == 'br' :
            self.collapse_last_block("\n", "")
        elif tag == 'script' :
            self.remove_data()
        elif tag == 'style' :
            self.remove_data()
        elif tag == 'title' :
            self.remove_data()
        elif tag == 'table' :
            self.remove_data("\nCan't display table\n")
        else:
            self.collapse_last_block()
        


def getFormatedArticle(html):
    parser = MyHTMLParser()
    soup = BeautifulSoup(html, features ="html.parser")
    text = parser.feed(str(soup).replace("\n", "").replace("\t", "")) #bfs processing time is roughly 1/4 of this functions time, and is probably not needed. But it seems to make the html much nicer
    #text = parser.feed(html.replace("\n", "").replace("\t", "")) # some things break when not using bfs
    parser.close()

    return text
