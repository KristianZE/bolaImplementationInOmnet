import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import csv
import math
import statistics
from scipy import stats
import os,sys,inspect
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.patches as patches

import re

import glob

font = {'weight' : 'normal',
        'size'   : 30}

matplotlib.rc('font', **font)
matplotlib.rc('lines', linewidth=2.0)
matplotlib.rc('lines', markersize=8)

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']
maxSimTime = 400

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
    print(dataName)
    print("in selection!!!!!!!!!")
    if dataName == 'VID':
        return 'VoD'
    elif dataName == 'FDO':
        return 'FD'
    elif dataName == 'SSH':
        return 'SSH'
    elif dataName == 'VIP':
        return 'VoIP'
    elif dataName == 'LVD':
        return 'Live'
    elif dataName == 'cVIP':
        return 'crit VIP'
gbrToColor = {
    100 : 'lime',
    95 : 'tab:orange',
    90 : 'tab:red',
    85 : 'tab:pink',
    80 : 'tab:blue',
    75 : 'tab:cyan',
    70 : 'tab:green',
    65 : 'tab:purple',
    60 : 'tab:brown',
    55 : 'tab:olive',
    50 : 'tab:gray',
}

mbrToPoint = {
    100 : 'o',
    125 : 'v',
    150 : 'P',
    175 : 's',
    200 : 'p',
    225 : 'X',
    250 : 'D',
    275 : '1',
    300 : '*'
}


def getFileInfo(filename, desInfo):
    eN = filename.split('/')[-1].split('.')[0]
    resDict = {}
    resDict['name'] = eN
    for param in eN.split('-')[-1].split('_'):
        split = re.split('(\d+)',param)
        if split[0] in desInfo:
            resDict[split[0]] = int(split[1])
    return resDict

def plotParameterStudyMOS(testPrefix, appType, mbrs, gbrs, qs, maxNumCliPlot):
    print('-------------', testPrefix, '-------------')
    prePath = '../exports/extracted/mos2/'
    filenames = glob.glob(prePath+testPrefix+'*')
    print('-> There are', len(filenames), 'experiments in this parameter study.')
    fig, ax = plt.subplots(1, figsize=(16,12))
    filterName = 'Val'
    
    reqRunInfo = ['Q', 'M', 'C'] # Q = target QoE, M = GBR multiplier, C = MBR multiplier
    reqRunInfo.append(appType) # This will get the number of clients in experiment

    runResults = {}
    numClis = []
    minValue = 5.0

    for filename in filenames:
        fid = getFileInfo(filename, reqRunInfo)
        if fid['Q'] == qs and fid['M'] in gbrs and fid['C'] in mbrs and fid[appType] <= maxNumCliPlot:
            print('\t-> Run:', fid['name'], end=': ')
            runDict = {}
            runDict['Q'] = fid['Q'] # Target QoE in run
            runDict['M'] = fid['M'] # GBR multiplier in run
            runDict['C'] = fid['C'] # MBR multiplier in run
            runDict['numCli'] = fid[appType] # Number of clients in run
            if runDict['numCli'] not in numClis:
                numClis.append(runDict['numCli'])
            
            # Getting values
            runDF = pd.read_csv(filename)
            valDF = filterDFType(filterDFType(runDF, filterName), appType)
            meanRunVals = []

            # Get mean for each client in run first
            for col in valDF:
                meanRunVals.append(statistics.mean(valDF[col].dropna().tolist()))
            # Then calculate the mean for fun based on client means
            runDict['meanVal'] = statistics.mean(meanRunVals)
            minValue = min(minValue, runDict['meanVal'])
            print('mean QoE =', runDict['meanVal'])
            runResults[fid['name']] = runDict # Store it ready to plot
    
    numClis = sorted(numClis)
    # minmax = (1.0,4.5)
    minmax = (minValue-0.05,4.5)

    # Plot the means
    for run in runResults:
        runData = runResults[run]
        ax.scatter(2*numClis.index(runData['numCli']), runData['meanVal'], marker=mbrToPoint[runData['C']], color=gbrToColor[runData['M']], alpha=0.7, s=16**2)
    
    # Take care of the legend
    legendHandles = []
    for mbr in mbrs:
        point = ax.scatter(-10,5, marker=mbrToPoint[mbr], color='black', label='MBR of ' + str(mbr) + '%', s=14**2)
        legendHandles.append(point)
    for gbr in gbrs:
        ptch = mpatches.Patch(color=gbrToColor[gbr], label='GBR of ' + str(gbr) + '%')
        legendHandles.append(ptch)

    ticks = []
    labels = []
    for num in range(len(numClis)):
        ax.vlines(2*num+1, ymin=minmax[0], ymax=minmax[1], color='black')
        ticks.append(2*num)
        labels.append(numClis[num])

    # Finish plotting
    preOutPath = '../exports/paramStudyPlots/mosVsNumCli/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)
    ax.set_ylim(minmax)
    ax.set_xlim(-1,2*len(numClis)-1)

    plt.xticks(ticks, labels, rotation=0)
    plt.legend(handles=legendHandles, fontsize=25, bbox_to_anchor=(1, 1), loc='upper left')
    plt.grid(axis='y')
    plt.xlabel('Number of Clients')
    plt.ylabel('Mean ' + chooseName(appType) + ' MOS')
    outPath = preOutPath+'sysUtilClient'+testPrefix+'_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


