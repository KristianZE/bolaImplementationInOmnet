import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors, cm
import matplotlib
import csv
import math
import statistics
from scipy import stats
import os

from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)

font = {'weight' : 'normal',
        'size'   : 40}

matplotlib.rc('font', **font)
matplotlib.rc('lines', linewidth=2.0)
matplotlib.rc('lines', markersize=8)

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']
maxSimTime = 40

def plotHeatMap(testName):
    xAxis = []
    yAxis = []
    tempMosMap = []
    mosMap = []
    csvFolder = '../exports/heatMap/' # Path to folder with csv heat map results
    file_to_read = csvFolder+testName+'.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                xAxis = row
            elif line_count == 1:
                yAxis = row
            elif line_count == 2:
                tempMosMap = row
            line_count += 1 
    for row in tempMosMap:
        mosMap.append([float(x) for x in row.replace(' ', '').replace('[', '').replace(']', '').split(',')])

    newMosMap = []
    for x in range(len(xAxis)):
        newMosMap.append([])
        for y in range(len(yAxis)):
            newMosMap[x].append(mosMap[y][x])

    tempMax = 0
    tempMin = 6
    for x in range(len(xAxis)):
        for y in range(len(yAxis)):
            if newMosMap[x][y] > tempMax:
                tempMax = newMosMap[x][y]
            if newMosMap[x][y] < tempMin:
                tempMin = newMosMap[x][y]

    print("Max: " + str(tempMax) + "; Min: " + str(tempMin))

    newMosMap = newMosMap[::-1]
    xAxis = xAxis[::-1]

    print(testName + ' xAxis length: ' + str(len(xAxis)))
    print(testName + ' yAxis length: ' + str(len(yAxis)))

    fig, ax = plt.subplots(1, figsize=(16,12))
    norm = matplotlib.colors.Normalize(vmin=1.0, vmax=5.0)
    cmap = plt.cm.get_cmap(name='viridis',lut=1024)
    im = ax.imshow(np.array(newMosMap), norm=norm, cmap=cmap, aspect='auto')
    
    cbar = ax.figure.colorbar(im, ax=ax, norm=norm, cmap=cmap)

    
    cbar.mappable.set_clim(1.0, 5.0)
    cbar.ax.set_ylabel('MOS Value', rotation=-90, va="bottom")

    xAxis = [int(x) for x in xAxis]
    yAxis = [int(y) for y in yAxis]

    ax.set_yticks(np.arange(len(xAxis)))
    ax.set_xticks(np.arange(len(yAxis)))

    ax.set_yticklabels(xAxis)
    ax.set_xticklabels(yAxis)


    xAxisMajor = 3
    if 'V2' in testName or 'V3' in testName:
        xAxisMajor = 15


    labels = ax.get_xticklabels() # get x labels
    newLabels = [0]
    for i,_ in enumerate(labels):
        if i % xAxisMajor == 0: newLabels.append(labels[i])
    ax.xaxis.set_major_locator(MultipleLocator(xAxisMajor))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.set_xticklabels(newLabels, rotation=90) # set new labels

    newLabels = [0]
    labels = ax.get_yticklabels() # get y labels
    for i,l in enumerate(labels):
        if i%3 == 0: newLabels.append(labels[i])
    ax.yaxis.set_major_locator(MultipleLocator(3))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.set_yticklabels(newLabels, rotation=0) # set new labels
    # plt.show()
    plt.ylabel("Link Delay [ms]")
    plt.xlabel("Link Throughput [kbps]")
    outPath = '../exports/plots/heatMapTest/' + testName + '.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    outPath = '../exports/plots/heatMapTest/' + testName + '.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

def normalizeQoE(cliType, mos):
    retMos = 0.0
    if cliType == 'hostFDO':
        retMos = (mos - 1.0)*((5.0 - 1.0)/(5.0 - 1.0)) + 1.0
    elif cliType == 'hostSSH':
        retMos = (mos - 1.0)*((5.0 - 1.0)/(4.292851753999999 - 1.0)) + 1.0
    elif cliType == 'hostVID':
        retMos = (mos - 1.0)*((5.0 - 1.0)/(4.394885531954699 - 1.0)) + 1.0
    elif cliType == 'hostVIP':
        retMos = (mos - 1.0)*((5.0 - 1.0)/(4.5 - 1.0)) + 1.0
    elif cliType == 'hostLVD':
        retMos = (mos - 1.0)*((5.0 - 1.0)/(4.585703050898499 - 1.0)) + 1.0
    # return max(1.0, min(retMos, 5.0))
    return retMos

