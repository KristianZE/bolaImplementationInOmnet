import pandas
import csv
import statistics
# from termcolor import colored
import sys
import os

maxSimTime = 280
DEBUG = 0

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']

def makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit):
    scenName = str(testName) + '_' + str(numCLI)
    for nodeType,numNodesType in zip(nodeTypes, nodeSplit):
        scenName += '_' + nodeType.replace('host','') + str(numNodesType)
    return scenName
    # return str(testName) + '_' + str(numCLI) + '_VID' + str(nodeSplit[0]) + '_FDO' + str(nodeSplit[1]) + '_SSH' + str(nodeSplit[2]) + '_VIP' + str(nodeSplit[3])

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
    fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/vectors/' + fullScenarioExportName + '_' + makeNodeIdentifier(nodeType, nodeNum) + '_vec.csv'
    print("Importing: " + fileToRead)
    # Read the CSV
    return pandas.read_csv(fileToRead)

def filterDFType(df, filterType):
    return df.filter(like=filterType)

def getFilteredDFtypeAndTS(df, filterType):
    filteredDF = filterDFType(df, filterType)
    if len(filteredDF.columns):
        colNoTS = df.columns.get_loc(df.filter(filteredDF).columns[0])
        return df.iloc[:,[colNoTS,colNoTS+1]].dropna()
    else:
        return pandas.DataFrame(columns=['ts', 'tp'])

def calculateThrougputPerSecondDirection(df, direction, nodeIdent):
    dirDF = getFilteredDFtypeAndTS(df, direction[1])
    dirDF = dirDF.rename(columns={str(dirDF.columns[0]) : "ts", str(dirDF.columns[1]) : "bytes"})
    tB = [0,1] # time bounds for calculation
    colName = direction[0] + ' Throughput ' + nodeIdent
    tpDirDF = pandas.DataFrame(columns=[colName])
    while tB[1] <= maxSimTime:
        if DEBUG: print(tB, end =" -> Throughput: ")
        throughput = dirDF.loc[(dirDF['ts'] > tB[0]) & (dirDF['ts'] <= tB[1])]["bytes"].sum()
        tpDirDF = tpDirDF.append({colName : throughput*8/1000}, ignore_index=True)
        if DEBUG: print(throughput*8/1000, end=" kbps\n")
        tB = [x+1 for x in tB]
    return tpDirDF

def extractNodeThroughputDirection(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, direction):
    print('TP ' + direction[0], end=' - ')
    nodeDF = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    nodeIdent = makeNodeIdentifier(nodeType, nodeNum)
    return calculateThrougputPerSecondDirection(nodeDF, direction, nodeIdent)

def extractAllThroughputsDirection(testName, numCLI, nodeTypes, nodeSplit, nodeTypesToExtract, numSlices, direction):
    # Prepare result dataframe
    tpDFall = pandas.DataFrame()
    # Add link tps
    for i in range(numSlices):
        tpDFall = pandas.concat([tpDFall,extractNodeThroughputDirection(testName, numCLI, nodeTypes, nodeSplit, 'resAllocLink', i ,direction)],axis=1,ignore_index=False)
    # Add nodes tps
    for nodeType,numNodes in zip(nodeTypesToExtract,nodeSplit):
        for nodeNum in range(numNodes):
            tpDFall = pandas.concat([tpDFall,extractNodeThroughputDirection(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum ,direction)],axis=1,ignore_index=False)
    if not os.path.exists('../exports/extracted/throughputs/'):
        os.makedirs('../exports/extracted/throughputs/')
    # Export to csv
    tpDFall.to_csv(path_or_buf='../exports/extracted/throughputs/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'_'+direction[0]+'.csv')

def extractNodeDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, dataType, dataIdent):
    print(dataIdent, end=' - ')
    nodeDF = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    dataTypeDF = getFilteredDFtypeAndTS(nodeDF, dataType)
    nodeIdent = makeNodeIdentifier(nodeType, nodeNum)
    dataTypeDF = dataTypeDF.rename(columns={str(dataTypeDF.columns[0]) : nodeIdent + " " + dataIdent + " TS", str(dataTypeDF.columns[1]) : nodeIdent + " " + dataIdent + " Val"})
    return dataTypeDF

def extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, nodeTypesToExtract, dataType, dataIdent, folderName):
    dfAll = pandas.DataFrame()
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToExtract:
            for nodeNum in range(numNodes):
                dfAll = pandas.concat([dfAll,extractNodeDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, dataType, dataIdent)],axis=1,ignore_index=False)

    prePath = '../exports/extracted/'+str(folderName)+'/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    dfAll.to_csv(path_or_buf=prePath + makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit) + '.csv')

def extractRTO(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum):
    print('RTO', end=' - ')
    nodeDF = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    filteredDF = filterDFType(nodeDF, 'RTO ')
    rtos = []
    colTSList = nodeDF.filter(filteredDF).columns
    for col in colTSList:
        colNoTS = nodeDF.columns.get_loc(col)
        rtos.extend(nodeDF.iloc[:,colNoTS+1].dropna().tolist())
    filteredDFnumSes = filterDFType(nodeDF, 'advertised window')
    numSession = len(list(filteredDFnumSes))
    print('Total Number of sessions at the SSH server: ' + str(numSession))
    filteredDF2 = filterDFType(nodeDF, 'RTOs ')
    print(filteredDF2)
    numSessionWithRTO = len(list(filteredDF2))
    print('Number of sessions at the SSH server where at least one retransmission timeout occured: ' + str(numSessionWithRTO))

    with open('../exports/extracted/rto/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(rtos)
        fw.writerow([numSession])
        fw.writerow([numSessionWithRTO])

def getRTTValuesSingleNode(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, valueType):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum)
    df = df.shift(periods=-1, axis='columns')
    valueDF = filterDFType(df, valueType).dropna()
    resList = []
    for col in valueDF:
        resList.extend(valueDF[col].tolist())
    return resList

def extractRTTValues(testName, numCLI, nodeTypes, nodeSplit, nodeTypesToExtract):
    dfAll = pandas.DataFrame()
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToExtract:
            for nodeNum in range(numNodes):
                clientDf = pandas.DataFrame({makeNodeIdentifier(nodeType, nodeNum) + " rtt Val" : getRTTValuesSingleNode(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, 'rtt')})
                dfAll = pandas.concat([dfAll,clientDf], axis=1)
                # dfAll[makeNodeIdentifier(nodeType, nodeNum) + " rtt Val"] = getRTTValuesSingleNode(testName, numCLI, nodeTypes, nodeSplit, nodeType, nodeNum, 'rtt')
    prePath = '../exports/extracted/rtt/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    dfAll.to_csv(path_or_buf=prePath + makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit) + '.csv')

def extractAll(testName, nodeTypes, nodeSplit, numSlices):
    numCLI = sum(nodeSplit)
    # Extract throughputs for all nodes
    extractAllThroughputsDirection(testName, numCLI, nodeTypes, nodeSplit, nodeTypes, numSlices, downlink)
    extractAllThroughputsDirection(testName, numCLI, nodeTypes, nodeSplit, nodeTypes, numSlices, uplink)

    # # Extract all mos values
    extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, nodeTypes, 'mos', 'Mos', 'mos')
    extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, nodeTypes, 'endToEndDelay', 'E2ED', 'endToEndDelay')

    # Extract mean client rtt for all node types except VoIP
    extractRTTValues(testName, numCLI, nodeTypes, nodeSplit, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH'])

    # Extract additional data for SSH application
    # if 'hostSSH' in nodeTypes: 
    #     extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostSSH'], 'roundTripTime', 'RTT', 'rtt')
        # extractRTO(testName, numCLI, nodeTypes, nodeSplit, 'serverSSH', -1)
    
    # Extract additional data for VoIP application
    if 'hostVIP' in nodeTypes:
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVIP'], 'endToEndDelay', 'E2ED', 'e2ed')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVIP'], 'packetLossRate', 'PkLR', 'pklr')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVIP'], 'playoutDelay', 'PlDel', 'pldel')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVIP'], 'playoutLossRate', 'PlLR', 'pllr')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVIP'], 'taildropLossRate', 'TDLR', 'tdlr')
    
    if 'hostcVIP' in nodeTypes:
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostcVIP'], 'endToEndDelay', 'E2ED', 'e2ed')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostcVIP'], 'packetLossRate', 'PkLR', 'pklr')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostcVIP'], 'playoutDelay', 'PlDel', 'pldel')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostcVIP'], 'playoutLossRate', 'PlLR', 'pllr')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostcVIP'], 'taildropLossRate', 'TDLR', 'tdlr')

    if 'hostLVD' in nodeTypes:
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostLVD'], 'DASHliveDelay', 'DLVD', 'dlvd')
    
    if 'hostVID' in nodeTypes and 'hostLVD' in nodeTypes:
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVID', 'hostLVD'], 'DASHBufferLength', 'DABL', 'dabl')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVID', 'hostLVD'], 'DASHVideoBitrate', 'DAVB', 'davb')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVID', 'hostLVD'], 'DASHVideoResolution', 'DAVR', 'davr')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVID', 'hostLVD'], 'DASHmosScore', 'DAMS', 'dams')
        extractAllDataTypeToDF(testName, numCLI, nodeTypes, nodeSplit, ['hostVID', 'hostLVD'], 'DASHEstimatedBitrate', 'DAEB', 'daeb')

