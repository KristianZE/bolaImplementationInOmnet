import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import csv
import math
import statistics
from scipy import stats
import scipy
import os

font = {'weight' : 'normal',
        'size'   : 40}

matplotlib.rc('font', **font)
matplotlib.rc('lines', linewidth=2.0)
matplotlib.rc('lines', markersize=8)

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']
maxSimTime = 400

def makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit):
    scenName = str(testName) + '_' + str(numCLI)
    for nodeType,numNodesType in zip(nodeTypes, nodeSplit):
        scenName += '_' + nodeType.replace('host','') + str(numNodesType)
    return scenName

def makeXaxisLabel(valueType):
    if 'mos' in valueType:
        return 'Average Mos Value'
    if valueType == 'endToEndDelay':
        return 'Average End-To-End Delay [s]'
    if valueType == 'packetLossRate':
        return 'Average Packet Loss Rate'
    if valueType == 'playoutLossRate':
        return 'Average Playout Loss Rate'
    if valueType == 'playoutDelay':
        return 'Average Playout Delay [s]'
    if valueType == 'averageDownloadThroughput':
        return 'Average Download Throughput [bps]'
    if valueType == 'downloadTime':
        return 'Average Download Time [s]'
    if valueType == 'DASHReceivedBytes':
        return 'Average Number of Bytes Received per Video Segment'
    if valueType == 'DASHBufferLength':
        return 'Average Video Buffer Length [s]'
    if valueType == 'numActiveSessions':
        return 'Average Number of Active Sessions per Client'
    if valueType == 'roundTripTime':
        return 'Average Round Trip Time [s]'
    if valueType == 'packetReceived':
        return 'Average Size of Received Packets [Bytes]'
    if valueType == 'packetSent':
        return 'Average Size of Sent Packets [Bytes]'
    if valueType == 'DASHliveDelay':
        return 'Average Delay to Live Video Edge [s]'

    return valueType