def plotParameterStudyMOSheatMap(testPrefix, appType, mbrs, gbrs, qs, maxNumCliPlot):
    print('-------------', testPrefix, '-------------')
    prePath = '../exports/extracted/mos2/'
    filenames = glob.glob(prePath+testPrefix+'*')
    print('-> There are', len(filenames), 'experiments in this parameter study.')
    filterName = 'Val'
    
    reqRunInfo = ['Q', 'M', 'C'] # Q = target QoE, M = GBR multiplier, C = MBR multiplier
    reqRunInfo.append(appType) # This will get the number of clients in experiment

    runResults = {}
    numClis = []
    minValue = 5.0

    for filename in filenames:
        fid = getFileInfo(filename, reqRunInfo)
        if fid['Q'] == qs and fid['M'] in gbrs and fid['C'] in mbrs and fid[appType] <= maxNumCliPlot:
            print('\t-> Run:', fid['name'], end=': ')
            runDict = {}
            runDict['Q'] = fid['Q'] # Target QoE in run
            runDict['M'] = fid['M'] # GBR multiplier in run
            runDict['C'] = fid['C'] # MBR multiplier in run
            runDict['numCli'] = fid[appType] # Number of clients in run
            if runDict['numCli'] not in numClis:
                numClis.append(runDict['numCli'])
            
            # Getting values
            runDF = pd.read_csv(filename)
            valDF = filterDFType(filterDFType(runDF, filterName), appType)
            meanRunVals = []

            # Get mean for each client in run first
            for col in valDF:
                if len(valDF[col].dropna().tolist()) == 0:
                    print('No MOS!', end='')
                    meanRunVals.append(1.0)
                else:
                    meanRunVals.append(statistics.mean(valDF[col].dropna().tolist()))
            # Then calculate the mean for fun based on client means
            runDict['meanVal'] = statistics.mean(meanRunVals)
            minValue = min(minValue, runDict['meanVal'])
            print('mean QoE =', runDict['meanVal'])
            runResults[fid['name']] = runDict # Store it ready to plot
    
    numClis = sorted(numClis)
    # minmax = (1.0,4.5)
    minmax = (minValue-0.05,4.5)

    # Plot the means
    # print(runResults)
    heatMap = []
    for i in range(len(mbrs)):
        heatMap.append([])
        for j in range(len(gbrs)):
            for _ in range(len(gbrs)-j):
                heatMap[i].append(0)
    xTickLbls = []
    for j in range(len(gbrs)):
        for i in range(len(gbrs)-j):
            xTickLbls.append(gbrs[j+i])
    # print(len(heatMap), len(heatMap[0]))
    fig, ax = plt.subplots(1, figsize=(len(heatMap[0])*2/3,len(heatMap)))

    maxVal = 4.5
    minVal = 1.0
    for run in runResults:
        cliIndex = numClis.index(runResults[run]['numCli'])
        gbrIndex = gbrs.index(runResults[run]['M'])
        cliOff = 0
        for i in range(len(gbrs)-cliIndex, len(gbrs)):
            cliOff += i
        xAxisIdent = cliOff + gbrIndex
        yAxisIdent = mbrs.index(runResults[run]['C'])
        # print(runResults[run]['numCli'], runResults[run]['M'], runResults[run]['C'], xAxisIdent, xTickLbls[xAxisIdent])
        heatMap[yAxisIdent][xAxisIdent] = runResults[run]['meanVal']
        maxVal = max(maxVal, runResults[run]['meanVal'])
        minVal = min(minVal, runResults[run]['meanVal'])
        # print(xAxisIdent, yAxisIdent, runResults[run]['meanVal'])
    
    # print(heatMap)

    norm = matplotlib.colors.Normalize(vmin=minVal, vmax=maxVal)
    cmap = plt.get_cmap(name='viridis',lut=1024)
    im = ax.imshow(np.array(heatMap), norm=norm, cmap=cmap, aspect='auto')
    ax.set_ylabel('MBR\nMultiplier [%]')
    ax.set_xlabel('GBR Multiplier [%]')
    divider = make_axes_locatable(plt.gca())
    cax = divider.append_axes("right", "0.5%", pad="0.5%")
    cbar = ax.figure.colorbar(im, ax=ax, norm=norm, cmap=cmap, aspect=15, cax=cax)
    cbar.ax.set_ylabel('Mos Value', rotation=-90, va="bottom")
    ticklabels = [str(1+x/2) for x in range(int((maxVal-minVal)*2)+1)]
    print(ticklabels)
    cbar.set_ticks(np.linspace(minVal, maxVal, len(ticklabels)))
    cbar.set_ticklabels(ticklabels)
    for i in range(len(heatMap)):
        print(len(heatMap), len(heatMap[i]))
    
    # Major ticks
    ax.set_yticks(np.arange(0, len(heatMap), 1))
    ax.set_xticks(np.arange(0, len(heatMap[0]), 1))

    # Labels for major ticks
    ax.set_yticklabels(mbrs)
    ax.set_xticklabels(xTickLbls)

    # Minor ticks
    ax.set_yticks(np.arange(-.5, len(heatMap), 1), minor=True)
    ax.set_xticks(np.arange(-.5, len(heatMap[0]), 1), minor=True)

    cliOff = 0
    for i in range(len(gbrs), 0, -1):
        rect = patches.Rectangle((cliOff-.44, -.47), 0.91, len(mbrs)-.06, linewidth=3, edgecolor='r', facecolor='none', zorder=100)
        ax.add_patch(rect)
        ax.text(cliOff-.5+i/2, -.75, str(numClis[len(gbrs)-i]), horizontalalignment='center')
        cliOff += i
        ax.vlines(cliOff-.5, -.5, len(heatMap)-.5, color='k')
        

    ax.grid(which='minor', color='w', linestyle='-', linewidth=2)
    # ax.minorticks_off()

    # Finish plotting
    preOutPath = '../exports/paramStudyPlots/mosHeatMap/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)
    # ax.set_ylim(minmax)
    # ax.set_xlim(-1,2*len(numClis)-1)

    # plt.xticks(ticks, labels, rotation=0)
    # plt.legend(handles=legendHandles, fontsize=25, bbox_to_anchor=(1, 1), loc='upper left')
    # plt.grid(axis='y')
    plt.tight_layout()
    # plt.ticklabel_format(style='plain')
    
    outPath = preOutPath+'sysUtilClient'+testPrefix+'_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    outPath = preOutPath+'sysUtilClient'+testPrefix+'_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    plt.close('all')
    return maxVal, minVal


