import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0,currentdir) 

import delayEstimation as delEst
import csv

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)

font = {'weight' : 'normal',
        'size'   : 40}

matplotlib.rc('font', **font)
matplotlib.rc('lines', linewidth=2.0)
matplotlib.rc('lines', markersize=8)

class ClientQoeEstimator:

    cliType = ''
    mosMap = []
    xAxis = []
    yAxis = []

    maxMos = 0
    minMos = 6

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

    def __init__(self, cliType):
        self.cliType = cliType
        self.mosMap, self.xAxis, self.yAxis = self.__loadQoEmap()

    def prettyPrimtMosMap(self):
        for row in range(len(self.mosMap)):
            print("{:.2f}".format(self.xAxis[row]), end='\t|  ')
            for val in range(len(self.mosMap[row])):
                estimMos = (self.mosMap[row][val] - self.minMaxQoE[self.cliType]['minMOS'])*((5.0 - 1.0)/(self.minMaxQoE[self.cliType]['maxMOS'] - self.minMaxQoE[self.cliType]['minMOS'])) + 1.0
                print("{:.2f}".format(estimMos), end=' ')
            print()
        print("\t|  ", end='')
        for i in range(len(self.yAxis)):
            print("{:.2f}".format(self.yAxis[i]), end=' ')
        print()

    def __loadQoEmap(self):
        xAxis = []
        yAxis = []
        tempMosMap = []
        mosMap = []
        csvFolder = currentdir+'/mosMaps/' # Path to folder with csv heat map results
        suffix = ''
        if  self.cliType == 'hostVID':
            suffix = 'FineLongV2'
        if  self.cliType == 'hostLVD':
            suffix = 'FineLongV2'  
        if self.cliType == 'hostFDO':
            suffix = 'FineV3'
        if  self.cliType == 'hostVIP':
            suffix = '_corrected'    
        if  self.cliType == 'hostSSH':
            suffix = ''    
        if  self.cliType == 'hostcVIP':
            suffix = ''    
          
        
        file_to_read = csvFolder + 'heatMap_' + self.cliType + suffix + '.csv'
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

        self.maxMos = tempMax
        self.minMos = tempMin

        newMosMap = newMosMap[::-1]
        xAxis = xAxis[::-1]
        return newMosMap, xAxis, yAxis
    
    def estUTILbd(self, availBand, estDelay):
        corBand = min(self.yAxis, key=lambda x:abs(x-availBand))
        corDel = min(self.xAxis, key=lambda x:abs(x-estDelay))
        # print(corBand, corDel)
        initialEstimMos = self.mosMap[self.xAxis.index(corDel)][self.yAxis.index(corBand)]
        estimMos = (initialEstimMos - self.minMaxQoE[self.cliType]['minMOS'])*((5.0 - 1.0)/(self.minMaxQoE[self.cliType]['maxMOS'] - self.minMaxQoE[self.cliType]['minMOS'])) + 1.0
        # print("Estimated MOS for " + self.cliType + " with bandwidth of " + str(availBand) + "kbps and end-to-end delay of " + str(estDelay) + "ms: " + str(estimMos))
        # if self.cliType == 'hostLVD':
        #     estimMos += 0.8
        return estimMos
    
    def estQoEbd(self, availBand, estDelay):
        corBand = min(self.yAxis, key=lambda x:abs(x-availBand))
        corDel = min(self.xAxis, key=lambda x:abs(x-estDelay))
        # print(corBand, corDel)
        initialEstimMos = self.mosMap[self.xAxis.index(corDel)][self.yAxis.index(corBand)]
        return initialEstimMos

    def estQoEb(self, availBand):
        estimatedDelay = delEst.estDelay(self.cliType, availBand)
        return self.estQoEbd(availBand, estimatedDelay)

    def plotMOSWithDelay(self):
        print(self.cliType + ' xAxis length: ' + str(len(self.xAxis)))
        print(self.cliType + ' yAxis length: ' + str(len(self.yAxis)))

        fig, ax = plt.subplots(1, figsize=(16,12))
        norm = matplotlib.colors.Normalize(vmin=1.0, vmax=5.0)
        cmap = plt.cm.get_cmap(name='viridis',lut=1024)
        im = ax.imshow(np.array(self.mosMap), norm=norm, cmap=cmap, aspect='auto')
        
        cbar = ax.figure.colorbar(im, ax=ax, norm=norm, cmap=cmap)

        
        cbar.mappable.set_clim(1.0, 5.0)
        cbar.ax.set_ylabel('Mos Value', rotation=-90, va="bottom")


        xAxis = [int(x) for x in self.xAxis]
        yAxis = [int(y) for y in self.yAxis]

        ax.set_yticks(np.arange(len(xAxis)))
        ax.set_xticks(np.arange(len(yAxis)))

        ax.set_yticklabels(xAxis)
        ax.set_xticklabels(yAxis)

        xAxisMajor = 3
        if 'VID' in self.cliType or 'LVD' in self.cliType or 'FDO' in self.cliType:
            xAxisMajor = 15


        labels = ax.get_xticklabels() # get x labels
        newLabels = [0]
        for i,_ in enumerate(labels):
            if i % xAxisMajor == 0: newLabels.append(labels[i])
        ax.xaxis.set_major_locator(MultipleLocator(xAxisMajor))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.set_xticklabels(newLabels, rotation=90) # set new labels
        # print(ax.get_yticks())

        newLabels = [0]
        labels = ax.get_yticklabels() # get y labels
        for i,l in enumerate(labels):
            if i%3 == 0: newLabels.append(labels[i])
        ax.yaxis.set_major_locator(MultipleLocator(3))
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.set_yticklabels(newLabels, rotation=0) # set new labels
        

        estimDelays = []
        for place in yAxis:
            # print(place)
            # print(place, delEst.estDelay(self.cliType, place))
            # corDel = min(self.xAxis, key=lambda x:abs(x-delEst.estDelay(self.cliType, x)))
            estimDelays.append(min(self.xAxis, key=lambda x:abs(x-delEst.estDelay(self.cliType, place))))
        # print(estimDelays)

        # ax.plot([str(int(x)) for x in yAxis], [str(int(y)) for y in estimDelays], marker='+', ls='-', color='red')
        ax.plot([yAxis.index(x) for x in yAxis], [xAxis.index(y) for y in estimDelays], marker='+', ls='-', color='red')

        plt.ylabel("Link Delay [ms]")
        plt.xlabel("Link Throughput [kbps]")
        outPath = 'mosMaps/plots/' + self.cliType + '.pdf'
        fig.savefig(outPath, dpi=100, bbox_inches='tight')
        outPath = 'mosMaps/plots/' + self.cliType + '.png'
        fig.savefig(outPath, dpi=100, bbox_inches='tight', format='png')
        plt.close('all')