# extractAll('baselineTest', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [10,10,10,10,10], 1)
# extractAll('baselineTest', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,20,20,20,20], 1)
# extractAll('baselineTest', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [30,30,30,30,30], 1)
# extractAll('baselineTest', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [40,40,40,40,40], 1)
# extractAll('baselineTest', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,50,50,50,50], 1)

# extractAll('initialTestHTB_105mbps', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [1,1,1,1,1], 1)
# extractAll('initialTestHTB_105mbps_bla', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [1,1,1,1,1], 1)

# extractAll('test', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [36,36,36,50,37], 1)
# extractAll('test2', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [33,32,33,50,33], 1)


# extractAll('baselineTestNS_2sli_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sli_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)

# extractAll('baselineTestNS_2sliSingle_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sliSingle_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)

# extractAll('baselineTestNS_2sliSingle2sli_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sliSingle2sli_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)

# extractAll('baselineTestNS_2sliDouble_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sliDouble_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)


# extractAll('baselineTestNS_5sli', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)

# extractAll('baselineTestNS_5sliSingle', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)

# extractAll('baselineTestNS_5sliSingle5sli', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)

# extractAll('baselineTestNS_5sliDouble', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)

# extractAll('baselineTestTemp', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [10,10,10,10,10], 1)

# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDW_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNSPrioQueue_SingleDW_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)
# extractAll('baselineTestNSPrioQueue_SingleDW_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)
# extractAll('baselineTestNSPrioQueueAF_2sliSingle2sliNBS_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNSPrioQueueAF_SingleNBS_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)

# extractAll('baselineTestNSPrioQueue_SingleDWR_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)
# extractAll('baselineTestNSPrioQueue_SingleDWR_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)

# extractAll('baselineTestNSPrioQueueDES2_2sliSingle2sli_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)
# extractAll('baselineTestNSPrioQueueDES2_2sliSingle2sli_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)
# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDWR2_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)
# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDWR2_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)


# extractAll('baselineTestNSPrioQueueAF_Single_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)
# extractAll('baselineTestNSPrioQueueAF_SingleLBS_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)
# extractAll('baselineTestNSPrioQueueAF_Single50_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)

# extractAll('baselineTestNSPrioQueueDES4_2sliSingle2sli_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)
# extractAll('baselineTestNSPrioQueueDES4_2sliSingle2sli_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)

# extractAll('baselineTestNSPrioQueue_SingleDWRLQ_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)
# extractAll('baselineTestNSPrioQueue_SingleDWRLQ_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1)

# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDWRLQ_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)
# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDWRLQ_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)

# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDWRLQPD_LVD-DES', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)
# extractAll('baselineTestNSPrioQueue_2sliSingle2sliDWRLQPD_LVD-BWS', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 0)

# extractAll('baselineTestNS_5sli_AlgoTest1', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)
# extractAll('baselineTestNS_2sli_LVD-DES_AlgoTest3', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sli_LVD-BWS_AlgoTest3', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)

