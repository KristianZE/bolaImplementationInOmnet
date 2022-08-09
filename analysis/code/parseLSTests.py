import pandas
import csv
import statistics
from termcolor import colored
import sys
import os
import math
from scipy.stats import sem, t

maxSimTime = 400
DEBUG = 0

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']

def makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit):
    scenName = str(testName) + '_' + str(numCLI)
    for nodeType,numNodesType in zip(nodeTypes, nodeSplit):
        scenName += '_' + nodeType.replace('host','') + str(numNodesType)
    return scenName
    # return str(testName) + '_' + str(numCLI) + '_VID' + str(nodeSplit[0]) + '_FDO' + str(nodeSplit[1]) + '_SSH' + str(nodeSplit[2]) + '_VIP' + str(nodeSplit[3])

def makeNodeIdentifier(tp, delay, nodeType, nodeNum):
    return 'tp' + str(tp) + '_del' + str(delay) + '_' + nodeType + str(nodeNum)

# Function that imports node information into a dataframe
#   - testName - name of the test
#   - numCLI - total number of clients in the test
#   - nodeSplit - number of nodes running certain applications in the test
#       [numVID, numFDO, numSSH, numVIP]
#   - nodeType - type of the node to import (String), curr. used
#       hostVID, hostFDO, hostSSH, hostVIP, links, serverSSH
#   - nodeNum - number of the node to import, omitted if -1
def importDF(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum):
    # File that will be read
    fullScenarioExportName = makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)
    fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + testName + '_' + makeNodeIdentifier(tp, delay,nodeType, nodeNum) + '_vec.csv'
    print("Importing: " + fileToRead)
    # Read the CSV
    return pandas.read_csv(fileToRead)

def filterDFType(df, filterType):
    return df.filter(like=filterType)

def makeSNI(nodeType, nodeNum):
    return str(nodeType) + str(nodeNum)

def getFilteredDFtypeAndTS(df, filterType, nodeType, nodeNum):
    filteredDF = filterDFType(df, filterType)
    if len(filteredDF.columns):
        colNoTS = df.columns.get_loc(df.filter(filteredDF).columns[0])
        newDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
        newDF = newDF.rename(columns={str(newDF.columns[0]) : 'TS ' + makeSNI(nodeType, nodeNum), str(newDF.columns[1]) : filterType + ' Val ' + makeSNI(nodeType, nodeNum)})
        return newDF
    else:
        return pandas.DataFrame(columns=['TS ' + makeSNI(nodeType, nodeNum), filterType + ' Val ' + makeSNI(nodeType, nodeNum)])

def extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType):
    print(valueType + ' - ', end='')
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum)
    filteredDF = getFilteredDFtypeAndTS(df, valueType, nodeType, nodeNum)
    # print(filteredDF)
    return filteredDF

def extractValuesTypeForAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, valueType):
    valuesDF = pandas.DataFrame()
    for i in range(nodeSplit[nodeTypes.index(nodeType)]):
        valuesDF = valuesDF.append(extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, i, valueType))
    # print(valuesDF)
    return valuesDF

def getMeanValueTypeForAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, valueType):
    valuesDF = extractValuesTypeForAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, valueType)
    allValues = []
    for i in range(nodeSplit[nodeTypes.index(nodeType)]):
        filteredDF = filterDFType(valuesDF, 'Val ' + makeSNI(nodeType, i))
        allValues.extend(filteredDF.iloc[:,0].dropna().tolist())
        # print(filteredDF)
    # print(allValues)
    if len(allValues) > 0:
        meanValue = statistics.mean(allValues)
        stdDevValue = statistics.stdev(allValues)
        confidence = 0.95
        n = len(allValues)
        std_err = sem(allValues)
        ci95hVal = std_err * t.ppf((1 + confidence) / 2, n - 1)
        minVal = min(allValues)
        maxVal = max(allValues)
        numVal = len(allValues)
    else:
        meanValue = -1
        stdDevValue = 0
        ci95hVal = 0
        minVal = -1
        maxVal = -1
        numVal = 0
    print(meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal)
    return meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal

def getMeanValuesTypeForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, valueType):
    print('Extracting for ' + valueType + ':')
    meanValues = []
    for delay in delays:

        meanValues.append(getMeanValueTypeForAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, valueType))
    # print(meanValues)
    prePath = '../exports/extracted/' + valueType + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(delays)
        fw.writerow(meanValues)

def getMeanValuesTypeForStressExperiment(testName, nodeTypes, nodeSplits, tp, delay, nodeType, valueType):
    print('Extracting for ' + valueType + ':')
    numNodes = []
    meanValues = []
    stdDevValues = []
    ci95hValues = []
    minValues = []
    maxValues = []
    numValues = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal = getMeanValueTypeForAllNodes(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, valueType)
        meanValues.append(meanValue)
        stdDevValues.append(stdDevValue)
        ci95hValues.append(ci95hVal)
        minValues.append(minVal)
        maxValues.append(maxVal)
        numValues.append(numVal)
    # print(meanValues)
    prePath = '../exports/extracted/' + valueType + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(meanValues)
        fw.writerow(stdDevValues)
        fw.writerow(ci95hValues)
        fw.writerow(minValues)
        fw.writerow(maxValues)

