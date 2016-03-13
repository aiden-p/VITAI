from wordnik import *
import requests
import os

class wordnikConnection(object):
    ''' Connects to wordnik API and holds connection information '''

    def __init__(self):
        # Values set by configparser in main program.
        self.apiUrl = None
        self.apiKey = None
        self.client = None

    def setup_client(self):
        # Establish client connection
        self.client = swagger.ApiClient(self.apiKey, self.apiUrl)

class card(object):
    ''' Looks up info for words and holds that information. '''

    def __init__(self):
        # Attributes needed for cardMaker to work.
        # Values set by configparser in main program.
        self.audioSource = None
        self.defLimit = None
        self.exLimit = None

        # Card is a dictionary: {word:,defs:,examples:,audio:}
        self.cardData = {'word':None, 'defs':None,
                         'examples':None, 'audio':None}
        self.outputHeader = "#Word   Definition  Example Audio"
        self.foundWord = False

    def fetch(self, word, wordnikConn):
        ''' Reads in a word and looks up definition, pronunciation, and examples.
            Stores this information in cardData.
           
            None is returned if word/definition can't be found.
        '''
        # wordApi object to hold word's information
        wordApi = WordApi.WordApi(wordnikConn.client)
        
        # Fetch word
        wordObj = wordApi.getWord(word, useCanonical=True)
        if wordObj is None:
            # Couldn't match word.
            self.foundWord = False
            return

        # Get definitions, examples, and audio data
        defs = wordApi.getDefinitions(wordObj.word, limit=self.defLimit)
        examples = wordApi.getExamples(wordObj.word, limit=self.exLimit).examples
        request = requests.get(self.make_full_audio_link(wordObj.word))

        # Make sure a definition was found.
        if defs is None:
            self.foundWord = False
            return

        # If audio-clip not found, set to None
        if request.status_code == 200:
            audioData = request.content
        else:
            audioData = None

        # Make an ankiCard ready to be formatted for output
        ankiCard = {'word':word, 'defs':defs,
                    'examples':examples, 'audio': audioData}
        self.cardData = ankiCard

        self.foundWord = True

    def write(self, outputPaths, header=False):
        ''' Given a list of cards, card_writer will format and write information
            to a text file and create an mp3 file for the audio clip.

            If header=True, output file will be overwritten with provided header.

            card:= {'word': str,'defs':definition obj,'examples':example obj,'audio':bytes}
            outputPaths = {'audio': '/path/to/audio', 'cards': /path/to/cards/text/file.txt}
        '''
        # Anki won't correctly parse fields that contain double quotes.
        rmQuotes = str.maketrans('"', "'")

        # Write out header if needed.
        if header:
            with open(outputPaths['cards'], 'wt') as fileOut:
                print(self.outputHeader, file=fileOut)
                
        if self.cardData['audio'] is not None:
            # Create audio file name & Anki field
            audioFileName = self.cardData['word'] + ".mp3"
            audioFileFullPath = os.path.join(outputPaths['audio'], audioFileName)
            audioAnkiField = "[sound:" + audioFileName + "]"

            # Write out audio
            with open(audioFileFullPath, 'wb') as fileOut:
                fileOut.write(self.cardData['audio'])
        else:
            # No audio file, leave Anki field empty.
            audioAnkiField = '""'

        # Strip quotes, wrap each definition/example in <li></li> & create output string.
        wrappedDefs = [self.wrap_li(defn.text.translate(rmQuotes)) for defn in self.cardData['defs']]
        joinedDefs = ("").join(wrappedDefs)
        cardDefs = "Definitions:<br><ul>{0}</ul><br>".format(joinedDefs)

        if self.cardData['examples'] is None:
            # Empty field for Anki
            cardExs = '""'
        else:
            wrappedExs = [self.wrap_li(ex.text.translate(rmQuotes)) for ex in self.cardData['examples']]
            joinedExs = ("").join(wrappedExs)
            cardExs = "Examples:<br><ul>{0}</ul></br>".format(joinedExs)

        # Write out card
        with open(outputPaths['cards'], 'at') as fileOut:
            print(self.cardData['word'], cardDefs,
                  cardExs, audioAnkiField,
                  sep='\t', file=fileOut)

    def wrap_li(self, string):
        '''Wrap a string in <li align="left"></li> html tags'''
        return '<li align=\'left\'>' + string + '</li>'

    
    def make_full_audio_link(self, word):
        ''' Creates the full URL where audio file is stored '''
        return self.audioSource + word + ".mp3"
