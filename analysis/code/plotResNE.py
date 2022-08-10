import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
import math
import statistics
from scipy import stats
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(os.path.dirname(currentdir))
print(parentdir)
sys.path.insert(0,parentdir) 
from algorithm import algorithm as algo

font = {'weight' : 'normal',
        'size'   : 40}

matplotlib.rc('font', **font)
matplotlib.rc('lines', linewidth=2.0)
matplotlib.rc('lines', markersize=8)

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']
maxSimTime = 280

globalCounter = 0

def partialCDFBegin(numSubplots):
    fig, ax = plt.subplots(numSubplots, figsize=(16,12*numSubplots))
    return fig, ax

def partialCDFPlotData(fig, ax, data, label, lineType, lineColor):
    sorted_data = np.sort(data)
    linspaced = np.linspace(0, 1, len(data), endpoint=True)
    ax.plot(sorted_data, linspaced, lineType, label=label, color=lineColor)

def partialCDFPlotDataNoColor(fig, ax, data, label, lineType):
    sorted_data = np.sort(data)
    linspaced = np.linspace(0, 1, len(data), endpoint=True)
    ax.plot(sorted_data, linspaced, lineType, label=label)

def partialCDFEnd(fig, ax, title, xLabel, outPath):
    try:
        iterator = iter(ax)
    except TypeError:
        ax.set_ylim(0,1.1)
        ax.grid(True)
    else:
        for axs in ax:
            axs.set_ylim(0,1.1)
            axs.grid(True)
    plt.legend()
    if title != '':
        plt.title(title)
    plt.xlabel(xLabel)
    plt.ylabel("CDF")
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    plt.close('all')

def partialCDFEndPNG(fig, ax, title, xLabel, outPath):
    try:
        iterator = iter(ax)
    except TypeError:
        ax.set_ylim(0,1.1)
        ax.grid(True)
    else:
        for axs in ax:
            axs.set_ylim(0,1.1)
            axs.grid(True)
    plt.legend()
    if title != '':
        plt.title(title)
    plt.xlabel(xLabel)
    plt.ylabel("CDF")
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

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

def importDF(testName, numCLI, nodeTypes, nodeSplit, dataType):
    # File that will be read
    fullScenarioName = makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)
    file_to_read = '../exports/extracted/' + str(dataType) + '/' + fullScenarioName + '.csv'
    print("Results from run: " + file_to_read)
    # Read the CSV
    return pd.read_csv(file_to_read)

def importDFextended(testName, numCLI, nodeTypes, nodeSplit, dataType, extension):
    # File that will be read
    fullScenarioName = makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)
    file_to_read = '../exports/extracted/' + str(dataType) + '/' + fullScenarioName + extension + '.csv'
    print("Results from run: " + file_to_read)
    # Read the CSV
    return pd.read_csv(file_to_read)

def filterDFType(df, filterType):
    return df.filter(like=filterType)

def chooseName(dataName):
    if dataName == 'hostVID':
        return 'VoD'
    elif dataName == 'hostFDO':
        return 'Download'
    elif dataName == 'hostSSH':
        return 'SSH'
    elif dataName == 'hostVIP':
        return 'VoIP'
    elif dataName == 'hostcVIP':
        return 'Crit VoIP'
    elif dataName == 'hostLVD':
        return 'Live Video'
    elif dataName == '2link0':
        return 'Bandwidth Slice'
    elif dataName == '2link1':
        return 'Delay Slice'
    elif dataName == '1link0':
        return 'Link'
    elif dataName == '3link0':
        return 'Bandwidth Slice'
    elif dataName == '3link1':
        return 'Delay Slice'
    elif dataName == '3link2':
        return 'Return Link'

colormap = plt.get_cmap('Set1').colors
print(colormap)
colorMapping = {
    'VID' : colormap[0],
    'LVD' : colormap[1], 
    'FDO' : colormap[2], 
    'SSH' : colormap[3], 
    'VIP' : colormap[4],
    'cVIP' : colormap[5],
    'all' : colormap[6]
}
def chooseColor(dataName):
    # if dataName == 'hostVID':
    #     return 'y'
    # elif dataName == 'hostFDO':
    #     return 'g'
    # elif dataName == 'hostSSH':
    #     return 'r'
    # elif dataName == 'hostVIP':
    #     return 'b'
    # if dataName == 'hostLVD':
    #     return 'm'
    if dataName == 'hostVID':
        return colorMapping['VID']
    elif dataName == 'hostFDO':
        return colorMapping['FDO']
    elif dataName == 'hostSSH':
        return colorMapping['SSH']
    elif dataName == 'hostVIP':
        return colorMapping['VIP']
    elif dataName == 'hostcVIP':
        return colorMapping['cVIP']
    if dataName == 'hostLVD':
        return colorMapping['LVD']
    elif dataName == '2link0':
        return 'c'
    elif dataName == '2link1':
        return 'm'
    elif dataName == '1link0':
        return 'k'
    elif dataName == '3link0':
        return 'c'
    elif dataName == '3link1':
        return 'm'
    elif dataName == '3link2':
        return 'k'

niceDataTypeName = {
    'DABL' : 'Buffer Length [s]',
    'DAMS' : 'MOS',
    'DAVB' : 'Requested Video Bitrate [kbps]',
    'DAVR' : 'Requested Video Resolution [p]',
    'DLVD' : 'Delay To Live Video Edge [s]',
    'Mos' : 'MOS',
    'RTT' : 'Round Trip Time [s]',
    'DAEB' : 'Estimated Bitrate [kbps]',
    'E2ED' : 'End to End Delay [s]',
    'PkLR' : 'Packet Loss Rate',
    'PlDel' : 'Playout Delay [s]',
    'PlLR' : 'Playout Loss Rate',
    'TDLR' : 'Taildrop Loss Rate',
    'rtt' : 'Round Trip Time [s]'
}

def plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, dataIdent, folderName, nodeTypesToPlot):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, folderName)
    fig, ax1 = partialCDFBegin(1)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                data = df[colName].dropna().tolist()
                if len(data) > 0:
                    tempValue.append(statistics.mean(data))
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                partialCDFPlotData(fig, ax1, tempValue, chooseName(nodeType), '-o', chooseColor(nodeType))
    if dataIdent == 'Mos':
        ax1.set_xlim(0.95,5.05)
    # else:
    #     ax1.set_xlim(0,1.01*maxValue)
    partialCDFEnd(fig,ax1,'', 'Mean Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_meanCdf' + dataIdent + str(nodeTypesToPlot) + '.pdf')
    partialCDFEndPNG(fig,ax1,'', 'Mean Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_meanCdf' + dataIdent + str(nodeTypesToPlot) + '.png')