def getFilteredDFtypeAndTSServer(df, filterType, nodeType):
    filteredDF = filterDFType(df, filterType)
    # print(list(filteredDF))
    if len(filteredDF.columns):
        retDF = pandas.DataFrame()
        for i in range(len(filteredDF.columns)):
            colNoTS = df.columns.get_loc(df.filter(filteredDF).columns[i])
            newDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
            newDF = newDF.rename(columns={str(newDF.columns[0]) : filterType + 'TS ' + str(nodeType), str(newDF.columns[1]) : filterType + ' Val ' + str(nodeType)})
            retDF = retDF.append(newDF, ignore_index=True)
        # print(retDF)
        return retDF
    else:
        return pandas.DataFrame(columns=[filterType + 'TS ' + str(nodeType), filterType + ' Val ' + str(nodeType)])

def getMeanValueTypeForServer(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, valueType): # Actually NOT MEAN BUT SUM!!!!
    serverDF = importDF(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, '')
    print('Import DONE!')
    valuesDF = serverDF.shift(periods=-1, axis='columns').loc[:,::2].filter(like=valueType)
    serverDF = serverDF.iloc[0:0]
    print('Filtering DONE!')
    sumOfPeaks = 0
    for i in range(len(valuesDF.columns)):
        # print(valuesDF.iloc[:,i].max())
        if valueType == 'dupAcks':
            localSumOfPeaks = valuesDF.iloc[:,i][(valuesDF.iloc[:,i].shift(1) < valuesDF.iloc[:,i]) & (valuesDF.iloc[:,i].shift(-1) < valuesDF.iloc[:,i])].sum()
        elif valueType == 'numRtos':
            localSumOfPeaks = valuesDF.iloc[:,i].max()
        # print(localSumOfPeaks)
        sumOfPeaks += localSumOfPeaks

    print('Lost packet values extraction DONE! Lost packets due to ' + valueType + ': ' + str(sumOfPeaks))
    # print(sumOfPeaks)

    return sumOfPeaks


def getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tp, delay, nodeType, valueType):  # Actually NOT MEAN BUT SUM!!!!
    print('Extracting for ' + valueType + ':')
    numNodes = []
    meanValues = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        meanValues.append(getMeanValueTypeForServer(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, valueType))
    # print(meanValues)
    prePath = '../exports/extracted/' + valueType + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'_srv.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(meanValues)

def getNumPacketsServer(testName, nodeTypes, nodeSplits, tp, delay, nodeType, valueType): # valueType='txPk' or 'rxPkOk'
    print('Extracting for ' + valueType + ' numPackets:')
    numNodes = []
    meanValues = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        servDF = importDF(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, '')
        valuesDF = getFilteredDFtypeAndTSServer(servDF, valueType, nodeType)
        print('Num packets transmitted by the server: ' + str(len(valuesDF)))
        meanValues.append(len(valuesDF))
    print(meanValues)
    prePath = '../exports/extracted/' + valueType + 'NumPackets/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'_srv.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(meanValues)

# getNumPacketsServer('singleAppStressTest_FileDownload2-5MB',  ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0,x,0,0] for x in range(1,41)], 10000, 1, 'serverFDO', 'txPk')

def calculateThrougputPerSecondDirection(df, direction, nodeType, nodeNum):
    dirDF = getFilteredDFtypeAndTS(df, direction[1], nodeType, nodeNum)
    dirDF = dirDF.rename(columns={str(dirDF.columns[0]) : "ts", str(dirDF.columns[1]) : "bytes"})
    nodeIdent = makeSNI(nodeType, nodeNum)
    tB = [0,1] # time bounds for calculation
    colName = direction[0] + ' Throughput ' + nodeIdent
    tpDirDF = pandas.DataFrame(columns=[colName])
    # print(math.ceil(dirDF.iloc[-1,0]))
    while tB[1] <= math.ceil(dirDF.iloc[-1,0]):
        if DEBUG: print(tB, end =" -> Throughput: ")
        throughput = dirDF.loc[(dirDF['ts'] > tB[0]) & (dirDF['ts'] <= tB[1])]["bytes"].sum()
        tpDirDF = tpDirDF.append({colName : throughput*8/1000}, ignore_index=True)
        if DEBUG: print(throughput*8/1000, end=" kbps\n")
        tB = [x+1 for x in tB]
    return tpDirDF

def extractNodeThroughputDirection(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, direction):
    print('TP ' + direction[0], end=' - ')
    nodeDF = importDF(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum)
    return calculateThrougputPerSecondDirection(nodeDF, direction, nodeType, nodeNum)

def extractAllNodeThroughputDirection(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, direction):
    allTPsDF = pandas.DataFrame()
    for i in range(nodeSplit[nodeTypes.index(nodeType)]):
        allTPsDF = allTPsDF.append(extractNodeThroughputDirection(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, i, direction))
    print(allTPsDF)

def getMeanTPsAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, direction):
    if direction == downlink:
        valueType = 'rxPkOk'
    elif direction == uplink:
        valueType = 'txPk'
    df = extractValuesTypeForAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, valueType)
    bytesDF = filterDFType(df, 'Val')
    # tsDF = filterDFType(df, 'TS')
    # maxTime = max(tsDF.max().tolist())
    maxTime = 15
    if nodeType == 'hostVIP':
        maxTime = 50 # VoIP
    elif nodeType == 'hostSSH':
        maxTime = 15 # SSH
        # maxTime = 20 # SSH_crossTraffic
    elif nodeType == 'hostVID':
        maxTime = 200 # Video, file download, live video
    elif nodeType == 'hostFDO':
        maxTime = 200 # Video, file download, live video
    bytesList = []
    print('maxTime: ' + str(maxTime), end='; ')
    for i in range(nodeSplit[nodeTypes.index(nodeType)]):
        sumBytes = sum(bytesDF.iloc[:,i].dropna().tolist())
        bytesList.append(sumBytes)
        # print(bytesList)
    sumBytes = sum(bytesList)
    sumKbits = sumBytes * 8 / 1000
    meanTP = sumKbits / maxTime
    print('Mean Throughput (kbps) = sumBytes / maxTime = ' +str(sumBytes) + ' / ' + str(maxTime) + ' = ' + str(meanTP))
    return meanTP

def getMeanTPSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, direction):
    if direction == downlink:
        valueType = 'rxPkOk'
    elif direction == uplink:
        valueType = 'txPk'
    df = extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType)
    bytesDF = filterDFType(df, 'Val')
    maxTime = 15
    if nodeType == 'hostVIP':
        maxTime = 50 # VoIP
    elif nodeType == 'hostSSH':
        maxTime = 15 # SSH
        # maxTime = 20 # SSH_crossTraffic
    elif nodeType == 'hostVID':
        maxTime = 200 # Video, file download, live video
    elif nodeType == 'hostFDO':
        maxTime = 200 # Video, file download, live video
    bytesList = bytesDF.iloc[:,0].dropna().tolist()
    print('maxTime: ' + str(maxTime), end='; ')
    sumBytes = sum(bytesList)
    sumKbits = sumBytes * 8 / 1000
    meanTP = sumKbits / maxTime
    print('Mean Throughput (kbps) = sumBytes / maxTime = ' +str(sumBytes) + ' / ' + str(maxTime) + ' = ' + str(meanTP))
    return meanTP

def getMeanValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType):
    df = extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType)
    valueDF = filterDFType(df, 'Val')
    if len(valueDF.iloc[:,0].tolist()) > 0:
        meanValue = statistics.mean(valueDF.iloc[:,0].tolist())
    else:
        meanValue = -1
    print('Mean ' + valueType + ' = ' + str(meanValue))
    return meanValue

def getMeanTPandMeanE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType):
    meanTPs = []
    meanE2EDs = []
    for nodeNum in range(numCLI):
        meanTPs.append(getMeanTPSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, downlink))
        meanE2EDs.append(getMeanValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, 'endToEndDelay'))
    print(meanTPs)
    print(meanE2EDs)
    return meanTPs, meanE2EDs

def getMeanTPandMeanE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplit, tps, delay, nodeType):
    meanTPs = []
    meanE2EDs = []

    sumNodes = 0
    for tp in tps:
        numCLI = sum(nodeSplit)
        TPs, E2EDs = getMeanTPandMeanE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType)
        meanTPs.extend(TPs)
        meanE2EDs.extend(E2EDs)
        sumNodes += numCLI

    
    # print(len(meanTPs))
    # print(len(meanE2EDs))
    # print(sumNodes)
    prePath = '../exports/extracted/lsMeanTPMeanE2ED/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(tps)
        fw.writerow(meanTPs)
        fw.writerow(meanE2EDs)

# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH')
# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP')
# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_VoIP_corrected', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [x for x in range(5,56)], 100, 'hostVIP')
# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO')

getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppLSTest_VoIP_corrected', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400,410,420,430,440,450,460,470,480,490,500,510,520,530,540,550], 100, 'hostVIP')


def getMeanRTTValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum)
    df = df.shift(periods=-1, axis='columns')
    valueDF = filterDFType(df, valueType).dropna()
    resList = []
    for col in valueDF:
        resList.extend(valueDF[col].tolist())
    print(resList)
    if len(resList) > 0:
        meanValue = statistics.mean(resList)
    else:
        meanValue = -1
    print('Mean ' + valueType + ' = ' + str(meanValue))
    return meanValue

def getMeanTPandMeanRTTforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType):
    meanTPs = []
    meanE2EDs = []
    for nodeNum in range(numCLI):
        meanTPs.append(getMeanTPSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, downlink))
        meanE2EDs.append(getMeanRTTValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, 'rtt'))
    print(meanTPs)
    print(meanE2EDs)
    return meanTPs, meanE2EDs

def getMeanTPandMeanRTTforEachNodeExpScenario(testName, nodeTypes, nodeSplit, tps, delay, nodeType):
    meanTPs = []
    meanE2EDs = []

    sumNodes = 0
    for tp in tps:
        numCLI = sum(nodeSplit)
        TPs, E2EDs = getMeanTPandMeanRTTforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType)
        meanTPs.extend(TPs)
        meanE2EDs.extend(E2EDs)
        sumNodes += numCLI

    
    # print(len(meanTPs))
    # print(len(meanE2EDs))
    # print(sumNodes)
    prePath = '../exports/extracted/lsMeanTPMeanRTT/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(tps)
        fw.writerow(meanTPs)
        fw.writerow(meanE2EDs)

# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH')
# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP')
# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO')

# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_VideoLongV2', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520, 540, 560, 580, 600, 620, 640, 660, 680, 700, 720, 740, 760, 780, 800, 820, 840, 860, 880, 900, 920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080, 1100, 1120, 1140, 1160, 1180, 1200, 1220, 1240, 1260, 1280, 1300, 1320, 1340, 1360, 1380, 1400, 1420, 1440, 1460, 1480, 1500, 1520, 1540, 1560, 1580, 1600, 1620, 1640, 1660, 1680, 1700, 1720, 1740, 1760, 1780, 1800, 1820, 1840, 1860, 1880, 1900, 1920, 1940, 1960, 1980, 2000, 2020, 2040, 2060, 2080, 2100, 2120, 2140, 2160, 2180, 2200, 2220, 2240, 2260, 2280, 2300, 2320, 2340, 2360, 2380, 2400, 2420, 2440, 2460, 2480, 2500, 2520, 2540, 2560, 2580, 2600, 2620, 2640, 2660, 2680, 2700, 2720, 2740, 2760, 2780, 2800, 2820, 2840, 2860, 2880, 2900, 2920, 2940, 2960, 2980, 3000, 3020, 3040, 3060, 3080, 3100, 3120, 3140, 3160, 3180, 3200, 3220, 3240, 3260, 3280, 3300, 3320, 3340, 3360, 3380, 3400, 3420, 3440, 3460, 3480, 3500, 3520, 3540, 3560, 3580, 3600, 3620, 3640, 3660, 3680, 3700, 3720, 3740, 3760, 3780, 3800, 3820, 3840, 3860, 3880, 3900, 3920, 3940, 3960, 3980, 4000, 4020, 4040, 4060, 4080, 4100, 4120, 4140, 4160, 4180, 4200, 4220, 4240, 4260, 4280, 4300, 4320, 4340, 4360, 4380, 4400, 4420, 4440, 4460, 4480, 4500, 4520, 4540, 4560, 4580, 4600], 100, 'hostVID')
# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_LiveVideoClientV2', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520, 540, 560, 580, 600, 620, 640, 660, 680, 700, 720, 740, 760, 780, 800, 820, 840, 860, 880, 900, 920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080, 1100, 1120, 1140, 1160, 1180, 1200, 1220, 1240, 1260, 1280, 1300, 1320, 1340, 1360, 1380, 1400, 1420, 1440, 1460, 1480, 1500, 1520, 1540, 1560, 1580, 1600, 1620, 1640, 1660, 1680, 1700, 1720, 1740, 1760, 1780, 1800, 1820, 1840, 1860, 1880, 1900, 1920, 1940, 1960, 1980, 2000, 2020, 2040, 2060, 2080, 2100, 2120, 2140, 2160, 2180, 2200, 2220, 2240, 2260, 2280, 2300, 2320, 2340, 2360, 2380, 2400, 2420, 2440, 2460, 2480, 2500, 2520, 2540, 2560, 2580, 2600, 2620, 2640, 2660, 2680, 2700, 2720, 2740, 2760, 2780, 2800, 2820, 2840, 2860, 2880, 2900, 2920, 2940, 2960, 2980, 3000, 3020, 3040, 3060, 3080, 3100, 3120, 3140, 3160, 3180, 3200, 3220, 3240, 3260, 3280, 3300, 3320, 3340, 3360, 3380, 3400, 3420, 3440, 3460, 3480, 3500, 3520, 3540, 3560, 3580, 3600, 3620, 3640, 3660, 3680, 3700, 3720, 3740, 3760, 3780, 3800, 3820, 3840, 3860, 3880, 3900, 3920, 3940, 3960, 3980, 4000, 4020, 4040, 4060, 4080, 4100, 4120, 4140, 4160, 4180, 4200, 4220, 4240, 4260, 4280, 4300, 4320, 4340, 4360, 4380, 4400, 4420, 4440, 4460, 4480, 4500, 4520, 4540, 4560, 4580, 4600], 100, 'hostVID')
# getMeanTPandMeanRTTforEachNodeExpScenario('singleAppLSTest_FileDownloadV3', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520, 540, 560, 580, 600, 620, 640, 660, 680, 700, 720, 740, 760, 780, 800, 820, 840, 860, 880, 900, 920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080, 1100, 1120, 1140, 1160, 1180, 1200, 1220, 1240, 1260, 1280, 1300, 1320, 1340, 1360, 1380, 1400, 1420, 1440, 1460, 1480, 1500, 1520, 1540, 1560, 1580, 1600, 1620, 1640, 1660, 1680, 1700, 1720, 1740, 1760, 1780, 1800, 1820, 1840, 1860, 1880, 1900, 1920, 1940, 1960, 1980, 2000, 2020, 2040, 2060, 2080, 2100, 2120, 2140, 2160, 2180, 2200, 2220, 2240, 2260, 2280, 2300, 2320, 2340, 2360, 2380, 2400, 2420, 2440, 2460, 2480, 2500, 2520, 2540, 2560, 2580, 2600, 2620, 2640, 2660, 2680, 2700, 2720, 2740, 2760, 2780, 2800, 2820, 2840, 2860, 2880, 2900, 2920, 2940, 2960, 2980, 3000, 3020, 3040, 3060, 3080, 3100, 3120, 3140, 3160, 3180, 3200, 3220, 3240, 3260, 3280, 3300, 3320, 3340, 3360, 3380, 3400, 3420, 3440, 3460, 3480, 3500, 3520, 3540, 3560, 3580, 3600, 3620, 3640, 3660, 3680, 3700, 3720, 3740, 3760, 3780, 3800, 3820, 3840, 3860, 3880, 3900, 3920, 3940, 3960, 3980, 4000, 4020, 4040, 4060, 4080, 4100, 4120, 4140, 4160, 4180, 4200, 4220, 4240, 4260, 4280, 4300, 4320, 4340, 4360, 4380, 4400, 4420, 4440, 4460, 4480, 4500, 4520, 4540, 4560, 4580, 4600], 100, 'hostFDO')


def getMedianValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType):
    df = extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType)
    valueDF = filterDFType(df, 'Val')
    meanValue = statistics.median(valueDF.iloc[:,0].tolist())
    print('Median ' + valueType + ' = ' + str(meanValue))
    return meanValue

def getMeanTPandMedianE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType):
    meanTPs = []
    meanE2EDs = []
    for nodeNum in range(numCLI):
        meanTPs.append(getMeanTPSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, downlink))
        meanE2EDs.append(getMedianValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, 'endToEndDelay'))
    # print(meanTPs)
    # print(meanE2EDs)
    return meanTPs, meanE2EDs

def getMeanTPandMedianE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplit, tps, delay, nodeType):
    meanTPs = []
    meanE2EDs = []

    sumNodes = 0
    for tp in tps:
        numCLI = sum(nodeSplit)
        TPs, E2EDs = getMeanTPandMedianE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType)
        meanTPs.extend(TPs)
        meanE2EDs.extend(E2EDs)
        sumNodes += numCLI

    
    # print(meanTPs)
    # print(meanE2EDs)
    # print(sumNodes)
    prePath = '../exports/extracted/lsEachNodeMeanTPMedianE2ED/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(tps)
        fw.writerow(meanTPs)
        fw.writerow(meanE2EDs)

# getMeanTPandMedianE2EDforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH')
# getMeanTPandMedianE2EDforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP')
# getMeanTPandMedianE2EDforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMedianE2EDforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMedianE2EDforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO')


def getMaxValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType):
    df = extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType)
    valueDF = filterDFType(df, 'Val')
    meanValue = max(valueDF.iloc[:,0].tolist())
    print('Max ' + valueType + ' = ' + str(meanValue))
    return meanValue

def getMeanTPandMaxE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType):
    meanTPs = []
    meanE2EDs = []
    for nodeNum in range(numCLI):
        meanTPs.append(getMeanTPSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, downlink))
        meanE2EDs.append(getMaxValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, 'endToEndDelay'))
    # print(meanTPs)
    # print(meanE2EDs)
    return meanTPs, meanE2EDs

def getMeanTPandMaxE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplit, tps, delay, nodeType):
    meanTPs = []
    meanE2EDs = []

    sumNodes = 0
    for tp in tps:
        numCLI = sum(nodeSplit)
        TPs, E2EDs = getMeanTPandMaxE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType)
        meanTPs.extend(TPs)
        meanE2EDs.extend(E2EDs)
        sumNodes += numCLI

    
    # print(len(meanTPs))
    # print(len(meanE2EDs))
    # print(sumNodes)
    prePath = '../exports/extracted/lsEachNodeMeanTPMaxE2ED/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(tps)
        fw.writerow(meanTPs)
        fw.writerow(meanE2EDs)

# getMeanTPandMaxE2EDforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH')
# getMeanTPandMaxE2EDforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP')
# getMeanTPandMaxE2EDforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMaxE2EDforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID')
# getMeanTPandMaxE2EDforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO')


def getXPercentileValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType, percentile):
    df = extractValuesTypeForNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, valueType)
    valueDF = filterDFType(df, 'Val')
    valueList = valueDF.iloc[:,0].tolist()
    sortedList = sorted(valueList)
    # print(sortedList)
    index = (percentile/100) * len(sortedList)
    index = round(index)
    print(str(percentile) + 'th Percentile ' + valueType + ' = ' + str(sortedList[index]))
    return sortedList[index]

def getMeanTPandXPercentileE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, percentile):
    meanTPs = []
    meanE2EDs = []
    for nodeNum in range(numCLI):
        meanTPs.append(getMeanTPSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, downlink))
        meanE2EDs.append(getXPercentileValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum, 'endToEndDelay', percentile))
    # print(meanTPs)
    # print(meanE2EDs)
    return meanTPs, meanE2EDs