# extractAll('optimizationAlgoFairness1_5sli_0alpha_SSH100VIP75VID20LVD5FDO50_sSSH3sVIP44sVID14sLVD2sFDO37_fairness_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,5,50,100,75], 5)
# extractAll('optimizationAlgoFairness1_5sli_5alpha_SSH100VIP20VID75LVD5FDO50_sSSH1sVIP12sVID51sLVD6sFDO30_fairness_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75,5,50,100,20], 5)
# extractAll('optimizationAlgoFairness1_5sli_10alpha_SSH100VIP20VID75LVD5FDO50_sSSH1sVIP12sVID51sLVD6sFDO30_fairness_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75,5,50,100,20], 5)
# extractAll('optimizationAlgoFairness1_5sli_0alpha_SSH100VIP20VID50LVD5FDO75_sSSH4sVIP12sVID35sLVD6sFDO43_min_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,5,75,100,20], 5)
# extractAll('optimizationAlgoFairness1_5sli_5alpha_SSH100VIP50VID20LVD5FDO75_sSSH1sVIP29sVID15sLVD6sFDO49_min_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,5,75,100,50], 5)
# extractAll('optimizationAlgoFairness1_5sli_10alpha_SSH100VIP50VID20LVD5FDO75_sSSH1sVIP29sVID15sLVD6sFDO49_min_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,5,75,100,50], 5)
# extractAll('optimizationAlgoFairness1_5sli_0alpha_SSH100VIP75VID20LVD5FDO50_sSSH3sVIP44sVID14sLVD2sFDO37_mean_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,5,50,100,75], 5)
# extractAll('optimizationAlgoFairness1_5sli_5alpha_SSH100VIP75VID50LVD5FDO20_sSSH2sVIP44sVID34sLVD6sFDO14_mean_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,5,20,100,75], 5)
# extractAll('optimizationAlgoFairness1_5sli_10alpha_SSH100VIP75VID50LVD5FDO20_sSSH1sVIP44sVID34sLVD6sFDO15_mean_max', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,5,20,100,75], 5)
# extractAll('optimizationAlgoFairness1_5sli_0alpha_SSH50VIP75VID100LVD5FDO20_sSSH7sVIP45sVID20sLVD7sFDO21_fairness_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [100,5,20,50,75], 5)
# extractAll('optimizationAlgoFairness1_5sli_5alpha_SSH20VIP100VID75LVD5FDO50_sSSH1sVIP58sVID37sLVD3sFDO1_fairness_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75,5,50,20,100], 5)
# extractAll('optimizationAlgoFairness1_5sli_10alpha_SSH50VIP100VID5LVD20FDO75_sSSH1sVIP36sVID20sLVD20sFDO23_fairness_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [5,20,75,50,100], 5)
# extractAll('optimizationAlgoFairness1_5sli_0alpha_SSH5VIP75VID100LVD20FDO50_sSSH1sVIP44sVID48sLVD6sFDO1_min_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [100,20,50,5,75], 5)
# extractAll('optimizationAlgoFairness1_5sli_5alpha_SSH20VIP100VID75LVD5FDO50_sSSH1sVIP58sVID37sLVD3sFDO1_min_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75,5,50,20,100], 5)
# extractAll('optimizationAlgoFairness1_5sli_10alpha_SSH5VIP50VID75LVD100FDO20_sSSH18sVIP28sVID29sLVD22sFDO3_min_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75,100,20,5,50], 5)
# extractAll('optimizationAlgoFairness1_5sli_0alpha_SSH5VIP100VID50LVD75FDO20_sSSH1sVIP1sVID50sLVD22sFDO26_mean_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,75,20,5,100], 5)
# extractAll('optimizationAlgoFairness1_5sli_5alpha_SSH5VIP100VID75LVD20FDO50_sSSH25sVIP26sVID32sLVD6sFDO11_mean_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75,20,50,5,100], 5)
# extractAll('optimizationAlgoFairness1_5sli_10alpha_SSH5VIP75VID50LVD100FDO20_sSSH15sVIP42sVID18sLVD22sFDO3_mean_min', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50,100,20,5,75], 5)