minMaxQoE = {'hostFDO' : {'minMOS' : 1.0,
                            'maxMOS' : 5.0},
                'hostSSH' : {'minMOS' : 1.0,
                            'maxMOS' : 4.292851753999999},
                'hostVID' : {'minMOS' : 1.0,
                            'maxMOS' : 4.394885531954699},
                'hostVIP' : {'minMOS' : 1.0,
                            'maxMOS' : 4.5},
                'hostcVIP' : {'minMOS' : 1.0,
                            'maxMOS' : 4.5},
                'hostLVD' : {'minMOS' : 1.0,
                            'maxMOS' : 4.585703050898499}}

def normalizeQoE(cliType, mos):
    retMos = (mos - minMaxQoE[cliType]['minMOS'])*((5.0 - 1.0)/(minMaxQoE[cliType]['maxMOS'] - minMaxQoE[cliType]['minMOS'])) + 1.0
    return max(1.0, min(retMos, 5.0))

def getMeanDataTypeAppClass(testName, numCLI, nodeTypes, nodeSplit, dataIdent, folderName, nodeTypesToPlot, sliceConfig):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, folderName)
    dfRtt = importDF(testName, numCLI, nodeTypes, nodeSplit, 'rtt')
    dfE2ed = importDF(testName, numCLI, nodeTypes, nodeSplit, 'endToEndDelay')
    meanMosFromExperiment = {}
    mosFairnessFromExperiment = {}
    minMosValFromExperiment = {}
    maxMosValFromExperiment = {}
    allData = []
    allDataRtt = []
    allDataE2ed = []

    initBandAss = {}
    for sli in list(sliceConfig):
        initBandAss[sli] = 100/len(list(sliceConfig))
    algoRes = algo.algorithm(sliceConfig, initBandAss, 1000, 0.33, 0.33, 1000, 50, False)
    # print(algoRes)

    algoMeanMos = {}
    algoMeanDelay = {}
    for sli in list(algoRes[8]):
        for cli in list(algoRes[8][sli]):
            # print(sli, cli,algoRes[8][sli][cli])
            algoMeanMos[cli] = algoRes[8][sli][cli]
            algoMeanDelay[cli] = algoRes[7][sli][cli]

    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            tempValueRtt = []
            tempValueE2ed = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                data = df[colName].dropna().tolist()
                if len(data) > 0:
                    # normalizedQoEdata = [normalizeQoE(nodeType, x) for x in data]
                    tempValue.append(normalizeQoE(nodeType,statistics.mean(data)))
                    allData.append(normalizeQoE(nodeType,statistics.mean(data)))
                if nodeType != 'hostVIP':
                    colName = makeNodeIdentifier(nodeType, nodeNum) + " rtt Val"
                    data = dfRtt[colName].dropna().tolist()
                    if len(data) > 0:
                        tempValueRtt.append(statistics.mean(data))
                        allDataRtt.append(statistics.mean(data))
                else:
                    colName = makeNodeIdentifier(nodeType, nodeNum) + " E2ED Val"
                    data = dfE2ed[colName].dropna().tolist()
                    if len(data) > 0:
                        tempValueE2ed.append(statistics.mean(data))
                        allDataE2ed.append(statistics.mean(data))

            # print(tempValue)
            print(nodeType + ':')
            meanMosFromExperiment[nodeType] = statistics.mean(tempValue)
            print('\tMean ' + dataIdent + ' of clients: ' + str(statistics.mean(tempValue)) + '; vs. predicted mean: ' + str(algoMeanMos[nodeType]))
            minMosValFromExperiment[nodeType] = min(tempValue)
            print('\tMin ' + dataIdent + ' of clients: ' + str(min(tempValue)))
            maxMosValFromExperiment[nodeType] = max(tempValue)
            print('\tMax ' + dataIdent + ' of clients: ' + str(max(tempValue)))
            mosFairnessFromExperiment[nodeType] = 1 - (2*statistics.stdev(tempValue))/(5.0-1.0)
            print('\tFairness ' + dataIdent + ' of clients: ' + str(1 - (2*statistics.stdev(tempValue))/(5.0-1.0)))
            if nodeType != 'hostVIP':
                print('\tMean delay of clients: ' + str(statistics.mean([x*1000/2 for x in tempValueRtt])) + '; vs. predicted mean: ' + str(algoMeanDelay[nodeType]))
                print('\tMin delay of clients: ' + str(min(tempValueRtt)*1000/2))
                print('\tMax delay of clients: ' + str(max(tempValueRtt)*1000/2))
            else:
                print('\tMean delay of clients: ' + str(statistics.mean([x*1000 for x in tempValueE2ed])) + '; vs. predicted mean: ' + str(algoMeanDelay[nodeType]))
                print('\tMin delay of clients: ' + str(min(tempValueE2ed)*1000))
                print('\tMax delay of clients: ' + str(max(tempValueE2ed)*1000))
            # allData.extend(tempValue)
    print(len(allData))
    print('Mean ' + dataIdent + ' of all clients: ' + str(statistics.mean(allData)) + '; vs. predicted mean: ' + str(algoRes[4]))
    print('Min ' + dataIdent + ' of all clients: ' + str(min(allData)) + '; vs. predicted min: ' + str(algoRes[2][2]))
    print('Max ' + dataIdent + ' of all clients: ' + str(max(allData)) + '; vs. predicted max: ' + str(algoRes[3][2]))
    print('Fairness ' + dataIdent + ' of all clients: ' + str(1 - (2*statistics.stdev(allData))/(5.0-1.0)) + '; vs. predicted fairness: ' + str(algoRes[5]))

    



# getMeanDataTypeAppClass('baselineTestNS_5sli_AlgoTest1', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}})
# getMeanDataTypeAppClass('baselineTestNS_5sli_AlgoTest2', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}})
# getMeanDataTypeAppClass('baselineTestNS_2sli_LVD-DES_AlgoTest1', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceDel' : {'hostSSH' : 50, 'hostLVD' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostFDO' : 50}})
# getMeanDataTypeAppClass('baselineTestNS_2sli_LVD-BWS_AlgoTest1', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}})

