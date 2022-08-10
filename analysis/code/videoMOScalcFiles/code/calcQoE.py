import json
import os
from ITUp1203.itu_p1203 import P1203Standalone

import sys

'''Calculate P.1203 scores based on JSON input file and dump all score dicts into another json file
Input: Pway(optional argument)  - Pa calculating audio scores
                                - Pv calculating video scores
                                - Pq calculating audio visual integration
                                - Pc calculating complete  P.1203 scores
       folder - contains the JSON_formatted input files
       
Output: Json file contains the score dicts
'''
def cal_ITUp1203(inputJsonFile,name):#, outJsonFile):
    # PC={} #complete
    fname=inputJsonFile
    with open(fname, 'r') as f:
        #load JSON_formatted input information from Json files
        jsonf = json.load(f)
        PCscore=P1203Standalone(jsonf,quiet=True).calculate_complete(print_intermediate=True)
        # PCscore['O46']
        # with open(outJsonFile, 'w+') as outfile:
        #     outfile.write(str(PCscore['O46']))
            # json.dump(PCscore,outfile,sort_keys=False, indent=4, separators=(',', ':'))
        # print(PCscore['O23'], end='; ')
    return PCscore['O46']
# if __name__ == "__main__":
#     print("Calculating QoE for ", end='')
#     inputJsonFile = sys.argv[1]
#     name = sys.argv[2]
#     outJsonFile = sys.argv[3]
#     print(name, end=' processing... ')
#     cal_ITUp1203(inputJsonFile,name, outJsonFile)
#     print("Done!")

