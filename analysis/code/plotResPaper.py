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
import matplotlib.patches as patches

import re

import glob

font = {'weight' : 'normal',
        'size'   : 35}

matplotlib.rc('font', **font)
matplotlib.rc('lines', linewidth=5.0)
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
    if dataName == 'hostVID':
        return 'VoD'
    elif dataName == 'hostFDO':
        return 'FD'
    elif dataName == 'hostSSH':
        return 'SSH'
    elif dataName == 'hostVIP':
        return 'VoIP'
    elif dataName == 'hostcVIP':
        return 'crit VoIP'    
    elif dataName == 'hostLVD':
        return 'Live'

colormap = plt.get_cmap('Set1').colors
appTypeToColor = {
    'VID' : colormap[0],
    'LVD' : colormap[1], 
    'FDO' : colormap[2], 
    'SSH' : colormap[3], 
    'VIP' : colormap[4],
    'cVIP' : colormap[5],
    'all' : 'black'
}

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

def plotQoSFMOS(testPrefix, appType, mbrs, gbrs, qs, maxNumCliPlot):
    print('-------------', testPrefix, '-------------')
    prePath = '../exports/extracted/mos2/'
    filenames = glob.glob(prePath+testPrefix+'-*')
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
    plt.ylabel('Mean ' + chooseName('host'+appType) + ' MOS')
    outPath = preOutPath+'sysUtilClient'+testPrefix+'_M'+str(gbrs)+'_C'+str(mbrs)+'_maxNumClis'+str(maxNumCliPlot)+'.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')