def plotDelayMeanValue(testName, numCLI, nodeTypes, nodeSplit, valueType):
    delays = []
    meanValues = []
    file_to_read = '../exports/extracted/' + valueType + '/' + makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                delays = row
            elif line_count == 1:
                meanValues = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    dela = [x for x, y in zip(delays, meanValues) if y >= 0]
    meanVal = [x for x in meanValues if x >= 0]
    ax1.plot(dela, meanVal, 'o-')
    
    plt.xlabel('Link Delay [ms]')
    plt.ylabel(makeXaxisLabel(valueType))
    prePath = '../exports/plots/' + makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + valueType + '.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + valueType + '.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotDelayMeanTPsDirection(testName, numCLI, nodeTypes, nodeSplit, direction):
    delays = []
    meanValues = []
    file_to_read = '../exports/extracted/throughput' + direction[0] + '/' + makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                delays = row
            elif line_count == 1:
                meanValues = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(delays, meanValues, 'o-')
    
    plt.xlabel('Link Delay [ms]')
    plt.ylabel('Mean ' + direction[0] + ' Throughput [kbps]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, numCLI, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'meanThroughput' + direction[0] + '.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanThroughput' + direction[0] + '.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotMeanTPMeanE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanTPMeanE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                meanTPs = row
            elif line_count == 1:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Mean Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'meanTPMeanE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanTPMeanE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotMeanTPMedianE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanTPMedianE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                meanTPs = row
            elif line_count == 1:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Median Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'mediTPMedianE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanTPMedianE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotMeanTPMaxE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanTPMaxE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                meanTPs = row
            elif line_count == 1:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Max Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'meanTPMaxE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanTPMaxE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotMeanTPXPercentileE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit, percentile):
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanTP' + str(percentile) + 'percentileE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                meanTPs = row
            elif line_count == 1:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel(str(percentile) + 'th-Percentile Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'meanTP' + str(percentile) + 'percentileE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanTP' + str(percentile) +'percentileE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


def plotMeanQLMeanE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanQLandMeanE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                meanTPs = row
            elif line_count == 1:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Queue Length [packets]')
    plt.ylabel('Mean Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'meanQLMeanE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanQLMeanE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# plotMeanTPMeanE2EDScatter('singleAppStressTest_SSH_smallLink', 8200, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,400,0])

def plotAllValuesForDelayTest(testName, nodeTypes, nodeSplit, nodeType):
    print('Plotting for ' + testName)
    numCLI = sum(nodeSplit)
    valueTypes = []
    if nodeType == 'hostVIP':
        valueTypes = ['mos', 'endToEndDelay', 'packetLossRate', 'playoutDelay', 'playoutLossRate', 'taildropLossRate']
        plotDelayMeanTPsDirection(testName, numCLI, nodeTypes, nodeSplit, downlink)
    if nodeType == 'hostSSH':
        valueTypes = ['numActiveSessions', 'packetSent', 'packetReceived', 'endToEndDelay', 'roundTripTime', 'mosValue']
        plotDelayMeanTPsDirection(testName, numCLI, nodeTypes, nodeSplit, downlink)
        plotDelayMeanTPsDirection(testName, numCLI, nodeTypes, nodeSplit, uplink)
    if nodeType == 'hostVID':
        valueTypes = ['DASHBufferLength', 'DASHVideoBitrate', 'numActiveSessions', 'DASHReceivedBytes', 'DASHmosScore', 'DASHliveDelay']
        plotDelayMeanTPsDirection(testName, numCLI, nodeTypes, nodeSplit, downlink)
        plotDelayMeanTPsDirection(testName, numCLI, nodeTypes, nodeSplit, uplink)
    for valueType in valueTypes:
        plotDelayMeanValue(testName, numCLI, nodeTypes, nodeSplit, valueType)

def plotStressMeanValue(testName, numCLIs, nodeTypes, nodeSplit, valueType):
    meanValues = []
    file_to_read = '../exports/extracted/' + valueType + '/' + makeFullScenarioName(testName, numCLIs, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 1:
                meanValues = row
                break
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    nCLI = [x for x, y in zip(numCLIs, meanValues) if y >= 0]
    meanVal = [x for x in meanValues if x >= 0]
    ax1.plot(nCLI, meanVal, 'o-')
    
    plt.xlabel('Number of Clients')
    plt.ylabel(makeXaxisLabel(valueType))
    prePath = '../exports/plots/' + makeFullScenarioName(testName, numCLIs, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + valueType + '.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + valueType + '.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, direction):
    meanValues = []
    file_to_read = '../exports/extracted/throughput' + direction[0] + '/' + makeFullScenarioName(testName, numCLIs, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 1:
                meanValues = row
                break
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(numCLIs, meanValues, 'o-')
    
    plt.xlabel('Number of Clients')
    plt.ylabel('Mean ' + direction[0] + ' Throughput [kbps]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, numCLIs, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'meanThroughput' + direction[0] + '.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'meanThroughput' + direction[0] + '.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def plotAllValuesForStressTest(testName, numCLIs, nodeTypes, nodeSplit, nodeType):
    print('Plotting for ' + testName)
    valueTypes = []
    if nodeType == 'hostVIP':
        valueTypes = ['mos', 'endToEndDelay', 'packetLossRate', 'playoutDelay', 'playoutLossRate', 'taildropLossRate']
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, downlink)

    if nodeType == 'hostSSH':
        valueTypes = ['numActiveSessions', 'packetSent', 'packetReceived', 'endToEndDelay', 'roundTripTime', 'mosValue']
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, downlink)
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, uplink)
        plotMeanQLMeanE2EDScatter(testName, sum(numCLIs), nodeTypes, nodeSplit)

    if nodeType == 'hostFDO':
        valueTypes = ['endToEndDelay', 'mosScore', 'downloadTime', 'averageDownloadThroughput']
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, downlink)
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, uplink)

    if nodeType == 'hostVID':
        valueTypes = ['DASHBufferLength', 'DASHVideoBitrate', 'numActiveSessions', 'DASHReceivedBytes', 'DASHmosScore', 'DASHliveDelay']
        if 'Live' in testName:
            valueTypes.append('endToEndDelay')
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, downlink)
        plotStressMeanTPsDirection(testName, numCLIs, nodeTypes, nodeSplit, uplink)

    plotMeanTPMeanE2EDScatter(testName, sum(numCLIs),nodeTypes, nodeSplit)
    plotMeanTPMedianE2EDScatter(testName, sum(numCLIs),nodeTypes, nodeSplit)
    plotMeanTPMaxE2EDScatter(testName, sum(numCLIs),nodeTypes, nodeSplit)
    plotMeanTPXPercentileE2EDScatter(testName, sum(numCLIs),nodeTypes, nodeSplit, 90)
    plotMeanTPXPercentileE2EDScatter(testName, sum(numCLIs),nodeTypes, nodeSplit, 95)
    plotMeanTPXPercentileE2EDScatter(testName, sum(numCLIs),nodeTypes, nodeSplit, 97)

    

    for valueType in valueTypes:
        plotStressMeanValue(testName, numCLIs, nodeTypes, nodeSplit, valueType)


def plotLSMeanTPMeanE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsMeanTPMeanE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Mean Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsMeanTPMeanE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsMeanTPMeanE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# plotLSMeanTPMeanE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSMeanTPMeanE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1])
# plotLSMeanTPMeanE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMeanE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMeanE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])