# getMeanDataTypeAppClass('baselineTestNS_5sli_AlgoTest3', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}})
# getMeanDataTypeAppClass('baselineTest', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceSSH' : {'hostSSH' : 50, 'hostVIP' : 50, 'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}})
# getMeanDataTypeAppClass('baselineTestNS_2sli_LVD-DES_AlgoTest3', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceDel' : {'hostSSH' : 50, 'hostLVD' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostFDO' : 50}})
# getMeanDataTypeAppClass('baselineTestNS_2sli_LVD-BWS_AlgoTest3', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], {'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}})

def plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, dataIdent, folderName, nodeTypesToPlot):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, folderName)
    fig, ax1 = partialCDFBegin(1)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                tempValue.extend(df[colName].dropna().tolist())
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                partialCDFPlotData(fig, ax1, tempValue, chooseName(nodeType), '-o', chooseColor(nodeType))
    if dataIdent == 'Mos':
        ax1.set_xlim(0.95,5.05)
    else:
        ax1.set_xlim(0,1.01*maxValue)
    partialCDFEnd(fig,ax1,'', 'Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdf' + dataIdent + str(nodeTypesToPlot) + '.pdf')
    partialCDFEndPNG(fig,ax1,'', 'Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdf' + dataIdent + str(nodeTypesToPlot) + '.png')

def plotUtilityCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, nodeTypesToPlot):
    folderName = 'mos'
    dataIdent = 'Mos'
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, folderName)
    fig, ax1 = partialCDFBegin(1)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                tempValue.extend([normalizeQoE(nodeType, x) for x in df[colName].dropna().tolist()])
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                partialCDFPlotData(fig, ax1, tempValue, chooseName(nodeType), '-o', chooseColor(nodeType))
    if dataIdent == 'Mos':
        ax1.set_xlim(0.95,5.05)
    # else:
    #     ax1.set_xlim(0,1.01*maxValue)
    prePath = '../exports/plots/baseSlicingComps/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    plt.legend(loc='upper left')
    partialCDFEnd(fig,ax1,'', 'Utility', prePath+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'_'+str(globalCounter)+'_cdf' + dataIdent + str(nodeTypesToPlot) + '.pdf')
    partialCDFEndPNG(fig,ax1,'', 'Utility', prePath+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'_'+str(globalCounter)+'_cdf' + dataIdent + str(nodeTypesToPlot) + '.png')

# plotUtilityCdfAllApps('baselineTest', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'])
# plotUtilityCdfAllApps('baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'])
# plotUtilityCdfAllApps('baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'])
# plotMosBaseSliComp('baselineTest', 'baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 'baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'hostVID')

niceTestName = {
    'baselineTest' : 'Baseline',
    'baselineTestTemp' : 'Temporary Baseline',
    'baselineTestNS_2sli_LVD-DES' : '2 Slices, Live in Delay, No Algorithm',
    # 'baselineTestNS_2sli_LVD-BWS' : '2 Slices, Live Video in Bandwidth Slice',
    'baselineTestNS_2sli_LVD-BWS' : '2 Slices, Live in Bandwidth, No Algorithm',
    'baselineTestNS_2sliSingle_LVD-DES' : '2 Slices + Single Link, Live Video in Delay Slice',
    'baselineTestNS_2sliSingle_LVD-BWS' : '2 Slices + Single Link, Live Video in Bandwidth Slice',
    'baselineTestNS_2sliSingle2sli_LVD-DES' : '2 Slices + Single Link + 2 Slices, Live Video in Delay Slice',
    'baselineTestNS_2sliSingle2sli_LVD-BWS' : '2 Slices + Single Link + 2 Slices, Live Video in Bandwidth Slice',
    'baselineTestNS_2sliDouble_LVD-DES' : 'Directional 2 Slices + Single Link, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliNBS_LVD-DES' : '2 Same Prio Queues: 2 + Single + 2 Links, Live Vid in Delay Slice',
    'baselineTestNSPrioQueueAF_2sliSingle2sliNBS_LVD-DES' : '2 Different Prio Queues: 2 + Single + 2 Links, Live Vid in Delay Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliNBS_LVD-BWS' : '2 Same Prio Queues: 2 + Single + 2 Links, Live Vid in Bandwidth Slice',
    'baselineTestNSPrioQueueAF_2sliSingle2sliNBS_LVD-BWS' : '2 Different Prio Queues: 2 + Single + 2 Links, Live Vid in Bandwidth Slice',
    'baselineTestNS_2sliDouble_LVD-BWS' : 'Directional 2 Slices + Single Link, Live Video in Bandwidth Slice',
    'baselineTestNS_5sli' : '5 Slices',
    'baselineTestNS_5sliSingle' : '5 Slices + Single Link',
    'baselineTestNS_5sliSingle5sli' : '5 Slices + Single Link + 5 Slices',
    'baselineTestNS_5sliDouble' : 'Directional 5 Slices + Single Link',
    'baselineTestNSPrioQueueAF_Single_LVD-DES' : 'Single Link with priority queue for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueueAF_SingleLBS_LVD-DES' : 'Single Link with priority queue for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueueAF_Single50_LVD-DES' : 'Single Link with priority queue for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueueAF_SingleNBS_LVD-DES' : 'Single Link with priority queue for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_SingleDW_LVD-BWS' : 'Single Link with WRR sheduler, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueue_SingleDWR_LVD-DES' : 'Single Link with WRR sheduler, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_SingleDWR_LVD-BWS' : 'Single Link with WRR sheduler, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueue_SingleDWRLQ_LVD-DES' : 'One Link + WRR sheduler LQ, Live Vid in Delay Sli',
    'baselineTestNSPrioQueue_SingleDWRLQ_LVD-BWS' : 'One Link + WRR sheduler LQ, Live Vid in Bandwidth Sli',
    'baselineTestNSPrioQueueDES_2sliSingle2sli_LVD-DES' : '1 + 1 + 1 Links with Priority for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueueDES_2sliSingle2sli_LVD-BWS' : '1 + 1 + 1 Links with Priority for Delay Slice, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWR_LVD-DES' : '1 + 1 + 1 Links with Weighted Queues, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWR_LVD-BWS' : '1 + 1 + 1 Links with Weighted Queues, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueueDES2_2sliSingle2sli_LVD-DES' : '2 + 1 + 2 Links with Priority for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueueDES2_2sliSingle2sli_LVD-BWS' : '2 + 1 + 2 Links with Priority for Delay Slice, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueueDES4_2sliSingle2sli_LVD-DES' : '2 + 1 + 2 Links with 4x Priority for Delay Slice, Live Video in Delay Slice',
    'baselineTestNSPrioQueueDES4_2sliSingle2sli_LVD-BWS' : '2 + 1 + 2 Links with 4x Priority for Delay Slice, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWR2_LVD-DES' : '2 + 1 + 2 Links with Weighted Queues, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWR2_LVD-BWS' : '2 + 1 + 2 Links with Weighted Queues, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWRLQ_LVD-DES' : '2 + 1 + 2 Links with WRR, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWRLQ_LVD-BWS' : '2 + 1 + 2 Links with WRR, Live Video in Bandwidth Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWRLQPD_LVD-DES' : '2 + 1 + 2 Links WRR Delay Prio, Live Video in Delay Slice',
    'baselineTestNSPrioQueue_2sliSingle2sliDWRLQPD_LVD-BWS' : '2 + 1 + 2 Links WRR Delay Prio, Live Video in Bandwidth Slice',
    'baselineTestNS_5sli_AlgoTest1' : '5 Slices, Algorithm v0.1',
    'baselineTestNS_5sli_AlgoTest2' : '5 Slices, Algorithm v0.11',
    'baselineTestNS_5sli_AlgoTest3' : '5 Slices, Algorithm v0.12',
    'baselineTestNS_2sli_LVD-DES_AlgoTest1' : '2 Slices, Live in Delay, Algorithm v0.11',
    'baselineTestNS_2sli_LVD-BWS_AlgoTest1' : '2 Slices, Live in Bandwidth, Algorithm v0.11',
    'baselineTestNS_2sli_LVD-DES_AlgoTest3' : '2 Slices, Live in Delay, Algorithm v0.12',
    'baselineTestNS_2sli_LVD-BWS_AlgoTest3' : '2 Slices, Live in Bandwidth, Algorithm v0.12'
}



