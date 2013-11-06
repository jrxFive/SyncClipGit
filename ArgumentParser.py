__author__ = 'jxfivex1c-xubuntu'

import argparse

class ArgumentParser(object):

    def __init__(self):
        self.dummy = " "

    def argSetup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-g", "--get", help="Put integer value from list as current copy on clipboard", type=int,
                            dest="g")
        parser.add_argument("-l", "--list", help="List most recent synced clips")
        parser.add_argument("-u", "--update", help="Request update from server database")
        parser.add_argument("-x", "--exit", help="Terminate program")

        arguments = vars(parser.parse_args())

        return arguments