def plotParameterStudyMOSheatMapAllInOne(testPrefixes, appTypes, mbrs, gbrs, qs, maxNumCliPlot, selectedGBRMBR):
    fig, axs = plt.subplots(len(testPrefixes), figsize=(10+sum([x for x in range(len(gbrs))])*2/3,(len(mbrs)-1)*len(testPrefixes)), sharex=True, sharey=True)
    count = 0
    for testPrefix, appType, selGBRMBR in zip(testPrefixes, appTypes, selectedGBRMBR):
        print('-------------', testPrefix, '-------------')
        prePath = '../exports/extracted/mos2/'
        filenames = glob.glob(prePath+testPrefix+'*')
        print('-> There are', len(filenames), 'experiments in this parameter study.')
        filterName = 'Val'
        
        reqRunInfo = ['Q', 'M', 'C'] # Q = target QoE, M = GBR multiplier, C = MBR multiplier
        reqRunInfo.append(appType) # This will get the number of clients in experiment

        runResults = {}
        numClis = []
        minValue = 5.0

        if len(filenames) == 0:
            numClis = [100, 105, 111, 117, 125, 133, 142, 153, 166, 181, 200]

        for filename in filenames:
            # print(filename)
            fid = getFileInfo(filename, reqRunInfo)
            if fid['Q'] == qs and fid['M'] in gbrs and fid['C'] in mbrs and fid[appType] <= maxNumCliPlot:
                print('\t-> Run:', fid['name'], end=': ')
                runDict = {}
                runDict['Q'] = fid['Q'] # Target QoE in run
                runDict['M'] = fid['M'] # GBR multiplier in run
                runDict['C'] = fid['C'] # MBR multiplier in run
                runDict['numCli'] = fid[appType] # Number of clients in run
                if runDict['numCli'] not in numClis:
                    numClis.append(runDict['numCli'])
                
                # Getting values
                runDF = pd.read_csv(filename)
                valDF = filterDFType(filterDFType(runDF, filterName), appType)
                meanRunVals = []

                # Get mean for each client in run first
                for col in valDF:
                    if len(valDF[col].dropna().tolist()) == 0:
                        print('No MOS!', end='')
                        meanRunVals.append(1.0)
                    else:
                        meanRunVals.append(statistics.mean(valDF[col].dropna().tolist()))
                # Then calculate the mean for fun based on client means
                runDict['meanVal'] = statistics.mean(meanRunVals)
                minValue = min(minValue, runDict['meanVal'])
                print('mean QoE =', runDict['meanVal'])
                runResults[fid['name']] = runDict # Store it ready to plot
        
        numClis = sorted(numClis)
        print(numClis)
        # minmax = (1.0,4.5)
        minmax = (minValue-0.05,4.5)

        # Plot the means
        # print(runResults)
        heatMap = []
        for i in range(len(mbrs)):
            heatMap.append([])
            for j in range(len(gbrs)):
                for _ in range(len(gbrs)-j):
                    heatMap[i].append(0)
        xTickLbls = []
        for j in range(len(gbrs)):
            for i in range(len(gbrs)-j):
                xTickLbls.append(gbrs[j+i])
        # print(len(heatMap), len(heatMap[0]))
        # fig, ax = plt.subplots(1, figsize=(len(heatMap[0])*2/3,len(heatMap)))

        maxVal = 4.5
        minVal = 1.0
        for run in runResults:
            cliIndex = numClis.index(runResults[run]['numCli'])
            gbrIndex = gbrs.index(runResults[run]['M'])
            cliOff = 0
            for i in range(len(gbrs)-cliIndex, len(gbrs)):
                cliOff += i
            xAxisIdent = cliOff + gbrIndex
            yAxisIdent = mbrs.index(runResults[run]['C'])
            # print(runResults[run]['numCli'], runResults[run]['M'], runResults[run]['C'], xAxisIdent, xTickLbls[xAxisIdent])
            heatMap[yAxisIdent][xAxisIdent] = runResults[run]['meanVal']
            maxVal = max(maxVal, runResults[run]['meanVal'])
            minVal = min(minVal, runResults[run]['meanVal'])
            # print(xAxisIdent, yAxisIdent, runResults[run]['meanVal'])
        
        # print(heatMap)

        norm = matplotlib.colors.Normalize(vmin=minVal, vmax=maxVal)
        cmap = plt.cm.get_cmap(name='summer',lut=1024)
        im = axs[count].imshow(np.array(heatMap), norm=norm, cmap=cmap, aspect='auto')
        # axs[count].set_ylabel('MBR\nMultiplier [%]')
        # axs[count].set_xlabel('GBR Multiplier [%]')
        # divider = make_axes_locatable(plt.gca())
        # cax = divider.append_axes("right", "0.5%", pad="0.5%")
        cbar = axs[count].figure.colorbar(im, ax=axs[count], norm=norm, cmap=cmap, aspect=15, pad=0.01)
        cbar.ax.set_ylabel(chooseName(appType)+'\nMOS Score', rotation=-90, va="bottom")
        ticklabels = [str(1+x/2) for x in range(int((maxVal-minVal)*2)+1)]
        # print(ticklabels)
        cbar.set_ticks(np.linspace(minVal, maxVal, len(ticklabels)))
        cbar.set_ticklabels(ticklabels)
        # for i in range(len(heatMap)):
        #     print(len(heatMap), len(heatMap[i]))

        axs[count].scatter(sum([len(gbrs)-x for x in range(0, gbrs.index(selGBRMBR[0]))]), mbrs.index(selGBRMBR[1]), s=160.0, marker='o', c='maroon')
    
        # Major ticks
        axs[count].set_yticks(np.arange(0, len(heatMap), 1))
        axs[count].set_xticks(np.arange(0, len(heatMap[0]), 1))

        # Labels for major ticks
        axs[count].set_yticklabels(mbrs)
        axs[count].set_xticklabels(xTickLbls)

        # Minor ticks
        axs[count].set_yticks(np.arange(-.5, len(heatMap), 1), minor=True)
        axs[count].set_xticks(np.arange(-.5, len(heatMap[0]), 1), minor=True)

        cliOff = 0
        for i in range(len(gbrs), 0, -1):
            rect = patches.Rectangle((cliOff-.4, -.47), 0.8, len(mbrs)-.06, linewidth=4.0, edgecolor='maroon', facecolor='none', zorder=100)
            axs[count].add_patch(rect)
            if count == 0: 
                axs[count].text(cliOff-.5+i/2, -.75, str(numClis[len(gbrs)-i]), horizontalalignment='center', rotation=90)
            cliOff += i
            axs[count].vlines(cliOff-.5, -.5, len(heatMap)-.5, color='k', linewidth=6.0)
        

        axs[count].grid(which='minor', color='w', linestyle='-', linewidth=2)
        count+=1
    # ax.minorticks_off()
    # Finish plotting
    preOutPath = '../exports/paramStudyPlots/mosHeatMap/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)
    fig.text(0.095, 0.5, 'MBR Multiplier [%]', va='center', rotation='vertical')
    # fig.text(0.5, 0, 'GBR Multiplier [%]', va='center', rotation='horizontal')
    # plt.ylabel('MBR Multiplier [%]')
    plt.xlabel('GBR Multiplier [%]')
    plt.xticks(rotation=90)

    outPath = preOutPath+'parameterStudyMOSall_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    outPath = preOutPath+'parameterStudyMOSall_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    plt.close('all')
    return maxVal, minVal