def plotMeanDataTypeCdfAllAppsComp(testNameMain, testNameSecondary, numCLI, nodeTypes, nodeSplit, dataIdent, folderName, nodeTypesToPlot):
    df = importDF(testNameMain, numCLI, nodeTypes, nodeSplit, folderName)
    df2 = importDF(testNameSecondary, numCLI, nodeTypes, nodeSplit, folderName)
    fig, ax = partialCDFBegin(2)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            tempValue2 = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                data = df[colName].dropna().tolist()
                data2 = df2[colName].dropna().tolist()
                if len(data) > 0:
                    tempValue.append(statistics.mean(data))
                if len(data2) > 0:
                    tempValue2.append(statistics.mean(data2))
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                if len(tempValue2) > 0:
                    if maxValue < max(tempValue2):
                        maxValue = max(tempValue2)
                partialCDFPlotData(fig, ax[0], tempValue, chooseName(nodeType), '-o', chooseColor(nodeType))
                partialCDFPlotData(fig, ax[1], tempValue2, chooseName(nodeType), '-o', chooseColor(nodeType))
    for axs in ax:
        if dataIdent == 'Mos':
            axs.set_xlim(0.95,5.05)
        else:
            axs.set_xlim(0,1.01*maxValue)
    ax[0].title.set_text(niceTestName[testNameMain])
    ax[1].title.set_text(niceTestName[testNameSecondary])
    partialCDFEnd(fig,ax,'', 'Mean Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testNameMain, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_meanCdf' + dataIdent + str(nodeTypesToPlot) + 'compWith' + str(testNameSecondary) + '.pdf')
    partialCDFEndPNG(fig,ax,'', 'Mean Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testNameMain, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_meanCdf' + dataIdent + str(nodeTypesToPlot) + 'compWith' + str(testNameSecondary) + '.png')

# plotMeanDataTypeCdfAllAppsComp('baselineTestNS_2sliSingle_LVD-DES', 'baselineTest', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'])