def getMeanTPandXPercentileE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplit, tps, delay, nodeType, percentile):
    meanTPs = []
    meanE2EDs = []

    sumNodes = 0
    for tp in tps:
        numCLI = sum(nodeSplit)
        TPs, E2EDs = getMeanTPandXPercentileE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, percentile)
        meanTPs.extend(TPs)
        meanE2EDs.extend(E2EDs)
        sumNodes += numCLI

    
    # print(len(meanTPs))
    # print(len(meanE2EDs))
    # print(sumNodes)
    prePath = '../exports/extracted/eachNodeMeanTP' + str(percentile) + 'percentileE2ED/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(tps)
        fw.writerow(meanTPs)
        fw.writerow(meanE2EDs)

# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH', 97)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP', 97)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID', 97)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID', 97)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO', 97)


# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH', 95)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP', 95)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID', 95)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID', 95)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO', 95)


# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200], 100, 'hostSSH', 90)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], 100, 'hostVIP', 90)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID', 90)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostVID', 90)
# getMeanTPandXPercentileE2EDforEachNodeExpScenario('singleAppLSTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000,3100,3200,3300,3400,3500,3600,3700,3800,3900,4000,4100,4200,4300,4400,4500,4600,4700,4800,4900,5000,5100,5200,5300,5400,5500,5600,5700,5800,5900,6000], 100, 'hostFDO', 90)

# getMeanTPandMeanE2EDforEachNodeExpScenario('singleAppStressTest_SSH_smallLink', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0,0,x,0] for x in [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400]], 800, 1, 'hostSSH')

def getMeanTPsForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, direction):
    print('Extracting mean TPs for ' + direction[0] + ':')
    meanValues = []
    for delay in delays:
        meanValues.append(getMeanTPsAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, direction))
    # print(meanValues)
    prePath = '../exports/extracted/throughput' + direction[0] + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(delays)
        fw.writerow(meanValues)

def getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tp, delay, nodeType, direction):
    print('Extracting mean TPs for ' + direction[0] + ':')
    meanValues = []
    numNodes = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        meanValues.append(getMeanTPsAllNodes(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, direction))
    # print(meanValues)
    prePath = '../exports/extracted/throughput' + direction[0] + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(meanValues)

def extractJitterSumNumCli(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, nodeNum)
    diffSum = 0
    numComp = 0
    e2edDF = getFilteredDFtypeAndTS(df, 'endToEndDelay', nodeType, nodeNum)
    e2edList = e2edDF.iloc[:,1].tolist()
    for i in range(len(e2edList)-1):
        diff = abs(e2edList[i+1] - e2edList[i])
        diffSum += diff
        numComp += 1
    # print(testName + ' client ' + str(nodeNum) + ' has a Jitter of: ' + str(diffSum/numComp))
    return diffSum, numComp

# extractJitterSumNumCli('singleAppStressTest_FileDownload2-5MB', 10, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,10,0,0], 10000, 1, 'hostFDO', 5)

def getJitterForStressTest(testName, nodeTypes, nodeSplits, tp, delay, nodeType):
    jitterVals = []
    numNodes = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        diffSumTR = 0
        numCompTR = 0
        for i in range(nodeSplit[nodeTypes.index(nodeType)]):
            diffSum, numComp = extractJitterSumNumCli(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, i)
            diffSumTR += diffSum
            numCompTR += numComp
        jitterVals.append(diffSumTR/numCompTR)
    
    print(jitterVals)

    prePath = '../exports/extracted/endToEndDelayJitter/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(jitterVals)

def getMeanValueTypeForRouter(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, valueType):
    valuesDF = extractValuesTypeForNode(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, '', valueType)
    # print(valuesDF)
    allValues = []
    filteredDF = filterDFType(valuesDF, 'Val ' + makeSNI(nodeType, ''))
    allValues.extend(filteredDF.iloc[:,0].dropna().tolist())
    # print(filteredDF)
    # print(allValues)
    if len(allValues) > 0:
        meanValue = statistics.mean(allValues)
        stdDevValue = statistics.stdev(allValues)
        confidence = 0.95
        n = len(allValues)
        std_err = sem(allValues)
        ci95hVal = std_err * t.ppf((1 + confidence) / 2, n - 1)
        minVal = min(allValues)
        maxVal = max(allValues)
        numVal = len(allValues)
    else:
        meanValue = -1
        stdDevValue = 0
        ci95hVal = 0
        minVal = -1
        maxVal = -1
        numVal = 0
    print(meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal)
    return meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal

def getInfoRouter(testName, nodeTypes, nodeSplits, tp, delay, routerName, interfaceIdent, dataType):
    print('Extracting from ' + routerName + ' for ' + dataType + ':')
    numNodes = []
    meanValues = []
    stdDevValues = []
    ci95hValues = []
    minValues = []
    maxValues = []
    numValues = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal = getMeanValueTypeForRouter(testName, numNode, nodeTypes, nodeSplit, tp, delay, routerName, dataType)
        meanValues.append(meanValue)
        stdDevValues.append(stdDevValue)
        ci95hValues.append(ci95hVal)
        minValues.append(minVal)
        maxValues.append(maxVal)
        numValues.append(numVal)
    # print(meanValues)
    prePath = '../exports/extracted/' + dataType + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(meanValues)
        fw.writerow(stdDevValues)
        fw.writerow(ci95hValues)
        fw.writerow(minValues)
        fw.writerow(maxValues)