def plotLSMeanTPMeanRTTScatter(testName, sumNodes, nodeTypes, nodeSplit):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsMeanTPMeanRTT/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(meanTPs, [x*1000 for x in meanE2EDs], 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Mean Client RTT [ms]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsMeanTPMeanRTTScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsMeanTPMeanRTTScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# plotLSMeanTPMeanRTTScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSMeanTPMeanRTTScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMeanRTTScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMeanRTTScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])

def negExpFunc(x, a, b, c):
    return a * np.exp(-b*x) + c

def negLinFunc(x, a, b, c):
    return -a*x + b

def plotLSLinkSpeedMeanE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit, pZero):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsMeanTPMeanE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    print(min(meanE2EDs))

    tps = tps[17:]
    meanE2EDs = meanE2EDs[17:]

    ax1.plot(tps, [x*1000 for x in meanE2EDs], 'o')

    popt, pcov = scipy.optimize.curve_fit(negExpFunc, tps, [x*1000 for x in meanE2EDs], p0=pZero, maxfev=1000000, bounds=(0,np.inf))
    # popt = pZero
    with np.printoptions(precision=2):
        print(testName + ' with ' + str(nodeSplit) + ': ' + str(popt))
        # regLine = np.linspace(0, max(meanUtilValues), 100)
        # print(tps[-1])
        regLine = np.linspace(tps[0], tps[-1], 1000)
        theLabel = 'Exponential Fit'
        ax1.plot(regLine, negExpFunc(regLine, *popt), '-', label=theLabel, color='orange')
    
    print(min([x*1000 for x in meanE2EDs]))

    plt.xlabel('Link Bandwidth [kbps]')
    plt.ylabel('Mean Client End-To-End Delay [ms]')

    # ax1.set_ylim(0,1000)

    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsLinkSpeedMeanE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsLinkSpeedMeanE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


# plotLSLinkSpeedMeanE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSLinkSpeedMeanE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [2, 0.01, 1])
# plotLSLinkSpeedMeanE2EDScatter('singleAppLSTest_VoIP_corrected', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [50,0.00000000001,500])
# plotLSLinkSpeedMeanE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSLinkSpeedMeanE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSLinkSpeedMeanE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])


def plotLSLinkSpeedMeanE2EDScatterManReg(testName, sumNodes, nodeTypes, nodeSplit, popt):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsMeanTPMeanE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    print(min(meanE2EDs))

    tps = tps[17:]
    meanE2EDs = meanE2EDs[17:]

    ax1.plot(tps, [x*1000 for x in meanE2EDs], 'o')

    # popt, pcov = scipy.optimize.curve_fit(negExpFunc, tps, [x*1000 for x in meanE2EDs], p0=pZero, maxfev=1000000, bounds=(0,np.inf))
    # popt = pZero
    with np.printoptions(precision=2):
        print(testName + ' with ' + str(nodeSplit) + ': ' + str(popt))
        # regLine = np.linspace(0, max(meanUtilValues), 100)
        # print(tps[-1])
        regLine = np.linspace(tps[0], tps[-1], 1000)
        theLabel = 'Exponential Fit'
        ax1.plot(regLine, negExpFunc(regLine, *popt), '-', label=theLabel, color='orange')
    
    print(min([x*1000 for x in meanE2EDs]))

    plt.xlabel('Link Bandwidth [kbps]')
    plt.ylabel('Mean Client End-To-End Delay [ms]')

    # ax1.set_ylim(0,1000)

    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsLinkSpeedMeanE2EDScatterManReg.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsLinkSpeedMeanE2EDScatterManReg.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

plotLSLinkSpeedMeanE2EDScatterManReg('singleAppLSTest_VoIP_corrected', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], [45e+04,3e-02,3.1])

