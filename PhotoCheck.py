# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:31:13 2021

@author: james
"""

import sys
import os
import datetime
from PIL import Image
import imagehash
import datetime

hashes  = {"HASH" : "FILE"}
#duplicates_dict = {"HASH" : 1}
duplicates = []

def main(argv):
        
    for item in os.listdir(argv):
        root, extension = os.path.splitext(item)
        extension = extension.lower()
        
        if os.path.isdir(argv +'\\' + item):
            print ("SubFolder: " + item)
            main(argv +'\\' + item)
            
        if extension == ".png" or extension == ".jpg" or extension == ".jpeg" or extension == ".bmp":
            hash = imagehash.phash(Image.open(argv +'\\' + item),16)
            
            if str(hash) in hashes:
                print("DUPLICATE/SIMILAR IMAGE")
                
                found = False
                for row in range(len(duplicates)):
                    if duplicates[row][0] == ('#' + str(hash)) and not len(duplicates) == 0:
                       duplicates[row].append('\t'+ argv +'\\' + item)
                       break
                if not found:
                    duplicates.append(['#'+str(hash),'\t'+hashes[str(hash)],'\t'+ argv +'\\' + item])
            else:
                hashes[str(hash)] = argv +'\\' + item
                #print(item)
        # elif os.path.isdir(argv +'\\' + item):
        #         print ("SubFolder: " + item)
        #         main(argv +'\\' + item)
                
    print("Done Folder")
    return 0


if __name__ == "__main__":
   hashes  = {"HASH" : "FILE"}
   #duplicates_dict = {"HASH" : 1}
   duplicates = []
   
   main(sys.argv[1])
   
   if len(duplicates) == 0:
       print("No Duplicate/Similar Photos Found")
   else:
       date = datetime.datetime.now()
       file_path = ('\\'.join(sys.argv[0].split('\\')[0:-1]) +'\\' + 
                        'PhotoDuplicates ' + str(date).replace(':','.') +'.txt' )
       with open(file_path, 'w') as output:
           for row in duplicates:
               for column in row:
                   output.write(str(column) + '\n')
       output.close()
       print(sys.argv[0].split('\\')[-1] + " Done")
       print("Duplicate/Similar Photos Found. Please check Text file")
