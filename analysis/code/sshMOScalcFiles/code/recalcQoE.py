import numpy as np
import pandas
import matplotlib

import json
import os
import math
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))

import sshMOS as sshMC

def makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit):
    scenName = str(testName) + '_' + str(numCLI)
    for nodeType,numNodesType in zip(nodeTypes, nodeSplit):
        scenName += '_' + nodeType.replace('host','') + str(numNodesType)
    return scenName

def makeNodeIdentifier(nodeType, nodeNum):
    if nodeNum < 0:
        return nodeType
    else:
        return nodeType + str(nodeNum)

# Function that imports node information into a dataframe
#   - testName - name of the test
#   - numCLI - total number of clients in the test
#   - nodeSplit - number of nodes running certain applications in the test
#       [numVID, numFDO, numSSH, numVIP]
#   - nodeType - type of the node to import (String), curr. used
#       hostVID, hostFDO, hostSSH, hostVIP, links, serverSSH
#   - nodeNum - number of the node to import, omitted if -1
def importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum):
    # File that will be read
    fullScenarioExportName = makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)
    fileToRead = '../../../' + str(testName) + '/' + fullScenarioExportName + '/vectors/' + fullScenarioExportName + '_' + makeNodeIdentifier(nodeType, nodeNum) + '_vec.csv'
    print("Importing: " + fileToRead)
    # Read the CSV
    return pandas.read_csv(fileToRead)

def calcSSHnodeMOS(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)

    if not df.filter(like='roundTripTime').empty:
        colNoTS = df.columns.get_loc(df.filter(like='roundTripTime').columns[0])
        tempDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
        tempDF.rename(columns={tempDF.columns[0]: 'rtt TS', tempDF.columns[1]: 'rtt Values'}, inplace = True)
        rtts = tempDF['rtt Values'].dropna().tolist()
        mos = []
        for rtt in rtts:
            mos.append(sshMC.predictSSHmos(rtt))
        return mos
    else:
        return [-1.0]

def recalculateQoEsimulationRun(testName, numCLI, nodeTypes, nodeSplit, nodeType):
    resDF = pandas.DataFrame()
    for numN in range(nodeSplit[nodeTypes.index(nodeType)]):
        mosVals = calcSSHnodeMOS(testName, numCLI, nodeTypes, nodeSplit, nodeType, numN)
        dummyTS = [1.0 * x + 5.0 for x in range(len(mosVals))]
        resDF = pandas.concat([resDF, pandas.DataFrame({nodeType+str(numN) + ' Mos TS' : dummyTS})], axis=1)
        resDF = pandas.concat([resDF, pandas.DataFrame({nodeType+str(numN) + ' Mos Val' : mosVals})], axis=1)
    resDF.to_csv(os.path.join(file_dir,'../tempResults/'+testName+nodeType+'.csv'), index=True)

if __name__ == "__main__":
    name = sys.argv[2]
    numVID = int(name.split('VID')[1].split('_LVD')[0])
    numLVD = int(name.split('LVD')[1].split('_FDO')[0])
    numFDO = int(name.split('FDO')[1].split('_SSH')[0])
    numSSH = int(name.split('SSH')[1].split('_VIP')[0])
    numVIP = int(name.split('_VIP')[1].split('_cVIP')[0])
    numcVIP = int(name.split('_cVIP')[1])
    numCLI = numVID + numLVD + numFDO + numSSH + numVIP + numcVIP
    recalculateQoEsimulationRun(sys.argv[1], numCLI, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostcVIP'],  [numVID, numLVD, numFDO, numSSH, numVIP, numcVIP], 'hostSSH')