# extractAll('baselineTestVCD_SSH100VIP75VID20LVD5FDO50', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20, 5, 50, 100, 75], 1)
# extractAll('baselineTestVCD_SSH100VIP20VID75LVD5FDO50', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 5, 50, 100, 20], 1)
# extractAll('baselineTestVCD_SSH50VIP75VID100LVD5FDO20', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [100, 5, 20, 50, 75], 1)
# extractAll('baselineTestVCD_SSH20VIP100VID75LVD5FDO50', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 5, 50, 20, 100], 1)
# extractAll('baselineTestVCD_SSH50VIP100VID5LVD20FDO75', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [5, 20, 75, 50, 100], 1)
# extractAll('baselineTestVCD_SSH100VIP20VID50LVD5FDO75', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 5, 75, 100, 20], 1)
# extractAll('baselineTestVCD_SSH100VIP50VID20LVD5FDO75', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20, 5, 75, 100, 50], 1)
# extractAll('baselineTestVCD_SSH5VIP75VID100LVD20FDO50', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [100, 20, 50, 5, 75], 1)
# extractAll('baselineTestVCD_SSH5VIP50VID75LVD100FDO20', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 100, 20, 5, 50], 1)
# extractAll('baselineTestVCD_SSH100VIP75VID50LVD5FDO20', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 5, 20, 100, 75], 1)
# extractAll('baselineTestVCD_SSH5VIP100VID50LVD75FDO20', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 75, 20, 5, 100], 1)
# extractAll('baselineTestVCD_SSH5VIP100VID75LVD20FDO50', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 20, 50, 5, 100], 1)
# extractAll('baselineTestVCD_SSH5VIP75VID50LVD100FDO20', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 100, 20, 5, 75], 1)

# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_0alpha_SSH100VIP75VID20LVD5FDO50_sDES46sBWS54_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20, 5, 50, 100, 75], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_5alpha_SSH100VIP20VID75LVD5FDO50_sDES14sBWS86_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 5, 50, 100, 20], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_10alpha_SSH100VIP20VID75LVD5FDO50_sDES14sBWS86_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 5, 50, 100, 20], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_0alpha_SSH50VIP75VID100LVD5FDO20_sDES46sBWS54_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [100, 5, 20, 50, 75], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_5alpha_SSH20VIP100VID75LVD5FDO50_sDES58sBWS42_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 5, 50, 20, 100], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_10alpha_SSH50VIP100VID5LVD20FDO75_sDES59sBWS41_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [5, 20, 75, 50, 100], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_0alpha_SSH100VIP20VID50LVD5FDO75_sDES15sBWS85_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 5, 75, 100, 20], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_5alpha_SSH100VIP50VID20LVD5FDO75_sDES31sBWS69_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20, 5, 75, 100, 50], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_10alpha_SSH100VIP50VID20LVD5FDO75_sDES31sBWS69_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20, 5, 75, 100, 50], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_0alpha_SSH5VIP75VID100LVD20FDO50_sDES47sBWS53_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [100, 20, 50, 5, 75], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_5alpha_SSH20VIP100VID75LVD5FDO50_sDES58sBWS42_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 5, 50, 20, 100], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_10alpha_SSH5VIP50VID75LVD100FDO20_sDES18sBWS82_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 100, 20, 5, 50], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_0alpha_SSH100VIP75VID20LVD5FDO50_sDES46sBWS54_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20, 5, 50, 100, 75], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_5alpha_SSH100VIP75VID50LVD5FDO20_sDES46sBWS54_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 5, 20, 100, 75], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_10alpha_SSH100VIP75VID50LVD5FDO20_sDES46sBWS54_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 5, 20, 100, 75], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_0alpha_SSH5VIP100VID50LVD75FDO20_sDES60sBWS40_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 75, 20, 5, 100], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_5alpha_SSH5VIP100VID75LVD20FDO50_sDES57sBWS43_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [75, 20, 50, 5, 100], 2)
# extractAll('optimizationAlgoFairness1_2sli_LVD-BWS_10alpha_SSH5VIP75VID50LVD100FDO20_sDES43sBWS57_ndf_ndf', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50, 100, 20, 5, 75], 2)


# extractAll('baselineTestNS_5sli_AlgoTest_alpha00', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)
# extractAll('baselineTestNS_5sli_AlgoTest_alpha05', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)
# extractAll('baselineTestNS_5sli_AlgoTest_alpha10', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 5)

# extractAll('baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha00', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)
# extractAll('baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha10', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 2)


if __name__ == "__main__":
    name = sys.argv[3]
    numVID = int(name.split('VID')[1].split('_LVD')[0])
    numLVD = int(name.split('LVD')[1].split('_FDO')[0])
    numFDO = int(name.split('FDO')[1].split('_SSH')[0])
    numSSH = int(name.split('SSH')[1].split('_VIP')[0])
    numVIP = int(name.split('_VIP')[1].split('_cVIP')[0])
    numcVIP = int(name.split('cVIP')[1])
    extractAll(sys.argv[1], ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostcVIP'], [numVID, numLVD, numFDO, numSSH, numVIP,numcVIP], int(sys.argv[2]))