def plotParameterStudyMOSheatMapAllInOneSmall(testPrefixes, appTypes, mbrs, gbrs, qs, maxNumCliPlot, selectedGBRMBR):
    fig, axs = plt.subplots(len(testPrefixes), figsize=(10+sum([x for x in range(len(gbrs))])*1/5,(len(mbrs)-1)*len(testPrefixes)), sharex=True, sharey=True)
    count = 0
    print(testPrefixes)
    for testPrefix, appType, selGBRMBR in zip(testPrefixes, appTypes, selectedGBRMBR):
        print('-------------', testPrefix, '-------------')
        print("-------------",appType,"-----------")
        print("--------------",selGBRMBR,"------------")
        prePath = '../exports/extracted/mos2/'
        filenames = glob.glob(prePath+testPrefix+'*')
        print('-> There are', len(filenames), 'experiments in this parameter study.')
        filterName = 'Val'
        
        reqRunInfo = ['Q', 'M', 'C'] # Q = target QoE, M = GBR multiplier, C = MBR multiplier
        reqRunInfo.append(appType) # This will get the number of clients in experiment

        runResults = {}
        numClis = []
        minValue = 5.0

        for filename in filenames:
            fid = getFileInfo(filename, reqRunInfo)
            # print(int(10000/fid['M']))
            if fid['Q'] == qs and fid['M'] in gbrs and fid['C'] in mbrs and fid[appType] == int(10000/fid['M']):
                print('\t-> Run:', fid['name'].split('-')[0].split('Study')[1], 'C =', fid['C'], 'M =', fid['M'], end=': ')
                runDict = {}
                runDict['Q'] = fid['Q'] # Target QoE in run
                runDict['M'] = fid['M'] # GBR multiplier in run
                runDict['C'] = fid['C'] # MBR multiplier in run
                runDict['numCli'] = fid[appType] # Number of clients in run
                if runDict['numCli'] not in numClis:
                    numClis.append(runDict['numCli'])
                
                # Getting values
                runDF = pd.read_csv(filename)
                valDF = filterDFType(filterDFType(runDF, filterName), appType)
                meanRunVals = []

                # Get mean for each client in run first
                for col in valDF:
                    if len(valDF[col].dropna().tolist()) == 0:
                        print('No MOS!', end='')
                        meanRunVals.append(1.0)
                    else:
                        meanRunVals.append(statistics.mean(valDF[col].dropna().tolist()))
                # Then calculate the mean for fun based on client means
                runDict['meanVal'] = statistics.mean(meanRunVals)
                # runDict['meanVal'] = np.percentile(meanRunVals, 25)
                # runDict['meanVal'] = min(meanRunVals)
                # runDict['meanVal'] = max(meanRunVals)
                #statistics. median(meanRunVals)
                minValue = min(minValue, runDict['meanVal'])
                print('mean QoE =', runDict['meanVal'])
                runResults[fid['name']] = runDict # Store it ready to plot
        
        numClis = sorted(numClis)
        print(numClis)
        # minmax = (1.0,4.5)
        minmax = (minValue-0.05,4.5)

        # Plot the means
        print(runResults)
        target = 3.5
        closestVal = 5
        runName = ''
        runNameClosestAbove = ''
        closValMBRmult = {}
        closNamMBRmult = {}
        for run in runResults:
            cMulti = run.split('_')[4]
            if cMulti in closValMBRmult:
                if runResults[run]['meanVal'] >= 3.5 and runResults[run]['meanVal'] < closValMBRmult[cMulti]:
                    closValMBRmult[cMulti] = runResults[run]['meanVal']
                    closNamMBRmult[cMulti] = run
            else:
                if runResults[run]['meanVal'] > 3.5:
                    closValMBRmult[cMulti] = runResults[run]['meanVal']
                    closNamMBRmult[cMulti] = run

        
        
        heatMap = []
        for i in range(len(mbrs)):
            heatMap.append([])
            for _ in range(len(gbrs)):
                heatMap[i].append(0)
        xTickLbls = []
        for j in range(len(gbrs)):
            # for i in range(len(gbrs)-j):
            xTickLbls.append(gbrs[j])
        # print(len(heatMap), len(heatMap[0]))
        # fig, ax = plt.subplots(1, figsize=(len(heatMap[0])*2/3,len(heatMap)))

        maxVal = 4.5
        minVal = 1.0
        for run in runResults:
            # cliIndex = numClis.index(runResults[run]['numCli'])
            gbrIndex = gbrs.index(runResults[run]['M'])
            # cliOff = 0
            # for i in range(len(gbrs)-cliIndex, len(gbrs)):
            #     cliOff += i
            # xAxisIdent = cliOff + gbrIndex
            xAxisIdent = gbrIndex
            yAxisIdent = mbrs.index(runResults[run]['C'])
            # print(runResults[run]['numCli'], runResults[run]['M'], runResults[run]['C'], xAxisIdent, xTickLbls[xAxisIdent])
            heatMap[yAxisIdent][xAxisIdent] = runResults[run]['meanVal']
            maxVal = max(maxVal, runResults[run]['meanVal'])
            minVal = min(minVal, runResults[run]['meanVal'])
            # print(xAxisIdent, yAxisIdent, runResults[run]['meanVal'])
        
        # print(heatMap)

        norm = matplotlib.colors.Normalize(vmin=minVal, vmax=maxVal)
        cmap = plt.cm.get_cmap(name='viridis',lut=1024)
        im = axs[count].imshow(np.array(heatMap), norm=norm, cmap=cmap, aspect='auto')
        # axs[count].set_ylabel('MBR\nMultiplier [%]')
        # axs[count].set_xlabel('GBR Multiplier [%]')
        # divider = make_axes_locatable(plt.gca())
        # cax = divider.append_axes("right", "0.5%", pad="0.5%")
        cbar = axs[count].figure.colorbar(im, ax=axs[count], norm=norm, cmap=cmap, aspect=15, pad=0.01)
        cbar.ax.set_ylabel(chooseName(appType)+' MOS', rotation=-90, va="bottom")
        ticklabels = [str(1+x/2) for x in range(int((maxVal-minVal)*2)+1)]
        # print(ticklabels)
        cbar.set_ticks(np.linspace(minVal, maxVal, len(ticklabels)))
        cbar.set_ticklabels(ticklabels)
        # for i in range(len(heatMap)):
        #     print(len(heatMap), len(heatMap[i]))

        axs[count].scatter(gbrs.index(selGBRMBR[0]), mbrs.index(selGBRMBR[1]), s=160.0, marker='o', c='maroon')
    
        #if len(runResults)>0:axs[count].scatter(gbrs.index(runResults[runNameClosestAbove]['M']), mbrs.index(runResults[runNameClosestAbove]['C']), s=140.0, marker='X', c='red', zorder=500)
        if len(runResults)>0 and runNameClosestAbove!='':
            axs[count].text(gbrs.index(runResults[runNameClosestAbove]['M']), mbrs.index(runResults[runNameClosestAbove]['C']), str(round(runResults[runNameClosestAbove]['meanVal'],2)), ha='center', va='center', c='maroon', zorder=500)
            axs[count].text(gbrs.index(runResults[runNameSelected]['M']), mbrs.index(runResults[runNameSelected]['C']), str(round(runResults[runNameSelected]['meanVal'],2)), ha='center', va='center', c='green', zorder=600)

        elif len(runResults)>0 and runName!='':
            axs[count].text(gbrs.index(runResults[runName]['M']), mbrs.index(runResults[runName]['C']), str(round(runResults[runName]['meanVal'],2)), ha='center', va='center', c='maroon', zorder=500)
        # if len(runResults)>0:axs[count].scatter(gbrs.index(runResults[runName]['M']), mbrs.index(runResults[runName]['C']), s=200.0, marker='s', c='black', zorder=400)
        # if len(runResults)>0:axs[count].text(gbrs.index(runResults[runName]['M']), mbrs.index(runResults[runName]['C']), str(round(runResults[runName]['meanVal'],2)), ha='center', va='center', c='green', zorder=400)
        if len(runResults)>0:
            for run in runResults:
                if runResults[run]['meanVal'] < 1.5:
                    axs[count].text(gbrs.index(runResults[run]['M']), mbrs.index(runResults[run]['C']), str(round(runResults[run]['meanVal'],2)), ha='center', va='center', c='white', zorder=300)
                else:
                    axs[count].text(gbrs.index(runResults[run]['M']), mbrs.index(runResults[run]['C']), str(round(runResults[run]['meanVal'],2)), ha='center', va='center', c='white', zorder=300)


            # for entry in closNamMBRmult:
            #     runName = closNamMBRmult[entry]
            #     axs[count].text(gbrs.index(runResults[runName]['M']), mbrs.index(runResults[runName]['C']), str(round(runResults[runName]['meanVal'],2)), ha='center', va='center')
                # axs[count].scatter(gbrs.index(runResults[runName]['M']), mbrs.index(runResults[runName]['C']), s=100.0, marker='D', c='orange', zorder=700)
        # Major ticks
        axs[count].set_yticks(np.arange(0, len(heatMap), 1))
        axs[count].set_xticks(np.arange(0, len(heatMap[0]), 1))

        # Labels for major ticks
        axs[count].set_yticklabels(mbrs)
        axs[count].set_xticklabels(xTickLbls)

        # Minor ticks
        axs[count].set_yticks(np.arange(-.5, len(heatMap), 1), minor=True)
        axs[count].set_xticks(np.arange(-.5, len(heatMap[0]), 1), minor=True)

        # cliOff = 0
        # for i in range(len(gbrs), 0, -1):
        #     rect = patches.Rectangle((cliOff-.4, -.47), 0.8, len(mbrs)-.06, linewidth=4.0, edgecolor='maroon', facecolor='none', zorder=100)
        #     axs[count].add_patch(rect)
        #     if count == 0: 
        #         axs[count].text(cliOff-.5+i/2, -.75, str(numClis[len(gbrs)-i]), horizontalalignment='center', rotation=90)
        #     cliOff += i
        #     axs[count].vlines(cliOff-.5, -.5, len(heatMap)-.5, color='k', linewidth=6.0)


        axs[count].grid(which='minor', color='w', linestyle='-', linewidth=2)
        count+=1
    # ax.minorticks_off()
    # Finish plotting
    preOutPath = '../exports/paramStudyPlots/mosHeatMap/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)
    fig.text(0.055, 0.5, 'MBR Multiplier [%]', va='center', rotation='vertical')
    # fig.text(0.5, 0, 'GBR Multiplier [%]', va='center', rotation='horizontal')
    # plt.ylabel('MBR Multiplier [%]')
    plt.xlabel('GBR Multiplier [%]')
    plt.xticks(rotation=0)

    outPath = preOutPath+'parameterStudyMOSallSmall_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'_older.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    outPath = preOutPath+'parameterStudyMOSallSmall_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'_older.pdf'
    fig.savefig(outPath, dpi=100, bbox_inches='tight')
    plt.close('all')
    return maxVal, minVal