def plotLSLinkSpeedMeanRTTScatter(testName, sumNodes, nodeTypes, nodeSplit, pZero):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsMeanTPMeanRTT/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(tps, [x*1000/2 for x in meanE2EDs], 'o')

    popt, pcov = scipy.optimize.curve_fit(negExpFunc, tps, [x*1000/2 for x in meanE2EDs], p0=pZero, maxfev=1000000, bounds=(0,np.inf))
    
    with np.printoptions(precision=2):
        print(testName + ' with ' + str(nodeSplit) + ': ' + str(popt))
        # regLine = np.linspace(0, max(meanUtilValues), 100)
        print(tps[-1])
        regLine = np.linspace(0, tps[-1], 1000)
        theLabel = 'Exponential Fit'
        ax1.plot(regLine, negExpFunc(regLine, *popt), '-', label=theLabel, color='orange')
    
    plt.xlabel('Link Bandwidth [kbps]')
    plt.ylabel('One-Way Delay (1/2 RTT) [ms]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsLinkSpeedMeanRTTScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsLinkSpeedMeanRTTScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], [1,1,0])
# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [200,0.0001,0])
# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [0.1,0.001,0])
# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [200,0.001,0])

# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_VideoLongV2', 226, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [200,0.0001,0])
# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_FileDownloadV3', 226, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], [200,0.001,0])
# plotLSLinkSpeedMeanRTTScatter('singleAppLSTest_LiveVideoClientV2', 226, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], [200,0.0001,0])


def plotLSMeanTPMedianE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsEachNodeMeanTPMedianE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    print(meanTPs)
    print(meanE2EDs)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Median Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsMeanTPMedianE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsMeanTPMedianE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# plotLSMeanTPMedianE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSMeanTPMedianE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1])
# plotLSMeanTPMedianE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMedianE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMedianE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])


def plotLSLinkSpeedMedianE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsEachNodeMeanTPMedianE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(tps, meanE2EDs, 'o')
    
    plt.xlabel('Link Bandwidth [kbps]')
    plt.ylabel('Median Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsLinkSpeedMedianE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsLinkSpeedMedianE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


# plotLSLinkSpeedMedianE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSLinkSpeedMedianE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1])
# plotLSLinkSpeedMedianE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSLinkSpeedMedianE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSLinkSpeedMedianE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])


def plotLSMeanTPMaxE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsEachNodeMeanTPMaxE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    print(meanTPs)
    print(meanE2EDs)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel('Max Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsMeanTPMaxE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsMeanTPMaxE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# plotLSMeanTPMaxE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSMeanTPMaxE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1])
# plotLSMeanTPMaxE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMaxE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSMeanTPMaxE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])


def plotLSLinkSpeedMaxE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/lsEachNodeMeanTPMaxE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(tps, meanE2EDs, 'o')
    
    plt.xlabel('Link Bandwidth [kbps]')
    plt.ylabel('Max Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsLinkSpeedMaxE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsLinkSpeedMaxE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


# plotLSLinkSpeedMaxE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0])
# plotLSLinkSpeedMaxE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1])
# plotLSLinkSpeedMaxE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSLinkSpeedMaxE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0])
# plotLSLinkSpeedMaxE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0])


def plotLSMeanTPXPercentileE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit, percentile):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanTP' + str(percentile) + 'percentileE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    print(meanTPs)
    print(meanE2EDs)
    ax1.plot(meanTPs, meanE2EDs, 'o')
    
    plt.xlabel('Mean Client Throughput [kbps]')
    plt.ylabel(str(percentile) + 'th-Percentile Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsMeanTP' + str(percentile) + 'percentileE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsMeanTP' + str(percentile) +'percentileE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 97)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 97)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 97)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 97)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], 97)

# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 95)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 95)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 95)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 95)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], 95)

# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 90)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 90)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 90)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 90)
# plotLSMeanTPXPercentileE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], 90)


def plotLSLinkSpeedXPercentileE2EDScatter(testName, sumNodes, nodeTypes, nodeSplit, percentile):
    tps = []
    meanTPs = []
    meanE2EDs = []
    file_to_read = '../exports/extracted/eachNodeMeanTP' + str(percentile) + 'percentileE2ED/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                tps = row
            elif line_count == 1:
                meanTPs = row
            elif line_count == 2:
                meanE2EDs = row
            line_count += 1 

    fig, ax1 = plt.subplots(1, figsize=(16,12))
    # print(meanValues)
    ax1.plot(tps, meanE2EDs, 'o')
    
    plt.xlabel('Link Bandwidth [kbps]')
    plt.ylabel(str(percentile) + 'th-Percentile Client End-To-End Delay [s]')
    prePath = '../exports/plots/' + makeFullScenarioName(testName, sumNodes, nodeTypes, nodeSplit) + '/'
    if not os.path.exists(prePath):
        os.makedirs(prePath)
    outPath = prePath + 'lsLinkSpeed' + str(percentile) +'percentileE2EDScatter.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath2 = prePath + 'lsLinkSpeed' + str(percentile) +'percentileE2EDScatter.png'
    fig.savefig(outPath2, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 97)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 97)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 97)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 97)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], 97)

# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 95)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 95)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 95)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 95)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], 95)

# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_SSH', 40, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,1,0], 90)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_VoIP', 51, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,0,0,1], 90)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_Video', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 90)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_NewLiveVideoClient', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [1,0,0,0], 90)
# plotLSLinkSpeedXPercentileE2EDScatter('singleAppLSTest_FileDownload2-5MB', 60, ['hostVID', 'hostFDO', 'hostSSH', 'hostVIP'], [0,1,0,0], 90)