def plotQoEcomp(testPrefix, subconfNames, appTypes, mbrs, gbr, q):
    print('-------------', testPrefix, '-------------')
    prePath = '../exports/extracted/mos2/'
    filenames = glob.glob(prePath+testPrefix+'*')
    # print(filenames)
    # fig, ax = plt.subplots(1, figsize=(16,12))
    filterName = 'Val'

    reqRunInfo = ['Q', 'M', 'C']
    reqRunInfo.extend(appTypes)

    runs = {}

    for filename in filenames:
        fid = getFileInfo(filename, reqRunInfo)
        if fid['Q'] == q and fid['M'] == gbr and fid['C'] in mbrs:
            sN = ''
            for subN in subconfNames:
                if subN in fid['name']:
                    sN = subN
                    break
            runIdent = 'Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C']) + '_' + sN
            if runIdent not in runs:
                runs[runIdent] = {}
            print('---', fid['name'], '---')
            runDF = pd.read_csv(filename)
            for aT in appTypes:
                if int(fid[aT]) != 0:
                    # valIdent = 'Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C']) + '_' + aT
                    # print(valIdent)
                    valDF = filterDFType(filterDFType(runDF, filterName), aT)
                    meanCliVals = []
                    for col in valDF:
                        meanCliVals.append(statistics.mean(valDF[col].dropna().tolist()))
                    # print(valIdent, statistics.mean(meanCliVals))
                    runs[runIdent][aT] = statistics.mean(meanCliVals)
    # print(runs)
    baseValues = {}

    for run in runs:
        if 'Base' in run:
            name = run.split('_Base')[0]
            baseValues[name] = runs[run]
    
    # print(baseValues)
    fig, axs = plt.subplots(len(subconfNames)-1, figsize=(16,12), sharex=True, sharey=True)

    compVals = {}

    for run in runs:
        if 'Base' not in run:
            baseName = run.split('_5')[0]
            cValsRun = {}
            for aT in appTypes:
                # cValsRun[aT] = baseValues[baseName][aT] - runs[run][aT]
                cValsRun[aT] = runs[run][aT] - baseValues[baseName][aT]
            compVals[run] = cValsRun
    print(compVals)
    
    appImprVsMBR = {}
    appImprVsMBRxAxis = {}

    for sN in subconfNames:
        if 'Base' not in sN:
            appImprVsMBR[sN] = {}
            appImprVsMBRxAxis[sN] = {}
            for aT in appTypes:
                appImprVsMBR[sN][aT] = []
                appImprVsMBRxAxis[sN][aT] = []
    print(appImprVsMBR)

    for aT in appTypes:
        for cVal in compVals:
            print(aT, cVal, compVals[cVal][aT], cVal.split('_')[-1])
            appImprVsMBR[cVal.split('_')[-1]][aT].append(compVals[cVal][aT])
            appImprVsMBRxAxis[cVal.split('_')[-1]][aT].append(int(cVal.split('_')[2][1:]))
    print(appImprVsMBR)

    for sN in subconfNames:
        if sN != 'Base':
            for aT in appTypes:
                x = sorted(appImprVsMBRxAxis[sN][aT])
                y = [x for _, x in sorted(zip(appImprVsMBRxAxis[sN][aT], appImprVsMBR[sN][aT]))]
                axs[subconfNames.index(sN)-1].plot(x, y, 'o-', color=appTypeToColor[aT], label=chooseName('host'+aT))
            axs[subconfNames.index(sN)-1].title.set_text(sN)
            axs[subconfNames.index(sN)-1].grid(axis='both')
    
    plt.xlabel('MBR setting [%]')
    # plt.ylabel("Relative MOS Score")
    fig.text(0, 0.5, 'Average MOS Improvement', va='center', rotation='vertical')
    plt.tight_layout()


        
    #     runInfo = run.split('_')
    #     rMbr = int(runInfo[2][1:])
    #     rGbr = int(runInfo[1][1:])
    #     rQ = int(runInfo[0][1:])/10
    #     print(runInfo, rMbr, rGbr, rQ)
    #     for aT in appTypes:
    #         xPosition = appTypes.index(aT)
    #         data = runs[run][aT]
    #         axs[mbrs.index(rMbr)].boxplot(data, positions=[xPosition], notch=False, patch_artist=True,
    #                                       boxprops=dict(facecolor=appTypeToColor[aT], color='black'),
    #                                       capprops=dict(color='black'),
    #                                       whiskerprops=dict(color='black'),
    #                                       flierprops=dict(color='black', markeredgecolor='black'),
    #                                       widths=0.75, zorder=0)
    #     axs[mbrs.index(rMbr)].title.set_text('MBR = '+str(rMbr)+'%')
    #     axs[mbrs.index(rMbr)].grid(axis='y')
    #     axs[mbrs.index(rMbr)].set_ylim(2.9,4.4)
    #     axs[mbrs.index(rMbr)].set_xlim(-0.5,len(appTypes)+0.5)
    #     axs[mbrs.index(rMbr)].set_xticks([])

    # for aT in appTypes:
    #     axs[-1].bar(-10,5,color=appTypeToColor[aT], edgecolor='black', label=chooseName('host'+aT))
    axs[0].legend(fontsize=25, bbox_to_anchor=(1, 1), loc='upper left')

    preOutPath = '../exports/plots/flows/mosComp/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)
    # axs[0].set_ylabel("Relative MOS Score")

    # plt.suptitle(testPrefix)
    
    outPath = preOutPath+'mos'+testPrefix+'_Q'+str(q)+'_C'+str(mbrs)+'_M'+str(gbr)+'.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')