def getMeanQLandMeanE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, numRouters):
    meanQLs = []
    meanE2EDs = []
    for nodeNum in range(numRouters):
        meanQLs.append(getMeanValueSingleNode(testName, numCLI, nodeTypes, nodeSplit, tp, delay, 'router', nodeNum, 'queueLength'))
        meanValue, stdDevValue, ci95hVal, minVal, maxVal, numVal = getMeanValueTypeForAllNodes(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, 'endToEndDelay')
        meanE2EDs.append(meanValue)
    # print(meanQLs)
    # print(meanE2EDs)
    return meanQLs, meanE2EDs

def getMeanQLandMeanE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType):
    meanQLs = []
    meanE2EDs = []

    sumNodes = 0
    for nodeSplit in nodeSplits:
        numCLI = sum(nodeSplit)
        QLs, E2EDs = getMeanQLandMeanE2EDforEachNodeRun(testName, numCLI, nodeTypes, nodeSplit, tp, delay, nodeType, 2)
        meanQLs.extend(QLs)
        meanE2EDs.extend(E2EDs)
        sumNodes += numCLI

    
    # print(len(meanTPs))
    # print(len(meanE2EDs))
    # print(sumNodes)
    prePath = '../exports/extracted/eachNodeMeanQLandMeanE2ED/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(meanQLs)
        fw.writerow(meanE2EDs)


# getJitterForStressTest('singleAppStressTest_FileDownload2-5MB',  ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0,x,0,0] for x in range(1,41)], 10000, 1, 'hostFDO')


def getAllValuesForDelayTest(testName, nodeTypes, nodeSplit, tp, delays, nodeType):
    numCLI = sum(nodeSplit)
    valueTypes = []
    if nodeType == 'hostVIP':
        valueTypes = ['mos', 'endToEndDelay', 'packetLossRate', 'playoutDelay', 'playoutLossRate', 'taildropLossRate']
        getMeanTPsForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, downlink)
    if nodeType == 'hostSSH':
        valueTypes = ['numActiveSessions', 'packetSent', 'packetReceived', 'endToEndDelay', 'roundTripTime', 'mosValue']
        getMeanTPsForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, downlink)
        getMeanTPsForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, uplink)
    if nodeType == 'hostVID':
        valueTypes = ['DASHBufferLength', 'DASHVideoBitrate', 'numActiveSessions', 'DASHReceivedBytes', 'DASHmosScore', 'DASHliveDelay']
        getMeanTPsForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, downlink)
        getMeanTPsForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, uplink)
    for valueType in valueTypes:
        getMeanValuesTypeForDelayExperiment(testName, numCLI, nodeTypes, nodeSplit, tp, delays, nodeType, valueType)
    
def getAllValuesForStressTest(testName, nodeTypes, numNodes, tps, delay, nodeType):
    valueTypes = []
    nodeSplits = []
    if nodeType == 'hostVIP':
        valueTypes = ['mos', 'endToEndDelay', 'packetLossRate', 'playoutDelay', 'playoutLossRate', 'taildropLossRate']
        nodeSplits = [[0,0,0,x] for x in numNodes]
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tps, delay, nodeType, downlink)
    
    if nodeType == 'hostSSH':
        valueTypes = ['numActiveSessions', 'packetSent', 'packetReceived', 'endToEndDelay', 'roundTripTime', 'mosValue']
        nodeSplits = [[0,0,x,0] for x in numNodes]
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tps, delay, nodeType, downlink)
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tps, delay, nodeType, uplink)

        getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tps, delay, 'serverSSH', 'dupAcks')
        getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tps, delay, 'serverSSH', 'numRtos')
        getNumPacketsServer(testName, nodeTypes, nodeSplits, tps, delay, 'serverSSH', 'txPk')
        # getInfoRouter(testName, nodeTypes, nodeSplits, tps, delay, 'router1', 'ppp[0]','queueLength')
        
    
    if nodeType == 'hostFDO':
        valueTypes = ['endToEndDelay', 'mosScore', 'downloadTime', 'averageDownloadThroughput']
        nodeSplits = [[0,x,0,0] for x in numNodes]
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tps, delay, nodeType, downlink)
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tps, delay, nodeType, uplink)

        getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tps, delay, 'serverFDO', 'dupAcks')
        getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tps, delay, 'serverFDO', 'numRtos')
        getNumPacketsServer(testName, nodeTypes, nodeSplits, tps, delay, 'serverFDO', 'txPk')

    if nodeType == 'hostVID':
        valueTypes = ['DASHBufferLength', 'DASHVideoBitrate', 'numActiveSessions', 'DASHReceivedBytes', 'DASHmosScore', 'DASHVideoResolution', 'DASHliveDelay', 'DASHEstimatedBitrate', 'endToEndDelay']

        nodeSplits = [[x,0,0,0] for x in numNodes]
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tp, delay, nodeType, downlink)
        getMeanTPsForStressExperiment(testName, nodeTypes, nodeSplits, tp, delay, nodeType, uplink)

        getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tp, delay, 'serverVID', 'dupAcks')
        getMeanValuesTypeForStressExperimentServer(testName, nodeTypes, nodeSplits, tp, delay, 'serverVID', 'numRtos')
        getNumPacketsServer(testName, nodeTypes, nodeSplits, tp, delay, 'serverVID', 'txPk')

    getMeanTPandMeanE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType)
    getMeanTPandMaxE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType)
    getMeanTPandMedianE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType)
    getMeanTPandXPercentileE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType, 97)
    getMeanTPandXPercentileE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType, 95)
    getMeanTPandXPercentileE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType, 90)

    getMeanQLandMeanE2EDforEachNodeExpScenario(testName, nodeTypes, nodeSplits, tp, delay, nodeType)

    # valueTypes = ['endToEndDelay']
    getJitterForStressTest(testName, nodeTypes, nodeSplits, tp, delay, nodeType)
    for valueType in valueTypes:
        getMeanValuesTypeForStressExperiment(testName, nodeTypes, nodeSplits, tp, delay, nodeType, valueType)