if __name__ == "__main__":
    print('QoE Estimation MAIN method:')
    test1 = ClientQoeEstimator('hostFDO')
    test2 = ClientQoeEstimator('hostSSH')
    test3 = ClientQoeEstimator('hostVID')
    test4 = ClientQoeEstimator('hostVIP')
    test5 = ClientQoeEstimator('hostLVD')
    test6 = ClientQoeEstimator('hostcVIP')
    test1.plotMOSWithDelay()
    test2.plotMOSWithDelay()
    test3.plotMOSWithDelay()
    test4.plotMOSWithDelay()
    test5.plotMOSWithDelay()
    test6.plotMOSWithDelay()
    # print(test1.cliType, '-> minMOS: ', test1.minMos, '\t- maxMOS: ', test1.maxMos)
    # print(test2.cliType, '-> minMOS: ', test2.minMos, '\t\t- maxMOS: ', test2.maxMos)
    # print(test3.cliType, '-> minMOS: ', test3.minMos, '\t- maxMOS: ', test3.maxMos)
    # print(test4.cliType, '-> minMOS: ', test4.minMos, '\t\t- maxMOS: ', test4.maxMos)
    # print(test5.cliType, '-> minMOS: ', test5.minMos, '\t- maxMOS: ', test5.maxMos)
    # print(test5.estQoEbd(4000,218))
    # test5.prettyPrimtMosMap()
    # print(test.estQoEbd(5.0, 600.0))