def plotQoE(testPrefix, appTypes, mbrs, gbr, q):
    print('-------------', testPrefix, '-------------')
    prePath = '../exports/extracted/mos2/'
    filenames = glob.glob(prePath+testPrefix+'*')
    # print(filenames)
    # fig, ax = plt.subplots(1, figsize=(16,12))
    filterName = 'Val'

    reqRunInfo = ['Q', 'M', 'C']
    reqRunInfo.extend(appTypes)

    runs = {}

    for filename in filenames:
        fid = getFileInfo(filename, reqRunInfo)
        if fid['Q'] == q and fid['M'] == gbr and fid['C'] in mbrs:
            runIdent = 'Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C'])
            if runIdent not in runs:
                runs[runIdent] = {}
            print('---', fid['name'], '---')
            runDF = pd.read_csv(filename)
            for aT in appTypes:
                if int(fid[aT]) != 0:
                    # valIdent = 'Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C']) + '_' + aT
                    # print(valIdent)
                    valDF = filterDFType(filterDFType(runDF, filterName), aT)
                    meanCliVals = []
                    for col in valDF:
                        meanCliVals.append(statistics.mean(valDF[col].dropna().tolist()))
                    # print(valIdent, statistics.mean(meanCliVals))
                    runs[runIdent][aT] = meanCliVals
    # print(runs)

    fig, axs = plt.subplots(1,len(runs), figsize=(len(runs)*6,12), sharex=True, sharey=True)

    for run in runs:
        runInfo = run.split('_')
        rMbr = int(runInfo[2][1:])
        rGbr = int(runInfo[1][1:])
        rQ = int(runInfo[0][1:])/10
        print(runInfo, rMbr, rGbr, rQ)
        ax = axs
        if len(runs) > 1:
            ax = axs[mbrs.index(rMbr)]
        for aT in appTypes:
            xPosition = appTypes.index(aT)
            data = runs[run][aT]
            ax.boxplot(data, positions=[xPosition], notch=True, patch_artist=True,
                                          boxprops=dict(facecolor=appTypeToColor[aT], color=appTypeToColor[aT]),
                                          capprops=dict(color=appTypeToColor[aT]),
                                          whiskerprops=dict(color=appTypeToColor[aT]),
                                          flierprops=dict(color='black', markeredgecolor='black'),
                                          showmeans=True,
                                          widths=0.75, zorder=0)
        ax.title.set_text('MBR = '+str(rMbr)+'%')
        ax.grid(axis='y')
        if 'AdmCon' in testPrefix:
            ax.set_ylim(1.5,4.5)
        else:
            ax.set_ylim(2.9,4.4)
        ax.set_xlim(-0.5,len(appTypes)+0.5)
        ax.set_xticks([])

    ax = axs
    if len(runs) > 1:
        ax = axs[-1]

    for aT in appTypes:
        ax.bar(-10,5,color=appTypeToColor[aT], edgecolor='black', label=chooseName('host'+aT))
    ax.legend(fontsize=25, bbox_to_anchor=(1, 1), loc='upper left')


    ax = axs
    if len(runs) > 1:
        ax = axs[0]
    preOutPath = '../exports/plots/flows/mos/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)
    ax.set_ylabel("MOS")

    plt.suptitle(testPrefix)
    
    outPath = preOutPath+'mos'+testPrefix+'_Q'+str(q)+'_C'+str(mbrs)+'_M'+str(gbr)+'.png'
    fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
    plt.close('all')

# mbrToGray = {
#     'C100' : '#e6e6e6',
#     'C125' : '#bfbfbf',
#     'C150' : '#999999',
#     'C175' : '#737373',
#     'C200' : '#4d4d4d'
# }

mbrToGray = {
    'C100' : '#e6e6e6',
    'C125' : '#cccccc',
    'C150' : '#b3b3b3',
    'C175' : '#999999',
    'C200' : '#808080'
}

mbrToLighterGray = {
    'C100' : '#f2f2f2',
    'C125' : '#d9d9d9',
    'C150' : '#bfbfbf',
    'C175' : '#a6a6a6',
    'C200' : '#8c8c8c'
}