def plotDataTypeCdfAllAppsComp(testNameMain, testNameSecondary, numCLI, nodeTypes, nodeSplit, dataIdent, folderName, nodeTypesToPlot):
    df = importDF(testNameMain, numCLI, nodeTypes, nodeSplit, folderName)
    df2 = importDF(testNameSecondary, numCLI, nodeTypes, nodeSplit, folderName)
    fig, ax = partialCDFBegin(2)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            tempValue2 = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                tempValue.extend(df[colName].dropna().tolist())
                tempValue2.extend(df2[colName].dropna().tolist())
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                if len(tempValue2) > 0:
                    if maxValue < max(tempValue2):
                        maxValue = max(tempValue2)
                partialCDFPlotData(fig, ax[0], tempValue, chooseName(nodeType), '-o', chooseColor(nodeType))
                partialCDFPlotData(fig, ax[1], tempValue2, chooseName(nodeType), '-o', chooseColor(nodeType))
    if dataIdent == 'Mos':
        for axs in ax:
            axs.set_xlim(0.95,5.05)
    else:
        ax[0].set_xlim(0,1.01*maxValue)
        ax[1].set_xlim(0,1.01*maxValue)
    ax[0].title.set_text(niceTestName[testNameMain])
    ax[1].title.set_text(niceTestName[testNameSecondary])
    partialCDFEnd(fig,ax,'', 'Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testNameMain, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdf' + dataIdent + str(nodeTypesToPlot) + 'compWith' + str(testNameSecondary) + '.pdf')
    partialCDFEndPNG(fig,ax,'', 'Client ' + niceDataTypeName[dataIdent], '../exports/plots/'+makeFullScenarioName(testNameMain, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdf' + dataIdent + str(nodeTypesToPlot) + 'compWith' + str(testNameSecondary) + '.png')

def plotEstimatedChosenBitrateLVD(testName, numCLI, nodeTypes, nodeSplit, nodeTypesToPlot):
    df = importDF(testName, numCLI, nodeTypes, nodeSplit, 'daeb')
    df2 = importDF(testName, numCLI, nodeTypes, nodeSplit, 'davb')
    fig, ax = partialCDFBegin(1)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType in nodeTypesToPlot:
            tempValue = []
            tempValue2 = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " DAEB Val"
                colName2 = makeNodeIdentifier(nodeType, nodeNum) + " DAVB Val"
                tempValue.extend(df[colName].dropna().tolist())
                tempValue2.extend(df2[colName2].dropna().tolist())
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                if maxValue < max(tempValue2):
                    maxValue = max(tempValue2)
                partialCDFPlotData(fig, ax, tempValue, 'Estimated Bitrate', '-o', 'g')
                partialCDFPlotData(fig, ax, tempValue2, 'Chosen Video Bitrate', '-o', 'b')
    ax.set_xlim(0,1.01*maxValue)
    partialCDFEnd(fig,ax,'', 'Bitrate [kbps]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfDAEBDAVB'  + str(nodeTypesToPlot) + '.pdf')
    partialCDFEndPNG(fig,ax,'', 'Bitrate [kbps]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfDAEBDAVB'  + str(nodeTypesToPlot) + '.png')

# plotDataTypeCdfAllAppsComp('baselineTestNS_2sliSingle_LVD-DES', 'baselineTest', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'Mos', 'mos', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], 'PNG')

def plotTPdirection(testName, numCLI, nodeTypes, nodeSplit, numSlices, direction):
    df = importDFextended(testName, numCLI, nodeTypes, nodeSplit, 'throughputs', '_' + direction[0])
    fig, ax1 = plt.subplots(1, figsize=(16,12))
    times = range(1,maxSimTime+1,1)
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        tempDF = pd.DataFrame()
        for nodeNum in range(numNodes):
            colName = direction[0] + " Throughput " + makeNodeIdentifier(nodeType, nodeNum)
            tempDF = pd.concat([tempDF,df[colName]],axis=1,ignore_index=False)
        ax1.plot(times, [x/1000 for x in tempDF.sum(axis=1).tolist()], label=chooseName(nodeType), marker='o', ls='-', color=chooseColor(nodeType))
    for sliceNum in range(numSlices):
        linkDF = filterDFType(df, direction[0] + ' Throughput resAllocLink' + str(sliceNum))
        ax1.plot(times, [x/1000 for x in linkDF.sum(axis=1).tolist()], label=chooseName(str(numSlices)+'link'+str(sliceNum)), marker='o', ls='-', color=chooseColor(str(numSlices)+'link'+str(sliceNum)))
        # print(linkDF)
    ax1.set_ylabel(direction[0]+' Throughput [mbps]')
    ax1.set_xlabel('Simulation Time [s]')
    ax1.set_xlim(0,1.01*times[-1])
    # ax1.set_ylim(0,105)
    plt.legend()
    plt.grid(True)
    fig.savefig('../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_'+direction[0]+'Throughputs' + str(nodeTypes) + '.pdf', dpi=100, bbox_inches='tight')

def plotTPScdfDirection(testName, numCLI, nodeTypes, nodeSplit, numSlices, direction, cutoff):
    df = importDFextended(testName, numCLI, nodeTypes, nodeSplit, 'throughputs', '_' + direction[0])
    fig, ax1 = partialCDFBegin(1)
    maxTPS = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        tempTPSall = []
        for nodeNum in range(numNodes):
            colName = direction[0] + " Throughput " + makeNodeIdentifier(nodeType, nodeNum)
            tempTPSall.extend([x/1000 for x in df[colName].tolist()[:int(cutoff)+1]])
        if maxTPS < max(tempTPSall):
            maxTPS = max(tempTPSall)
        partialCDFPlotData(fig, ax1, tempTPSall, chooseName(nodeType), '-o', chooseColor(nodeType))

    # for sliceNum in range(numSlices):
    #     tempTPSslice = []
    #     colName = direction[0] + ' Throughput resAllocLink' + str(sliceNum)
    #     tempTPSslice.extend([x/1000 for x in df[colName].tolist()[:int(cutoff)+1]])
    #     partialCDFPlotData(fig, ax1, tempTPSslice, chooseName(str(numSlices)+'link'+str(sliceNum)), '-o', chooseColor(str(numSlices)+'link'+str(sliceNum)))
    #     if maxTPS < max(tempTPSslice):
    #         maxTPS = max(tempTPSslice)

    ax1.set_xlim(0,1.01*maxTPS)
    partialCDFEndPNG(fig,ax1,'', 'Throughput [mbps]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdf'+direction[0]+'ThroughputsCutoff'+ str(cutoff) + str(nodeTypes) + '.png')
    partialCDFEnd(fig,ax1,'', 'Throughput [mbps]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdf'+direction[0]+'ThroughputsCutoff'+ str(cutoff) + str(nodeTypes) + '.pdf')

def plotMeanTPScdfDirection(testName, numCLI, nodeTypes, nodeSplit, direction, cutoff):
    df = importDFextended(testName, numCLI, nodeTypes, nodeSplit, 'throughputs', '_' + direction[0])
    fig, ax1 = partialCDFBegin(1)
    maxTPS = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        tempTPSall = []
        for nodeNum in range(numNodes):
            colName = direction[0] + " Throughput " + makeNodeIdentifier(nodeType, nodeNum)
            tempTPSall.append(statistics.mean([x/1000 for x in df[colName].tolist()[:int(cutoff)+1]]))
        if maxTPS < max(tempTPSall):
            maxTPS = max(tempTPSall)
        partialCDFPlotData(fig, ax1, tempTPSall, chooseName(nodeType), '-o', chooseColor(nodeType))

    ax1.set_xlim(0,1.01*maxTPS)
    partialCDFEnd(fig,ax1,'', 'Mean Client Throughput [mbps]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfMean'+direction[0]+'ThroughputsCutoff'+ str(cutoff) + str(nodeTypes) + '.pdf')
    partialCDFEndPNG(fig,ax1,'', 'Mean Client Throughput [mbps]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfMean'+direction[0]+'ThroughputsCutoff'+ str(cutoff) + str(nodeTypes) + '.png')

def plotMeanTPScdfDirectionComp(testNameMain, testNameSecondary, numCLI, nodeTypes, nodeSplit, direction, cutoff):
    df = importDFextended(testNameMain, numCLI, nodeTypes, nodeSplit, 'throughputs', '_' + direction[0])
    df2 = importDFextended(testNameSecondary, numCLI, nodeTypes, nodeSplit, 'throughputs', '_' + direction[0])
    fig, ax = partialCDFBegin(2)
    maxTPS = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        tempTPSall = []
        tempTPSall2 = []
        for nodeNum in range(numNodes):
            colName = direction[0] + " Throughput " + makeNodeIdentifier(nodeType, nodeNum)
            tempTPSall.append(statistics.mean([x/1000 for x in df[colName].tolist()[:int(cutoff)+1]]))
            tempTPSall2.append(statistics.mean([x/1000 for x in df2[colName].tolist()[:int(cutoff)+1]]))
        if maxTPS < max(tempTPSall):
            maxTPS = max(tempTPSall)
        if maxTPS < max(tempTPSall2):
            maxTPS = max(tempTPSall2)
        partialCDFPlotData(fig, ax[0], tempTPSall, chooseName(nodeType), '-o', chooseColor(nodeType))
        partialCDFPlotData(fig, ax[1], tempTPSall2, chooseName(nodeType), '-o', chooseColor(nodeType))
    for axs in ax:
        axs.set_xlim(0,1.01*maxTPS)
    ax[0].title.set_text(niceTestName[testNameMain])
    ax[1].title.set_text(niceTestName[testNameSecondary])
    partialCDFEnd(fig,ax,'', 'Mean Client Throughput [mbps]', '../exports/plots/'+makeFullScenarioName(testNameMain, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfMean'+direction[0]+'ThroughputsCutoff'+ str(cutoff) + str(nodeTypes) + 'compWith' + str(testNameSecondary) + '.pdf')
    partialCDFEndPNG(fig,ax,'', 'Mean Client Throughput [mbps]', '../exports/plots/'+makeFullScenarioName(testNameMain, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfMean'+direction[0]+'ThroughputsCutoff'+ str(cutoff) + str(nodeTypes) + 'compWith' + str(testNameSecondary) + '.png')


def plotRTOcdf(testName, numCLI, nodeTypes, nodeSplit):
    rtos = []
    numSession = 0
    numSessionWithRTO = 0
    fullScenarioName = makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)
    file_to_read = '../exports/extracted/rto/' + fullScenarioName + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                rtos = row
            elif line_count == 1:
                numSession = row[0]
            elif line_count == 2:
                numSessionWithRTO = row[0]
            line_count += 1
    # print(rtos)
    print('Total Number of sessions at the SSH server: ' + str(numSession))
    print('Number of sessions at the SSH server where at least one retransmission timeout occured: ' + str(numSessionWithRTO))
    print('Percentage of sessions with a timeout: ' + str(numSessionWithRTO*100/numSession) + '%')
    fig, ax1 = partialCDFBegin(1)
    partialCDFPlotData(fig, ax1, rtos, 'SSH Server', '-o', chooseColor('hostSSH'))
    ax1.text(0.25,0.12, 'SSH server sessions - total: ' + str(int(numSession)), horizontalalignment='left', transform=ax1.transAxes)
    ax1.text(0.25,0.07, 'SSH server sessions - with timeout: ' + str(int(numSessionWithRTO)), horizontalalignment='left', transform=ax1.transAxes)
    ax1.text(0.25,0.02, 'Sessions with timeout: ' + str(round(numSessionWithRTO*100/numSession, 2)) + '%', horizontalalignment='left', transform=ax1.transAxes)
    partialCDFEnd(fig,ax1,'', 'RTO Value [s]', '../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)+'/'+str(globalCounter)+'_cdfRTO[\'serverSSH\'].pdf')

def plotSSHRTOcdfMultiTest(testNames, numCLIs, lineColors):
    fig, ax1 = partialCDFBegin(1)
    iterator = 0
    for testName in testNames:
        rtos = []
        numSession = 0
        numSessionWithRTO = 0
        fullScenarioName = str(testName) + '_' + str(numCLIs[iterator])
        file_to_read = '../exports/extracted/rto/' + fullScenarioName + '.csv'
        with open(file_to_read, mode='r') as readFile:
            csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    rtos = row
                elif line_count == 1:
                    numSession = row[0]
                elif line_count == 2:
                    numSessionWithRTO = row[0]
                line_count += 1
        # print(rtos)
        print('Total Number of sessions at the SSH server: ' + str(numSession))
        print('Number of sessions at the SSH server where at least one retransmission timeout occured: ' + str(numSessionWithRTO))
        print('Percentage of sessions with a timeout: ' + str(numSessionWithRTO*100/numSession) + '%')
        
        partialCDFPlotData(fig, ax1, rtos, testName, '-o', lineColors[iterator])
        ax1.text(0.25,0.02+iterator*0.05, testName + ' # Sessions: ' + str(int(numSession)) + '; With Timeout: ' + str(round(numSessionWithRTO*100/numSession, 2)) + '%', horizontalalignment='left', transform=ax1.transAxes, fontsize=20)
        iterator += 1
    partialCDFEndPNG(fig,ax1,'', 'RTO Value [s]', '../exports/plots/'+str(testNames)+'_sshRtoCDF.png')

def chooseColorNS(nodeSplit):
    if nodeSplit == [10,10,10,10]:
        return 'c'
    elif nodeSplit == [20,20,20,20]:
        return 'm'
    elif nodeSplit == [30,30,30,30]:
        return 'y'
    elif nodeSplit == [40,40,40,40]:
        return 'b'
    elif nodeSplit == [50,50,50,50]:
        return 'g'

def chooseNameNS(nodeSplit):
    if nodeSplit == [10,10,10,10]:
        return '10 clients per app'
    elif nodeSplit == [20,20,20,20]:
        return '20 clients per app'
    elif nodeSplit == [30,30,30,30]:
        return '30 clients per app'
    elif nodeSplit == [40,40,40,40]:
        return '40 clients per app'
    elif nodeSplit == [50,50,50,50]:
        return '50 clients per app'

def plotMeanDataTypeCdfMultiRun(testName, nodeTypes, nodeSplits, dataIdent, folderName, nodeTypesToPlot):
    fig, ax1 = partialCDFBegin(1)
    maxValue = 0
    for nodeSplit in nodeSplits:
        numCLI = sum(nodeSplit)
        df = importDF(testName, numCLI, nodeTypes, nodeSplit, folderName)
        for nodeType,numNodes in zip(nodeTypes,nodeSplit):
            if nodeType in nodeTypesToPlot:
                tempValue = []
                for nodeNum in range(numNodes):
                    colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                    data = df[colName].dropna().tolist()
                    if len(data) > 0: 
                        tempValue.append(statistics.mean(data))
                # print(tempValue)
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                partialCDFPlotDataNoColor(fig, ax1, tempValue, nodeSplit, '-o')
    if dataIdent == 'Mos':
        ax1.set_xlim(0.95,5.05)
    else:
        ax1.set_xlim(0,1.01*maxValue)
    if not os.path.exists('../exports/plots/'+makeFullScenarioName(testName, 0, nodeTypes, [0,0,0,0])):
        os.makedirs('../exports/plots/'+makeFullScenarioName(testName, 0, nodeTypes, [0,0,0,0]))
    partialCDFEnd(fig,ax1,'', 'Mean Client ' + dataIdent + ' Value', '../exports/plots/'+makeFullScenarioName(testName, 0, nodeTypes, [0,0,0,0])+'/'+str(globalCounter)+'_meanCdf' + dataIdent + str(nodeTypesToPlot) + '.pdf')

def plotMultiTest(testName, nodeTypes, nodeSplits):
    for nodeType in nodeTypes:
        plotMeanDataTypeCdfMultiRun(testName, nodeTypes, nodeSplits, 'Mos', 'mos', [nodeType])
    plotMeanDataTypeCdfMultiRun(testName, nodeTypes, nodeSplits, 'RTT', 'rtt', ['hostSSH'])
    plotMeanDataTypeCdfMultiRun(testName, nodeTypes, nodeSplits, 'E2ED', 'e2ed', ['hostVIP'])
    plotMeanDataTypeCdfMultiRun(testName, nodeTypes, nodeSplits, 'PkLR', 'pklr', ['hostVIP'])

# plotMultiTest('baselineTestV3', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[10,10,10,10], [20,20,20,20], [30,30,30,30], [40,40,40,40], [50,50,50,50]])

# plotMeanDataTypeCdfMultiRun('singleAppTest_Video', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[i, 0, 0, 0] for i in range(1,14,1)], 'Mos', 'mos', ['hostVID'])
# plotMeanDataTypeCdfMultiRun('singleAppTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0, 0, i, 0] for i in [1,5,10,15,20,25,30,35,40,45,50,55,60]], 'Mos', 'mos', ['hostSSH'])
# plotMeanDataTypeCdfMultiRun('singleAppTest_SSH', ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [[0, 0, i, 0] for i in [1,5,10,15,20,25,30,35,40,45,50,55,60]], 'RTT', 'rtt', ['hostSSH'])

def plotMosBaseSliComp(testNameBaseline, testName2sli, testName5sli, numCLI, nodeTypes, nodeSplit, cliType):
    matplotlib.rc('lines', linewidth=3.0)
    matplotlib.rc('lines', markersize=8)
    folderName = 'mos'
    dataIdent = 'Mos'
    df = importDF(testNameBaseline, numCLI, nodeTypes, nodeSplit, folderName)
    df2 = importDF(testName2sli, numCLI, nodeTypes, nodeSplit, folderName)
    df5 = importDF(testName5sli, numCLI, nodeTypes, nodeSplit, folderName)
    fig, ax = partialCDFBegin(1)
    maxValue = 0
    for nodeType,numNodes in zip(nodeTypes,nodeSplit):
        if nodeType == cliType:
            tempValue = []
            tempValue2 = []
            tempValue5 = []
            for nodeNum in range(numNodes):
                colName = makeNodeIdentifier(nodeType, nodeNum) + " " + dataIdent + " Val"
                tempValue.extend([normalizeQoE(nodeType, x) for x in df[colName].dropna().tolist()])
                tempValue2.extend([normalizeQoE(nodeType, x) for x in df2[colName].dropna().tolist()])
                tempValue5.extend([normalizeQoE(nodeType, x) for x in df5[colName].dropna().tolist()])
            # print(tempValue)
            if len(tempValue) > 0:
                if maxValue < max(tempValue):
                    maxValue = max(tempValue)
                if len(tempValue2) > 0:
                    if maxValue < max(tempValue2):
                        maxValue = max(tempValue2)
                partialCDFPlotData(fig, ax, tempValue, 'Baseline', '-', 'red')
                print(np.sort(tempValue)[(np.abs(np.linspace(0, 1, len(tempValue), endpoint=True) - 0.4)).argmin()])
                partialCDFPlotData(fig, ax, tempValue2, '2 Slices', '-', 'blue')
                ax.arrow(np.sort(tempValue)[(np.abs(np.linspace(0, 1, len(tempValue), endpoint=True) - 0.4)).argmin()], 0.4, np.sort(tempValue2)[(np.abs(np.linspace(0, 1, len(tempValue2), endpoint=True) - 0.4)).argmin()] - np.sort(tempValue)[(np.abs(np.linspace(0, 1, len(tempValue), endpoint=True) - 0.4)).argmin()], 0, width=0.008, head_width=0.04, head_length=0.08, color='blue', length_includes_head=True, overhang=0.2)
                partialCDFPlotData(fig, ax, tempValue5, '5 Slices', '--', 'green')
                ax.arrow(np.sort(tempValue)[(np.abs(np.linspace(0, 1, len(tempValue), endpoint=True) - 0.6)).argmin()], 0.6, np.sort(tempValue5)[(np.abs(np.linspace(0, 1, len(tempValue5), endpoint=True) - 0.6)).argmin()] - np.sort(tempValue)[(np.abs(np.linspace(0, 1, len(tempValue), endpoint=True) - 0.6)).argmin()], 0, width=0.008, head_width=0.04, head_length=0.08, color='green', length_includes_head=True, overhang=0.2)
    if dataIdent == 'Mos':
        ax.set_xlim(0.95,5.05)
    else:
        ax[0].set_xlim(0,1.01*maxValue)
    prePath = '../exports/plots/baseSlicingComps/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    partialCDFEnd(fig,ax,'', 'Utility', prePath+str(globalCounter)+'_cdf_' + testNameBaseline + '_' + dataIdent + '_' + str(cliType) + '_compWith' + str(testName2sli) + '_and_' + testName5sli + '.pdf')
    partialCDFEndPNG(fig,ax,chooseName(cliType), 'Utility', prePath+str(globalCounter)+'_cdf_' + testNameBaseline + '_' + dataIdent + '_' + str(cliType) + '_compWith' + str(testName2sli) + '_and_' + testName5sli + '.png')

# plotMosBaseSliComp('baselineTest', 'baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 'baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'hostVID')
# plotMosBaseSliComp('baselineTest', 'baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 'baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'hostLVD')
# plotMosBaseSliComp('baselineTest', 'baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 'baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'hostFDO')
# plotMosBaseSliComp('baselineTest', 'baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 'baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'hostSSH')
# plotMosBaseSliComp('baselineTest', 'baselineTestNS_2sli_LVD-BWS_AlgoTest_alpha05', 'baselineTestNS_5sli_AlgoTest_alpha05', 250, ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 'hostVIP')

def plotTPS(testName, numCLI, nodeTypes, nodeSplit, numSlices, direction, cutoff):
    global globalCounter
    print(testName + ': Plotting ' + direction[0] + ' Throughput over time...')
    plotTPdirection(testName, numCLI, nodeTypes, nodeSplit, numSlices, direction)
    globalCounter += 1
    print(testName + ': Plotting ' + direction[0] + ' Throughput CDF...')
    plotTPScdfDirection(testName, numCLI, nodeTypes, nodeSplit, numSlices, direction, cutoff)
    globalCounter += 1
    print(testName + ': Plotting ' + direction[0] + ' Mean Throughput CDF...')
    plotMeanTPScdfDirection(testName, numCLI, nodeTypes, nodeSplit, direction, cutoff)

def plotAll(testName, compTestName, nodeTypes, nodeSplit, numSlices, cutoff):
    global globalCounter
    globalCounter = 0
    numCLI = sum(nodeSplit)
    if not os.path.exists('../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit)):
        os.makedirs('../exports/plots/'+makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit))
    print(testName + ': Plotting Mean MOS CDF...')
    plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'Mos', 'mos2', nodeTypes)
    globalCounter += 1
    print(testName + ': Plotting MOS CDF...')
    plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'Mos', 'mos2', nodeTypes)
    globalCounter += 1
    if compTestName != '':
        plotMeanDataTypeCdfAllAppsComp(testName, compTestName, numCLI, nodeTypes, nodeSplit, 'Mos', 'mos2', nodeTypes)
        globalCounter += 1
        plotDataTypeCdfAllAppsComp(testName, compTestName, numCLI, nodeTypes, nodeSplit, 'Mos', 'mos2', nodeTypes)
        globalCounter += 1
        plotMeanDataTypeCdfAllAppsComp(testName, compTestName, numCLI, nodeTypes, nodeSplit, 'E2ED', 'endToEndDelay', nodeTypes)
        globalCounter += 1
    else:
        globalCounter += 3
    plotTPS(testName, numCLI, nodeTypes, nodeSplit, numSlices, downlink, cutoff)
    globalCounter += 1
    plotTPS(testName, numCLI, nodeTypes, nodeSplit, numSlices, uplink, cutoff)
    globalCounter += 1

    # if 'hostSSH' in nodeTypes: 
    #     plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'RTT', 'rtt', ['hostSSH'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'RTT', 'rtt', ['hostSSH'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'RTT', 'rtt', ['hostSSH'])
    #     globalCounter += 1
    # else:
    #     globalCounter += 3
    globalCounter += 3
    # if 'hostVIP' in nodeTypes: 
    #     plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'E2ED', 'e2ed', ['hostVIP'])
    #     globalCounter += 1
    #     plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'PkLR', 'pklr', ['hostVIP'])
    #     globalCounter += 1
    #     plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'PlDel', 'pldel', ['hostVIP'])
    #     globalCounter += 1
    #     plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'PlLR', 'pllr', ['hostVIP'])
    #     globalCounter += 1
    #     plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'TDLR', 'tdlr', ['hostVIP'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'E2ED', 'e2ed', ['hostVIP'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'PkLR', 'pklr', ['hostVIP'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'PlDel', 'pldel', ['hostVIP'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'PlLR', 'pllr', ['hostVIP'])
    #     globalCounter += 1
    #     plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'TDLR', 'tdlr', ['hostVIP'])
    #     globalCounter += 1
    # else:
    #     globalCounter += 10
    globalCounter += 10
    if 'hostLVD' in nodeTypes:
        print(testName + ': Plotting Live Video Delay To Live CDF...')
        plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'DLVD', 'dlvd', ['hostLVD'])
        globalCounter += 1
        if compTestName != '':
            plotDataTypeCdfAllAppsComp(testName, compTestName, numCLI, nodeTypes, nodeSplit, 'DLVD', 'dlvd', ['hostLVD'])
        globalCounter += 1
        print(testName + ': Plotting Live Video Delay To Live CDF...')
        plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'DAEB', 'daeb', ['hostLVD'])
        globalCounter += 1
        print(testName + ': Plotting Live Video Estimated Bitrate CDF...')
        plotEstimatedChosenBitrateLVD(testName, numCLI, nodeTypes, nodeSplit, ['hostLVD'])
        globalCounter += 1
    if 'hostVID' in nodeTypes and 'hostLVD' in nodeTypes:
        print(testName + ': Plotting Video Buffer Length CDF...')
        plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'DABL', 'dabl', ['hostVID', 'hostLVD'])
        globalCounter += 1
        print(testName + ': Plotting Chosen Video Bitrate CDF...')
        plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'DAVB', 'davb', ['hostVID', 'hostLVD'])
        globalCounter += 1
        print(testName + ': Plotting Chosen Video Resolution CDF...')
        plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'DAVR', 'davr', ['hostVID', 'hostLVD'])
        globalCounter += 1
        print(testName + ': Plotting Video MOS CDF...')
        plotDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'DAMS', 'dams', ['hostVID', 'hostLVD'])
        globalCounter += 1
    if compTestName != '':
        plotMeanTPScdfDirectionComp(testName, compTestName, numCLI, nodeTypes, nodeSplit, downlink, cutoff)
    globalCounter += 1
    # print(testName + ': Plotting Mean End-To-End Delay CDF...')
    # plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'E2ED', 'endToEndDelay', nodeTypes)
    # globalCounter += 1
    # print(testName + ': Plotting Mean RTT CDF...')
    # plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'rtt', 'rtt', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH'])
    # globalCounter += 1
    # print(testName + ': Plotting VoIP Mean End-To-End Delay CDF...')
    # plotMeanDataTypeCdfAllApps(testName, numCLI, nodeTypes, nodeSplit, 'E2ED', 'endToEndDelay', ['hostVIP'])
    # globalCounter += 1


