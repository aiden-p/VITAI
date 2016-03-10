import configparser
import os
import sys

from wordnik import *
import requests


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
        
class cardMaker(object):
    ''' Given a list of words cardMaker() creates a text file
        that Anki can create cards from '''

    def __init__(self):
        # Attributes needed for cardMaker to work.
        # Values set by configparser in main program.
        self.audioSource = None
        self.audioSavePath = None
        self.outputPath = None
        self.outputHeader = None
        self.defLimit = None
        self.exLimit= None
        self.notFound = []

    def lookup(self, fileIn, wordnikConn):
        ''' Reads in list of words and looks up definition, 
            pronunciation, and examples.
           
            Unfound words are added to wordNotFound and written to a file.
        '''
        # wordApi object to hold word's information
        wordApi = WordApi.WordApi(wordnikConn.client)
        
        # Setup header info for output file
        with open(self.outputPath, 'wt') as outputFile:
            outputFile.write(self.outputHeader)

        # Iterate through list and write word info to output file.
        with open(fileIn, 'rt') as vocabIn:
            for line in vocabIn:
                wordData = wordApi.getWord(line.strip(), useCanonical=True)
                if wordData is None:
                    # Couldn't match word.
                    self.notFound.append(line.strip())
                    continue

                # Get definitions, examples, and audio data
                defs = wordApi.getDefinitions(wordData.word, limit=self.defLimit)
                examples = wordApi.getExamples(wordData.word, limit=self.exLimit).examples
                audioData = requests.get(self.generate_full_audio_link(wordData.word))

                # Make sure a definition was found.
                if defs is None:
                    continue
                
                # Write out gathered data
                with open(self.outputPath, 'at') as outputFile:
                    print(wordData.word, ", ",
                          ("<br>").join(defn.text for defn in defs), ", ",
                          ("<br>").join(ex.text for ex in examples),
                          sep="", file=outputFile)

                # Write out audio data
                with open(self.make_full_audio_path(wordData.word), 'wb') as fileOut:
                    fileOut.write(audioData.content)

                # Print out unmatched words
                if len(self.notFound) > 0:
                    print("The following words couldn't be found: ",
                          "\n".join(self.notFound), sep="")

    def generate_full_audio_link(self, word):
        ''' Creates the full URL where audio file is stored '''
        return self.audioSource + word + ".mp3"

    def make_full_audio_path(self, word):
        ''' Creates the full file path where audio file will be saved '''
        return self.audioSavePath + word + ".mp3"


def main():
    ''' Take a user inputted vocab file from the command line.
        Read config settings and run cardMaker.lookup()
     '''
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Provide one input file, please.")
        return
    else:
        inputVocabFile = sys.argv[1]

    # Check for config file
    if "config.ini" not in os.listdir(os.getcwd()):
        print("Please put the 'config.ini' file in the same folder as the program.")
        return

    # Config wordnik connection and cardMaker
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    config.read("config.ini")

    # Configure wordnikConnection object from config file
    wordnikConn = wordnikConnection()
    for attrb in wordnikConn.__dict__:
        if attrb in config["WORDNIK"]:
            setattr(wordnikConn, attrb, config["WORDNIK"][attrb])
    wordnikConn.setup_client()
    
    # Configure cardMaker object from config file
    maker = cardMaker()
    for key, value in config["CARDMAKER"].items():
        setattr(maker, key, value)
    for key, value in config["INTS"].items():
        setattr(maker, key, int(value))

        
    # Make output file for Anki
    maker.lookup(inputVocabFile, wordnikConn)
    
if __name__ == "__main__":
    main()
