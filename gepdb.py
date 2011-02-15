#!/usr/bin/env python
"gepdb - graphical user interface for epdb"


import argparse

from gepdb.guipdb import GuiPdb    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Start the application logic for the poll website')
    parser.add_argument('file',
        help='Give the filename to execute in debug mode', nargs='?')
    args = parser.parse_args()
    #print args.file[0]

    if args.file:
        guipdb = GuiPdb(args.file)
    else:
        guipdb = GuiPdb()
    guipdb.main()