# plotAll('baselineTest', '', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [50 for x in range(5)], 1, 400)
# plotAll('newHmsQoeAdm4-3xDelNo3_5sli_R100_Q35_M100_C200_PFalse', '', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,19,19,41,40], 1, 400)
# plotAll('newHmsQoeAdmNo3_5sli_R100_Q35_M100_C200_PFalse', '', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [20,19,19,31,30], 1, 400)


if __name__ == "__main__":
    name = sys.argv[3]
    numVID = int(name.split('VID')[1].split('_LVD')[0])
    numLVD = int(name.split('LVD')[1].split('_FDO')[0])
    numFDO = int(name.split('FDO')[1].split('_SSH')[0])
    numSSH = int(name.split('SSH')[1].split('_VIP')[0])
    numVIP = int(name.split('_VIP')[1].split('_cVIP')[0])
    numcVIP = int(name.split('cVIP')[1])
    plotAll(sys.argv[1], '', ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP', 'hostcVIP'], [numVID, numLVD, numFDO, numSSH, numVIP, numcVIP], int(sys.argv[2]), 280)
    # extractAll(sys.argv[1], ['hostVID', 'hostLVD', 'hostFDO', 'hostSSH', 'hostVIP'], [numVID, numLVD, numFDO, numSSH, numVIP], int(sys.argv[2]))