import numpy as np
import pandas
import matplotlib

import json
import os
import math
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))

def makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit):
    scenName = str(testName) + '_' + str(numCLI)
    for nodeType,numNodesType in zip(nodeTypes, nodeSplit):
        scenName += '_' + nodeType.replace('host','') + str(numNodesType)
    return scenName

def remakeMOSexport(testName, numCLI, nodeTypes, nodeSplit, nodeTypesToChange):
    print(testName)
    mosResDF = pandas.read_csv('../exports/extracted/mos/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'.csv', index_col=False)
    mosResDF = mosResDF.drop(mosResDF.columns[0], axis=1)

    for typeDrop in nodeTypesToChange:
        mosResDF = mosResDF.loc[:,~mosResDF.columns.duplicated()]
        mosResDF = mosResDF[mosResDF.columns.drop(list(mosResDF.filter(regex=typeDrop)))]
        if typeDrop == 'hostSSH': 
            dfNewType = pandas.read_csv('sshMOScalcFiles/tempResults/'+testName+typeDrop+'.csv', index_col=False)
        else: 
            dfNewType = pandas.read_csv('videoMOScalcFiles/tempMOS/'+testName+typeDrop+'.csv', index_col=False)
        dfNewType = dfNewType.drop(dfNewType.columns[0], axis=1)
        mosResDF = pandas.concat([mosResDF, dfNewType.reset_index()], axis=1)

    prePath = '../exports/extracted/mos2/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    mosResDF.to_csv(os.path.join(file_dir, prePath+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'.csv'), index=True)

if __name__ == "__main__":
    name = sys.argv[2]
    numVID = int(name.split('VID')[1].split('_LVD')[0])
    numLVD = int(name.split('LVD')[1].split('_FDO')[0])
    numFDO = int(name.split('FDO')[1].split('_SSH')[0])
    numSSH = int(name.split('SSH')[1].split('_VIP')[0])
    numVIP = int(name.split('_VIP')[1].split('_cVIP')[0])
    numcVIP = int(name.split('cVIP')[1])
    numCLI = numVID + numLVD + numFDO + numSSH + numVIP + numcVIP
    remakeMOSexport(sys.argv[1], numCLI, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostcVIP'],  [numVID, numLVD, numFDO, numSSH, numVIP, numcVIP], ['hostSSH', 'hostVID', 'hostLVD'])