def plotQoEMultiExperiment(testNames, appTypes, tQoE, descriptors):
    font = {'weight' : 'normal',
        'size'   : 50}
    matplotlib.rc('font', **font)
    prePath = '../exports/extracted/mos2/'
    runs = {}
    runCliNum = {}
    fig, ax = plt.subplots(1, figsize=(55,11))

    for testName in testNames:
        print('-------------', testName, '-------------')
        filenames = glob.glob(prePath+testName+'*')
        # print(filenames)
        filterName = 'Val'

        reqRunInfo = ['Q', 'M', 'C']
        reqRunInfo.extend(appTypes)
        runs[testName] = {}
        runCliNum[testName] = {}


        for filename in filenames:
            fid = getFileInfo(filename, reqRunInfo)
            # print(fid)
            runIdent = testName + '_Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C'])
            if runIdent not in runs[testName]:
                runs[testName][runIdent] = {}
                runCliNum[testName][runIdent] = int(fid['name'].split('_')[5])
            elif 'NoHTB' in fid['name']:
                runCliNum[testName][runIdent] += int(fid['name'].split('_')[5])
                
            print('---', fid['name'], '---')
            runDF = pd.read_csv(filename)
            for aT in appTypes:
                if int(fid[aT]) != 0:
                    # valIdent = 'Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C']) + '_' + aT
                    # print(valIdent)
                    valDF = filterDFType(filterDFType(runDF, filterName), aT)
                    meanCliVals = []
                    for col in valDF:
                        meanCliVals.append(statistics.mean(valDF[col].dropna().tolist()))
                    # print(valIdent, statistics.mean(meanCliVals))
                    runs[testName][runIdent][aT] = meanCliVals

    c2Offset = 1
    mS = 18
    mr = 'o'

    ylims = (2.0,4.5)
    confInt = 0.95
    ticks = []
    labels = []
    # supTicks = []
    c1 = c2Offset
    for test in runs:
        minT = c1
        for run in sorted(runs[test]):
            print(run)
            c2 = c2Offset
            allVals = []
            for aT in appTypes:
                allVals.extend(runs[test][run][aT])
                li, hi = stats.t.interval(confInt, len(runs[test][run][aT])-1, loc=np.mean(runs[test][run][aT]), scale=stats.sem(runs[test][run][aT]))
                print(test, run, aT, statistics.mean(runs[test][run][aT]))
                ax.errorbar(c1+c2+c2Offset, statistics.mean(runs[test][run][aT]), yerr=[[statistics.mean(runs[test][run][aT])-li],[hi-statistics.mean(runs[test][run][aT])]], color=appTypeToColor[aT], marker=mr, linestyle='', markersize=mS, capsize=mS/2, zorder=15)
                c2 += c2Offset
            li, hi = stats.t.interval(confInt, len(allVals)-1, loc=np.mean(allVals), scale=stats.sem(allVals))
            print(test, run, 'all', statistics.mean(allVals))
            ax.errorbar(c1+c2+c2Offset, statistics.mean(allVals), yerr=[[statistics.mean(allVals)-li],[hi-statistics.mean(allVals)]], color=appTypeToColor['all'], marker='s', linestyle='', markersize=mS, capsize=mS/2, zorder=14)
            c2 += c2Offset
            ticks.append(c1 + (c2+2*c2Offset)/2)
            labels.append(runCliNum[test][run])
            # if 'best' not in test and 'qoe' not in test:
            #     labels.append(run.split('_')[-1][1:])
            # else:
            #     labels.append('')
            if 'qosFlows' in run:
                rect = patches.Rectangle((c1, ylims[0]), c2+2*c2Offset, ylims[1]-ylims[0], facecolor=mbrToGray[run.split('_')[-1]], zorder=1, fill=True)
                ax.add_patch(rect)
                # ax.text(c1 + (c2+2*c2Offset)/2, ylims[0]+0.1, s=run.split('_')[-1][1:]+'%', rotation=90, horizontalalignment='center', bbox=dict(boxstyle="round", ec='black', fc='#e6e6e6',pad=0.2))
                ax.text(c1 + (c2+2*c2Offset)/2, ylims[0]+0.1, s=run.split('_')[-1][1:]+'%', rotation=0, horizontalalignment='center', bbox=dict(boxstyle="round", ec='black', fc=mbrToLighterGray[run.split('_')[-1]],pad=0.2), fontsize=44, zorder=10)
            c1 = c1+c2+2*c2Offset
            if 'qosFlows' in run and run.split('_')[-1] != 'C200': ax.vlines(c1, ymin=ylims[0], ymax=ylims[1], colors='black', linestyles='dotted', zorder=3)
        ax.vlines(c1, ymin=ylims[0], ymax=ylims[1], colors='black', linestyles='solid', zorder=3)
        ax.text(minT + (c1-minT)/2,ylims[1]+0.02, s=descriptors[testNames.index(test)], horizontalalignment='center', rotation=0, zorder=10, fontdict = {'variant': 'small-caps'})
        # supTicks.append(minT + (c1-minT)/2)

    for aT in appTypes:
        ax.errorbar(-5, 10, yerr=1, color=appTypeToColor[aT], marker=mr, linestyle='', markersize=mS, label=chooseName('host'+aT), capsize=mS/2)
    ax.errorbar(-5, 10, yerr=1, color=appTypeToColor['all'], marker='s', linestyle='', markersize=mS, label='All', capsize=mS/2)
        
    ax.hlines(tQoE, c2Offset, c1, colors='maroon', linestyles='dashed')
    preOutPath = '../exports/flowsPlotsPaper/mos/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)

    plt.xticks(ticks, labels, rotation=45)
    plt.ylim(ylims)
    plt.xlim(c2Offset,c1)
    plt.ylabel('Average MOS')
    plt.xlabel('Number of Admitted Clients')
    # plt.legend(fontsize=37, bbox_to_anchor=(1, 0), loc='lower right', framealpha=1.0)
    # plt.legend(fontsize=45, bbox_to_anchor=(1.0, -0.26), loc='upper right', framealpha=1.0, ncol=6)
    plt.legend(fontsize=45, bbox_to_anchor=(1.0, 1.035), loc='upper left', framealpha=1.0, ncol=1)

    plt.grid(which='both', axis='y')

    outPath = preOutPath+'mosCI_'+str(testNames)
    fig.savefig(outPath+'.png', dpi=100, bbox_inches='tight', format='png')
    fig.savefig(outPath+'.pdf', dpi=100, bbox_inches='tight')
    fig.savefig(preOutPath+'../mosCI_2.pdf', dpi=100, bbox_inches='tight')

    plt.close('all')


