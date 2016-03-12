import configparser
import os
import sys

import utils

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
    script_root = os.path.dirname(os.path.realpath(__file__))
    parent_root = os.path.abspath(os.path.join(script_root, os.pardir))
    if "config.ini" not in os.listdir(parent_root):
        print("Please put the 'config.ini' file in the parent folder of the program.")
        return

    # Setup configparser to be case-sensitive for keys via .optionxform
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    config.read("config.ini")

    # Get output paths from config file.
    outputPaths = {}
    outputPaths['cards'] = config["FILES"]["outputFile"]
    outputPaths['audio'] = config["PATHS"]["audioOutPath"]
    
    # Configure wordnikConnection object from config file
    wordnikConn = utils.wordnikConnection()
    for key, value in config["WORDNIK"].items():
        if key in wordnikConn.__dict__:
            setattr(wordnikConn, key, value)
    wordnikConn.setup_client()
    
    # Configure cardMaker object from config file
    ankiCard = utils.card()
    for key, value in config["CARD"].items():
        if key in ankiCard.__dict__:    
            setattr(ankiCard, key, value)
    for key, value in config["INTS"].items():
        if key in ankiCard.__dict__:
            setattr(ankiCard, key, int(value))

    # Read in vocab file.
    with open(inputVocabFile, 'rt') as fileIn:        
        vocabList = [line.strip() for line in fileIn if line.strip() is not '']

    # Header for output file -- set to false after first card written to file.
    firstTime = True
    
    # Lookup and write out words
    for word in vocabList:
        ankiCard.fetch(word, wordnikConn)
        if not ankiCard.foundWord:
            print("Unable to find '{word}'.".format(word=word))
            continue

        ankiCard.write(outputPaths, header=firstTime)
        firstTime = False

    # All done!
    return
    
if __name__ == "__main__":
    main()