def plotHeatMapUtility(testName, cliType):
    xAxis = []
    yAxis = []
    tempMosMap = []
    mosMap = []
    csvFolder = '../exports/heatMap/' # Path to folder with csv heat map results
    file_to_read = csvFolder+testName+'.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                xAxis = row
            elif line_count == 1:
                yAxis = row
            elif line_count == 2:
                tempMosMap = row
            line_count += 1 
    for row in tempMosMap:
        mosMap.append([float(x) for x in row.replace(' ', '').replace('[', '').replace(']', '').split(',')])

    newMosMap = []
    for x in range(len(xAxis)):
        newMosMap.append([])
        for y in range(len(yAxis)):
            newMosMap[x].append(normalizeQoE(cliType,mosMap[y][x]))

    tempMax = 0
    tempMin = 6
    for x in range(len(xAxis)):
        for y in range(len(yAxis)):
            if newMosMap[x][y] > tempMax:
                tempMax = newMosMap[x][y]
            if newMosMap[x][y] < tempMin:
                tempMin = newMosMap[x][y]

    print("Max: " + str(tempMax) + "; Min: " + str(tempMin))

    newMosMap = newMosMap[::-1]
    xAxis = xAxis[::-1]

    print(testName + ' xAxis length: ' + str(len(xAxis)))
    print(testName + ' yAxis length: ' + str(len(yAxis)))

    fig, ax = plt.subplots(1, figsize=(16,12))
    norm = matplotlib.colors.Normalize(vmin=1.0, vmax=5.0)
    cmap = plt.cm.get_cmap(name='viridis',lut=1024)
    im = ax.imshow(np.array(newMosMap), norm=norm, cmap=cmap)
    
    cbar = ax.figure.colorbar(im, ax=ax, norm=norm, cmap=cmap)

    cbar.ax.set_ylabel('Utility', rotation=-90, va="bottom")
    cbar.set_clim(1.0, 5.0)


    xAxis = [int(x) for x in xAxis]
    yAxis = [int(y) for y in yAxis]

    ax.set_yticks(np.arange(len(xAxis)))
    ax.set_xticks(np.arange(len(yAxis)))

    ax.set_yticklabels(xAxis)
    ax.set_xticklabels(yAxis)

    labels = ax.get_xticklabels() # get x labels
    for i,l in enumerate(labels):
        if(i%3 != 0): labels[i] = '' # skip even labels
    ax.set_xticklabels(labels, rotation=90) # set new labels

    labels = ax.get_yticklabels() # get y labels
    for i,l in enumerate(labels):
        if(i%3 != 0): labels[i] = '' # skip even labels
    ax.set_yticklabels(labels, rotation=0) # set new labels

    plt.ylabel("Delay [ms]")
    plt.xlabel("Bandwidth [kbps]")
    outPath = '../exports/plots/heatMapTest/utility_' + testName + '.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    plt.close('all')


# Function calls for various clients
# plotHeatMap('heatMapTest_SSH') # SSH Client
# plotHeatMap('heatMapTest_VoIP') # VoIP Client
# plotHeatMap('heatMapTest_VideoV2') # VoD Client
# plotHeatMap('heatMapTest_NewLiveVideoClient') # Live Video Client
# plotHeatMap('heatMapTest_FileDownload2-5MB') # File Download Client

# plotHeatMap('heatMapTest_VideoLong')
# plotHeatMap('heatMapTest_VideoFineLong')

# plotHeatMap('heatMapTest_LiveVideoLong')
# plotHeatMap('heatMapTest_LiveVideoShort')



# plotHeatMap('heatMapTest_VideoFine') # VoD Client
# plotHeatMap('heatMapTest_LiveVideoFine') # Live Video Client
# plotHeatMap('heatMapTest_FileDownloadFine') # File Download Client

# plotHeatMapUtility('heatMapTest_VoIP', 'hostVIP')
# plotHeatMapUtility('heatMapTest_SSH', 'hostSSH')
# plotHeatMapUtility('heatMapTest_VideoV2', 'hostVID')
# plotHeatMapUtility('heatMapTest_NewLiveVideoClient', 'hostLVD')
# plotHeatMapUtility('heatMapTest_FileDownload2-5MB', 'hostFDO')

# plotHeatMapUtility('heatMapTest_VideoLong', 'hostVID')

# plotHeatMap('heatMapTest_LiveVideoFineShort') # Live Video Client
# plotHeatMap('heatMapTest_LiveVideoFineLong') # Live Video Client

# plotHeatMapUtility('heatMapTest_LiveVideoFineShort', 'hostLVD')
# plotHeatMapUtility('heatMapTest_LiveVideoFineLong', 'hostLVD')

# plotHeatMapUtility('heatMapTest_LiveVideoShort', 'hostLVD')
# plotHeatMapUtility('heatMapTest_LiveVideoLong', 'hostLVD')

# plotHeatMapUtility('heatMapTest_VideoFineLong', 'hostVID')

# plotHeatMapUtility('heatMapTest_FileDownloadFine', 'hostFDO')

# plotHeatMapUtility('heatMapTest_VoIP_corrected', 'hostVIP')


# plotHeatMap('heatMapTest_LiveVideoFineLongV2')
# plotHeatMap('heatMapTest_VideoFineLongV2')
# plotHeatMap('heatMapTest_FileDownloadFine')
# plotHeatMap('heatMapTest_SSH')
plotHeatMap('heatMapTest_VoIP_corrected')

#plotHeatMap('heatMapTest_FileDownloadFineV3')