appToMarker = {
    'VID' : 'o',
    'LVD' : 'o', 
    'FDO' : 'o', 
    'SSH' : 'o', 
    'VIP' : 'o',
    'cVIP' : 'o',
    'all' : 's'
}

def plotSysUtilMultiExperiment(testNames, appTypes, descriptors, resToSli):
    font = {'weight' : 'normal',
        'size'   : 50}
    matplotlib.rc('font', **font)
    prePath = '../exports/extracted/throughputs/'
    runs = {}
    runCliNum = {}
    fig, ax = plt.subplots(1, figsize=(55,11))

    for testName in testNames:
        print('-------------', testName, '-------------')
        filenames = glob.glob(prePath+testName+'*Downlink*')
        # print(filenames)
        filterName = 'Throughput'

        reqRunInfo = ['Q', 'M', 'C']
        reqRunInfo.extend(appTypes)
        runs[testName] = {}
        runCliNum[testName] = {}

        for filename in filenames:
            fid = getFileInfo(filename, reqRunInfo)
            # print(fid)
            runIdent = testName + '_Q' + str(fid['Q']) + '_M' + str(fid['M']) + '_C' + str(fid['C'])
            print("---------------------")
            print(runIdent)
            print(runs[testName])
            if runIdent not in runs[testName]:
                runs[testName][runIdent] = {}
                for aT in resToSli:
                    runs[testName][runIdent][aT] = [0 for _ in range(400)]
                runCliNum[testName][runIdent] = int(fid['name'].split('_')[5])
            elif 'NoHTB' in fid['name']:
                runCliNum[testName][runIdent] += int(fid['name'].split('_')[5])
            print('---', fid['name'], '---')
            runDF = pd.read_csv(filename)
            valDF = filterDFType(filterDFType(runDF, filterName), 'resAllocLink0')
            meanSysVals = []
            for col in valDF:
                # print(col)
                meanSysVals = [100*x/resToSli['all'] for x in valDF[col].dropna().tolist()]
            runs[testName][runIdent]['all'] = [x + y for x,y in zip(runs[testName][runIdent]['all'], meanSysVals)]
            for aT in appTypes:
                if fid[aT] != 0:
                    valDF = filterDFType(filterDFType(runDF, filterName), aT)
                    for col in valDF:
                        meanCliVals = [100*x/resToSli[aT] for x in valDF[col].dropna().tolist()]
                        runs[testName][runIdent][aT] = [x + y for x,y in zip(runs[testName][runIdent][aT], meanCliVals)]

        

    c2Offset = 1
    mS = 18
    mr = 'o'

    ylims = (0,100)
    confInt = 0.95
    ticks = []
    labels = []
    # supTicks = []
    c1 = c2Offset
    for test in runs:
        minT = c1
        for run in sorted(runs[test]):
            c2 = c2Offset
            if 'bestEffort' in run or 'Base' in run: c2 += 2.5*c2Offset
            allVals = runs[test][run]
            appTypesToPlot = list(resToSli)
            if 'Slices' not in run:
                appTypesToPlot = ['all']
            for aT in appTypesToPlot:
                li, hi = stats.t.interval(confInt, len(allVals[aT])-1, loc=np.mean(allVals[aT]), scale=stats.sem(allVals[aT]))
                print(run, aT, statistics.mean(allVals[aT]))
                ax.errorbar(c1+c2+c2Offset, statistics.mean(allVals[aT]), yerr=[[statistics.mean(allVals[aT])-li],[hi-statistics.mean(allVals[aT])]], color=appTypeToColor[aT], marker=appToMarker[aT], linestyle='', markersize=mS, capsize=mS/2, zorder=15)
                c2 += c2Offset
            ticks.append(c1 + (c2+2*c2Offset)/2)
            labels.append(runCliNum[test][run])

            # if 'best' not in test and 'qoe' not in test:
            #     labels.append(run.split('_')[-1][1:])
            # else:
            #     labels.append('')
            if 'bestEffort' in run or 'Base' in run: c2 += 2.5*c2Offset

            if 'qosFlows' in run:
                rect = patches.Rectangle((c1, ylims[0]), c2+2*c2Offset, ylims[1]-ylims[0], facecolor=mbrToGray[run.split('_')[-1]], zorder=1, fill=True)
                ax.add_patch(rect)
                # ax.text(c1 + (c2+2*c2Offset)/2, ylims[0]+1.5, s=run.split('_')[-1][1:]+'%', rotation=90, backgroundcolor='#e6e6e6', horizontalalignment='center')
                yOff = ylims[0]+4.0
                # if 'NoHTB' in run:
                #     yOff += 32
                ax.text(c1 + (c2+2*c2Offset)/2, yOff, s=run.split('_')[-1][1:]+'%', rotation=0, horizontalalignment='center', bbox=dict(boxstyle="round", ec='black', fc=mbrToLighterGray[run.split('_')[-1]],pad=0.2), fontsize=44, zorder=2)
            c1 = c1+c2+2*c2Offset
            if 'qosFlows' in run and run.split('_')[-1] != 'C200': ax.vlines(c1, ymin=ylims[0], ymax=ylims[1], colors='black', linestyles='dotted', zorder=3)

        ax.vlines(c1, ymin=ylims[0], ymax=ylims[1], colors='black', linestyles='solid', zorder=3)
        ax.text(minT + (c1-minT)/2,ylims[1]+0.8, s=descriptors[testNames.index(test)], horizontalalignment='center', rotation=0, zorder=10, fontdict = {'variant': 'small-caps'})
        # supTicks.append(minT + (c1-minT)/2)

    for aT in appTypes:
        ax.errorbar(-5, 10, yerr=1, color=appTypeToColor[aT], marker=appToMarker[aT], linestyle='', markersize=mS, label=chooseName('host'+aT), capsize=mS/2)
    ax.errorbar(-5, 10, yerr=1, color=appTypeToColor['all'], marker=appToMarker['all'], linestyle='', markersize=mS, label='All', capsize=mS/2)
        
    # ax.hlines(tQoE, c2Offset, c1, colors='maroon', linestyles='dashed')
    preOutPath = '../exports/flowsPlotsPaper/sysUtil/'
    if not os.path.exists(preOutPath):
        os.makedirs(preOutPath)

    plt.xticks(ticks, labels, rotation=45)
    plt.ylim(ylims)
    plt.xlim(c2Offset,c1)
    plt.ylabel('Average Utilization [%]')
    plt.xlabel('Number of Admitted Clients')
    # plt.legend(fontsize=45, bbox_to_anchor=(1.0, -0.26), loc='upper right', framealpha=1.0, ncol=6)
    plt.legend(fontsize=45, bbox_to_anchor=(1.0, 1.035), loc='upper left', framealpha=1.0, ncol=1)
    plt.grid(which='both', axis='y')

    outPath = preOutPath+'sysUtilCI_'+str(testNames)
    fig.savefig(outPath+'.png', dpi=100, bbox_inches='tight', format='png')
    fig.savefig(outPath+'.pdf', dpi=100, bbox_inches='tight')
    fig.savefig(preOutPath+'../sysUtilCI_2.pdf', dpi=100, bbox_inches='tight')
    plt.close('all')