############################################################################################

testNames = ["parameterStudycVIP10ms-","parameterStudycVIP-"] # Name prefix of the QoE test
# testNames = ['parameterStudyVoD-','parameterStudyLive-','parameterStudySecureShell-','parameterStudyVoIP-', 'parameterStudyFileDownloadFix'] # Name prefix of the QoE test
# testNames = ['parameterStudyVoIPV2'] # Name prefix of the QoE test
targetQoEs = [35] # Target QoEs
mbrs = [100,125,150,175,200]
gbrs = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50]
sliNamess = [['none']]
clients = ['cVIP',"cVIP"]
# clients = ['VIP']
# maxNumCliPlot = [142,200]
maxNumCliPlot = [200]
# selectedGBRMBR = [[90,125],[80,150],[100,100],[70,200],[100,150]]
selectedGBRMBR = [[85,125],[60,150]]
maxi = 0
mini = 5
#plotParameterStudyMOSheatMapAllInOne(testNames, clients, mbrs, gbrs, targetQoEs[0], maxNumCliPlot[0], selectedGBRMBR)
plotParameterStudyMOSheatMapAllInOneSmall(testNames, clients, mbrs, gbrs, targetQoEs[0], maxNumCliPlot[0], selectedGBRMBR)
#for testName, client in zip(testNames, clients):
#     for tQ in targetQoEs:
#         for numCli in maxNumCliPlot:
#             print(testName)
#             print(client)
#             plotParameterStudyMOS(testName, client, mbrs, gbrs, tQ, numCli)
#             maxVal, minVal = plotParameterStudyMOSheatMap(testName, client, mbrs, gbrs, tQ, numCli)
#             for mbr in mbrs:
#                 plotParameterStudyMOS(testName, client, [mbr], gbrs, tQ, numCli)
