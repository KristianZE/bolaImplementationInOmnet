import numpy as np
import pandas
import matplotlib
import matplotlib.pyplot as plt

import json
import os
import math
import statistics
import sys

import csvToJsonV2 as csv2j
import calcQoE as calQoE

file_dir = os.path.dirname(os.path.abspath(__file__))

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

def createTempCSV(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    colList = ['DASHBufferLengthTS','DASHBufferLengthValues','DASHReceivedBytesTS','DASHReceivedBytesValues','DASHVideoBitrateTS','DASHVideoBitrateValues','DASHVideoResolutionTS','DASHVideoResolutionValues','DASHVideoPlaybackPointerTS','DASHVideoPlaybackPointerValues','DASHVideoPlaybackStatusTS','DASHVideoPlaybackStatusValues']
    newDF = pandas.DataFrame()
    for col in colList[::2]:
        valName = col.replace('TS','')
        colNoTS = df.columns.get_loc(df.filter(like=valName).columns[0])
        tempDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
        tempDF.rename(columns={tempDF.columns[0]: valName+'TS', tempDF.columns[1]: valName+'Values'}, inplace = True)
        if valName == 'DASHVideoResolution':
            tempDF = tempDF.replace(to_replace={240 : "426x240", 360 : "640x360", 480 : "854x480", 720 : "1280x720", 1080 : "1920x1080"})
        newDF = pandas.concat([newDF, tempDF], axis=1)
    
    videoStarts = newDF.loc[newDF['DASHVideoPlaybackPointerValues'] == 0.0]['DASHVideoPlaybackPointerTS'].tolist()[1:]
    numVids = 0
    prevVidStart = 0.0
    for videoStart in videoStarts:
        videoDF = pandas.DataFrame()
        if prevVidStart != 0.0: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHBufferLengthTS'] <= videoStart) & (newDF['DASHBufferLengthTS'] >= prevVidStart)][['DASHBufferLengthTS','DASHBufferLengthValues']][1:-1].dropna().reset_index(drop=True)], axis=1)
        else: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHBufferLengthTS'] <= videoStart) & (newDF['DASHBufferLengthTS'] >= prevVidStart)][['DASHBufferLengthTS','DASHBufferLengthValues']][:-1].dropna().reset_index(drop=True)], axis=1)
        
        if prevVidStart != 0.0:
            rbDF = newDF.loc[(newDF['DASHReceivedBytesTS'] <= videoStart) & (newDF['DASHReceivedBytesTS'] >= prevVidStart)][['DASHReceivedBytesTS','DASHReceivedBytesValues']].dropna().reset_index(drop=True)
            rbDF.loc[-1] = [0.0, 0.0]  # adding a row
            rbDF.index = rbDF.index + 1  # shifting index
            rbDF.sort_index(inplace=True) 
            videoDF = pandas.concat([videoDF, rbDF], axis=1)
        else: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHReceivedBytesTS'] <= videoStart) & (newDF['DASHReceivedBytesTS'] >= prevVidStart)][['DASHReceivedBytesTS','DASHReceivedBytesValues']].dropna().reset_index(drop=True)], axis=1)
        
        if prevVidStart != 0.0:
            vbDF = newDF.loc[(newDF['DASHVideoBitrateTS'] <= videoStart) & (newDF['DASHVideoBitrateTS'] >= prevVidStart)][['DASHVideoBitrateTS','DASHVideoBitrateValues']].dropna().reset_index(drop=True)
            vbDF.loc[-1] = [0.0, 0.0]  # adding a row
            vbDF.index = vbDF.index + 1  # shifting index
            vbDF.sort_index(inplace=True) 
            videoDF = pandas.concat([videoDF, vbDF], axis=1)
        else: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHVideoBitrateTS'] <= videoStart) & (newDF['DASHVideoBitrateTS'] >= prevVidStart)][['DASHVideoBitrateTS','DASHVideoBitrateValues']].dropna().reset_index(drop=True)], axis=1)
        
        if prevVidStart != 0.0:
            vrDF = newDF.loc[(newDF['DASHVideoResolutionTS'] <= videoStart) & (newDF['DASHVideoResolutionTS'] >= prevVidStart)][['DASHVideoResolutionTS','DASHVideoResolutionValues']].dropna().reset_index(drop=True)
            vrDF.loc[-1] = [0.0, 0.0]  # adding a row
            vrDF.index = vrDF.index + 1  # shifting index
            vrDF.sort_index(inplace=True) 
            videoDF = pandas.concat([videoDF, vrDF], axis=1)
        else: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHVideoResolutionTS'] <= videoStart) & (newDF['DASHVideoResolutionTS'] >= prevVidStart)][['DASHVideoResolutionTS','DASHVideoResolutionValues']].dropna().reset_index(drop=True)], axis=1)
        
        if prevVidStart != 0.0: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHVideoPlaybackPointerTS'] <= videoStart) & (newDF['DASHVideoPlaybackPointerTS'] >= prevVidStart)][['DASHVideoPlaybackPointerTS','DASHVideoPlaybackPointerValues']][1:-1].dropna().reset_index(drop=True)], axis=1)
        else: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHVideoPlaybackPointerTS'] <= videoStart) & (newDF['DASHVideoPlaybackPointerTS'] >= prevVidStart)][['DASHVideoPlaybackPointerTS','DASHVideoPlaybackPointerValues']][:-1].dropna().reset_index(drop=True)], axis=1)
        
        if prevVidStart != 0.0: 
            psDF = newDF.loc[(newDF['DASHVideoPlaybackStatusTS'] <= videoStart) & (newDF['DASHVideoPlaybackStatusTS'] >= prevVidStart)][['DASHVideoPlaybackStatusTS','DASHVideoPlaybackStatusValues']].dropna().reset_index(drop=True)
            psDF = psDF.drop(psDF.index[[1]]).reset_index(drop=True)
            videoDF = pandas.concat([videoDF, psDF], axis=1)
        else: videoDF = pandas.concat([videoDF, newDF.loc[(newDF['DASHVideoPlaybackStatusTS'] <= videoStart) & (newDF['DASHVideoPlaybackStatusTS'] >= prevVidStart)][['DASHVideoPlaybackStatusTS','DASHVideoPlaybackStatusValues']].dropna().reset_index(drop=True)], axis=1)
        
        videoDF.to_csv(os.path.join(file_dir,'../tempCSV/'+testName+nodeType+str(nodeNum)+'vid'+str(numVids)+'.csv'), index=False)
        prevVidStart = videoStart
        # print(testName.replace('_SSH50VIP50VID50LVD50FDO50','').replace('_LVD-BWS_AlgoTest','').replace('_AlgoTest',''), nodeType, str(nodeNum), end='  \t')
        # print('Vid Len:', videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1], end='\t')
        # fig, ax = plt.subplots(1, figsize=(16,12))
        xPlotTemp = videoDF.filter(like='DASHVideoResolution')['DASHVideoResolutionValues'].dropna().tolist()
        xPlot = []
        qualiLevNum = [0,0,0,0,0]
        for elem in xPlotTemp:
            if elem == "426x240":
                xPlot.append(240)
                qualiLevNum[0] += 1
            elif elem == "640x360":
                xPlot.append(360)
                qualiLevNum[1] += 1
            elif elem == "854x480":
                xPlot.append(480)
                qualiLevNum[2] += 1
            elif elem == "1280x720":
                xPlot.append(720)
                qualiLevNum[3] += 1
            elif elem == "1920x1080":
                xPlot.append(1080)
                qualiLevNum[4] += 1
        # print('426x240:', qualiLevNum[0], end='\t')
        # print('640x360:', qualiLevNum[1], end='\t')
        # print('854x480:', qualiLevNum[2], end='\t')
        # print('1280x720:', qualiLevNum[3], end='\t')
        # print('1920x1080:', qualiLevNum[4], end='\t')
        qualiIncrease = 0
        qualiDecrease = 0
        qualiSame = 0
        for elem in [xPlot[x] - xPlot[x-1] for x in range(1, len(xPlot))]:
            if elem > 0:
                qualiIncrease += 1
            elif elem < 0:
                qualiDecrease += 1
            else:
                qualiSame += 1
        # print('Inc:', qualiIncrease, end='\t')
        # print('Dec:', qualiDecrease, end='\t')
        # print('Same:', qualiSame, end=';\t')
        # print('InterSwitchUpTime:', round(videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1]/(qualiIncrease),2), end=';\t')
        # print('InterSwitchDownTime:', round(videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1]/(qualiDecrease),2), end=';\t')
        # print('InterSwitchTime:', round(videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1]/(qualiIncrease+qualiDecrease),2), end=';\tMOS: ')
        # ax.plot(videoDF.filter(like='DASHVideoResolution')['DASHVideoResolutionTS'].dropna().tolist()[1:], [xPlot[x] - xPlot[x-1] for x in range(1, len(xPlot))])
        # plt.xlabel('Time')
        # plt.ylabel('Bitrate')
        # fig.savefig('../plots/resDiff'+testName+nodeType+str(nodeNum)+'.png', dpi=100, bbox_inches='tight', format='png')
        # plt.close('all')
        numVids += 1
    # print(numVids)
    return numVids#, round(videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1]/(qualiIncrease),2), round(videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1]/(qualiDecrease),2), round(videoDF.filter(like='DASHVideoPlaybackPointer')['DASHVideoPlaybackPointerValues'].dropna().tolist()[-1]/(qualiIncrease+qualiDecrease),2)
    # print(newDF)
    # newDF.to_csv('/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempCSV/'+testName+nodeType+str(nodeNum)+'.csv', index=False)
    
# createTempCSV('baselineTestNS_2sli_LVD-BWS_AlgoTest_210mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostVID', 37)
# csv2j.toJson('/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempCSV/'+'baselineTestNS_2sli_LVD-BWS_AlgoTest_210mbps_SSH50VIP50VID50LVD50FDO50_alpha00'+'.csv','/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempJSON/test.json','test',int(5))
# calQoE.cal_ITUp1203('/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempJSON/test.json','test', '/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempMOS/test.json')

# print(calQoE.cal_ITUp1203('/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempJSON/test.json','test', '/home/marcin/marcin-master-thesis/analysis/code/videoMOScalcFiles/tempMOS/test.json'))

def recalculateQoENode(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, segLen):
    # numVids, upTime, downTime, allTime = createTempCSV(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    numVids = createTempCSV(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    mosVals = []
    for i in range(numVids):
        csv2j.toJson(os.path.join(file_dir,'../tempCSV/'+testName+nodeType+str(nodeNum)+'vid'+str(i)+'.csv'),os.path.join(file_dir,'../tempJSON/'+testName+nodeType+str(nodeNum)+'vid'+str(i)+'.json'),testName+nodeType+str(nodeNum)+'vid'+str(i),segLen)
        mosVals.append(calQoE.cal_ITUp1203(os.path.join(file_dir,'../tempJSON/'+testName+nodeType+str(nodeNum)+'vid'+str(i)+'.json'),testName+nodeType+str(nodeNum)+'vid'+str(i)))
    # print(mosVals[0])
    return mosVals#, upTime, downTime, allTime

# recalculateQoENode('baselineTestNS_2sli_LVD-BWS_AlgoTest_210mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostVID', 37, 5)
# recalculateQoENode('baselineTestNS_2sli_LVD-BWS_AlgoTest_210mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostLVD', 4, 1)

# recalculateQoENode('baselineTestNS_2sli_LVD-BWS_AlgoTest_150mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostVID', 2, 5)
# recalculateQoENode('baselineTestNS_2sli_LVD-BWS_AlgoTest_150mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostVID', 3, 5)

def recalculateQoEsimulationRun(testName, numCLI, nodeTypes, nodeSplit, nodeType, segLen):
    resDF = pandas.DataFrame()
    upTimes = []
    downTimes = []
    allTimes = []
    for numN in range(nodeSplit[nodeTypes.index(nodeType)]):
        # mosVals, upTime, downTime, allTime = recalculateQoENode(testName, numCLI, nodeTypes, nodeSplit, nodeType, numN, segLen)
        mosVals = recalculateQoENode(testName, numCLI, nodeTypes, nodeSplit, nodeType, numN, segLen)
        # upTimes.append(upTime)
        # downTimes.append(downTime)
        # allTimes.append(allTime)
        # print(mosVals[0])
        dummyTS = [1.0 * x + 5.0 for x in range(len(mosVals))]
        resDF = pandas.concat([resDF, pandas.DataFrame({nodeType+str(numN) + ' Mos TS' : dummyTS})], axis=1)
        resDF = pandas.concat([resDF, pandas.DataFrame({nodeType+str(numN) + ' Mos Val' : mosVals})], axis=1)
    resDF.to_csv(os.path.join(file_dir,'../tempMOS/'+testName+nodeType+'.csv'), index=True)
    # print(resDF)
    # print(testName.replace('_SSH50VIP50VID50LVD50FDO50','').replace('_LVD-BWS_AlgoTest','').replace('_AlgoTest',''), 'Mean Upswitch time:', statistics.mean(upTimes), 'Mean Downswitch time:', statistics.mean(downTimes), 'Mean Switch time:', statistics.mean(allTimes))

# recalculateQoEsimulationRun('baselineTestNS_2sli_LVD-BWS_AlgoTest_210mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostLVD', 1)
# recalculateQoEsimulationRun('baselineTestNS_2sli_LVD-BWS_AlgoTest_210mbps_SSH50VIP50VID50LVD50FDO50_alpha00', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 'hostVID', 5)


if __name__ == "__main__":
    name = sys.argv[2]
    numVID = int(name.split('VID')[1].split('_LVD')[0])
    numLVD = int(name.split('LVD')[1].split('_FDO')[0])
    numFDO = int(name.split('FDO')[1].split('_SSH')[0])
    numSSH = int(name.split('SSH')[1].split('_VIP')[0])
    numVIP = int(name.split('_VIP')[1].split('_cVIP')[0])
    numcVIP = int(name.split('cVIP')[1])
    numCLI = numVID + numLVD + numFDO + numSSH + numVIP + numcVIP
    recalculateQoEsimulationRun(sys.argv[1], numCLI, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostcVIP'],  [numVID, numLVD, numFDO, numSSH, numVIP, numcVIP], 'hostLVD', 1)
    recalculateQoEsimulationRun(sys.argv[1], numCLI, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostcVIP'],  [numVID, numLVD, numFDO, numSSH, numVIP, numcVIP], 'hostVID', 5)