############################################################################################

# testNames = ['qosFlows'] # Name prefix of the QoE test
# targetQoEs = [35] # Target QoEs
# mbrs = [100,125,150,175,200]
# gbrs = [100]
# subconfNames = ['Base', '5SlicesHTB', '5SlicesNoHTB']
# clients = ['VID', 'LVD', 'FDO', 'VIP', 'SSH']
# for testName, client in zip(testNames, clients):
#     for tQ in targetQoEs:
#         for gbr in gbrs:
#             for subconfName in subconfNames:
#                 plotQoE(testName+subconfName, clients, mbrs, gbr, tQ)
#             plotQoEcomp(testName, subconfNames, clients, mbrs, gbr, tQ)

# testNames = ['qoeFlows'] # Name prefix of the QoE test
# targetQoEs = [35] # Target QoEs
# mbrs = [100]
# gbrs = [100]
# subconfNames = ['Base', '5SlicesHTB', '5SlicesNoHTB']
# clients = ['VID', 'LVD', 'FDO', 'VIP', 'SSH']
# for testName, client in zip(testNames, clients):
#     for tQ in targetQoEs:
#         for gbr in gbrs:
#             for subconfName in subconfNames:
#                 plotQoE(testName+subconfName, clients, mbrs, gbr, tQ)
#             plotQoEcomp(testName, subconfNames, clients, mbrs, gbr, tQ)