# getAllValuesForDelayTest('singleAppDelayTest_VoIP_1cli', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 10000, [1,50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000], 'hostVIP')
# getAllValuesForDelayTest('singleAppDelayTest_VoIP_10cli', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,10], 10000, [1,50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000], 'hostVIP')
# getAllValuesForDelayTest('singleAppDelayTest_VoIP_50cli', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,50], 10000, [1,50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000], 'hostVIP')
# getAllValuesForDelayTest('singleAppDelayTest_SSH_1cli', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 10000, [1,50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000], 'hostSSH')
# getAllValuesForDelayTest('singleAppDelayTest_SSH_10cli', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,10,0], 10000, [1,50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000], 'hostSSH')
# getAllValuesForStressTest('singleAppStressTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,5,10,15,20,25,30,35,40,45,50,55,60], 10000, 1, 'hostVIP')
# getAllValuesForStressTest('singleAppStressTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300], 10000, 1, 'hostSSH')
# getAllValuesForStressTest('singleAppStressTest_FileDownload', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40], 10000, 1, 'hostFDO')
# getAllValuesForStressTest('singleAppStressTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150], 10000, 1, 'hostVID')
# getAllValuesForStressTest('singleAppStressTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150], 10000, 1, 'hostVID')
# getAllValuesForStressTest('singleAppStressTest_LiveVideo', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150], 10000, 1, 'hostVID')
# getAllValuesForDelayTest('singleAppDelayTest_LiveVideo', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 10000, [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400,410,420,430,440,450,460,470,480,490,500,550,600,650,700,750,800,850,900,950,1000], 'hostVID')
# getAllValuesForDelayTest('singleAppDelayTest_LiveVideoV2', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 10000, [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400,410,420,430,440,450,460,470,480,490,500,550,600,650,700,750,800,850,900,950,1000], 'hostVID')
# getAllValuesForDelayTest('singleAppDelayTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 10000, [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400,410,420,430,440,450,460,470,480,490,500,550,600,650,700,750,800,850,900,950,1000], 'hostVID')


# getAllValuesForStressTest('singleAppStressTest_VoIP', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,5,10,15,20,21,22,23,24,25,26,27,28,29,30,35,40,45,50,55,60], 10000, 1, 'hostVIP')
# getAllValuesForStressTest('singleAppStressTest_VoIP_oneTenth', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [x for x in range(1,7)], 1000, 1, 'hostVIP')
# getAllValuesForStressTest('singleAppStressTest_VoIP_oneTenth', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [x for x in range(1,16)], 1000, 1, 'hostVIP')
# getAllValuesForStressTest('singleAppStressTest_SSH_smallLink', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330,340,350,360,370,380,390,400], 800, 1, 'hostSSH')
# getAllValuesForStressTest('singleAppStressTest_FileDownload2-5MB', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40], 10000, 1, 'hostFDO')
# getAllValuesForStressTest('singleAppStressTest_VideoV2', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150], 10000, 1, 'hostVID')
# getAllValuesForStressTest('singleAppStressTest_NewLiveVideoClient', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150], 10000, 1, 'hostVID')


def getMeanTPsForSSHCrossTrafficStressExperiment(testName, nodeTypes, nodeSplits, tp, delay, nodeType, direction):
    print('Extracting mean TPs for ' + direction[0] + ':')
    meanValues = []
    numNodes = []
    for nodeSplit in nodeSplits:
        numNode = sum(nodeSplit)
        numNodes.append(numNode)
        bytesSSH = getMeanTPsAllNodes(testName, numNode, nodeTypes, nodeSplit, tp, delay, nodeType, direction) * 20
        bytesFDO = getMeanTPsAllNodes(testName, numNode, nodeTypes, nodeSplit, tp, delay, 'hostVIP', direction) * 20
        meanTP = (bytesSSH + bytesFDO) / 20
        meanValues.append(meanTP)
    
    print(meanValues)
    prePath = '../exports/extracted/throughput' + direction[0] + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    with open(prePath+makeFullScenarioName(testName, numNodes, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(numNodes)
        fw.writerow(meanValues)

# getMeanTPsForSSHCrossTrafficStressExperiment('singleAppStressTest_SSH_crossTraffic', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0,0,10,x] for x in range(1,61)], 10000, 1, 'hostSSH', downlink)
# getMeanValuesTypeForStressExperiment('singleAppStressTest_SSH_crossTraffic', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0,0,10,x] for x in range(1,61)], 10000, 1, 'hostSSH', 'endToEndDelay')