# testNames = ['bestEffort'] # Name prefix of the QoE test
# targetQoEs = [35] # Target QoEs
# mbrs = [100]
# gbrs = [100]
# subconfNames = ['AdmCon', 'NoAdmCon']
# clients = ['VID', 'LVD', 'FDO', 'VIP', 'SSH']
# for testName, client in zip(testNames, clients):
#     for tQ in targetQoEs:
#         for gbr in gbrs:
#             for subconfName in subconfNames:
#                 plotQoE(testName+subconfName, clients, mbrs, gbr, tQ)
#             # plotQoEcomp(testName, subconfNames, clients, mbrs, gbr, tQ)

# testNames = ['bestEffortAdmCon', 'bestEffortNoAdmCon', 'qosFlowsBase', 'qosFlows5SlicesNoHTB', 'qosFlows5SlicesHTB', 'qoeFlowsBase', 'qoeFlows5SlicesNoHTB', 'qoeFlows5SlicesHTB']
# testNames = ['bestEffortAdmCon', 'bestEffortNoAdmCon', 'qosFlowsV2Base', 'qosFlowsV25SlicesNoHTB', 'qosFlowsV25SlicesHTB', 'qoeFlowsV2Base', 'qoeFlowsV25SlicesNoHTB', 'qoeFlowsV25SlicesHTB']
# testNames = ['bestEffortAdmCon', 'bestEffortNoAdmCon', 'qosFlowsV3Base', 'qosFlowsV35SlicesNoHTB', 'qosFlowsV35SlicesHTB', 'qoeFlowsV3Base', 'qoeFlowsV35SlicesNoHTB', 'qoeFlowsV35SlicesHTB']
testNames = ['bestEffortAdmConV5', 'bestEffortNoAdmConV5', 'qosFlowsV5Base', 'qosFlowsV55SlicesNoHTB', 'qosFlowsV55SlicesHTB', 'qoeFlowsV5Base', 'qoeFlowsV55SlicesNoHTB', 'qoeFlowsV55SlicesHTB']
descriptors = ['BE-1', 'BE-2', 'QoS', 'QoS-Sli-1', 'QoS-Sli-2', 'QoE', 'QoESli1', 'QoE\nSli-2']
clients = ['VID', 'LVD', 'FDO', 'VIP', 'SSH','cVIP' ]
resToSli = {
    'VID' : 46741,
    'LVD' : 41430, 
    'FDO' : 10623, 
    'SSH' : 47, 
    'VIP' : 569,
    'cVIP' : 588,
    'all' : 100000
}
# descriptors = ['BE-1', 'BE-2', 'QoS', 'QoS-Sli-1', 'QoS-Sli-2', 'QoE', 'QoE\nSli-1', 'QoE\nSli-2']
plotQoEMultiExperiment(testNames, clients, 3.5, descriptors)
plotSysUtilMultiExperiment(testNames, clients, descriptors, resToSli)