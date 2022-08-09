import pandas
import csv
import statistics
from termcolor import colored
import sys
import os

maxSimTime = 400
DEBUG = 0

downlink = ['Downlink', 'rxPkOk:vector(packetBytes)']
uplink = ['Uplink', 'txPk:vector(packetBytes)']

def makeFullScenarioName(testName):
    scenName = str(testName)
    return scenName
    # return str(testName) + '_' + str(numCLI) + '_VID' + str(nodeSplit[0]) + '_FDO' + str(nodeSplit[1]) + '_SSH' + str(nodeSplit[2]) + '_VIP' + str(nodeSplit[3])

def makeNodeIdentifier(tp, delay):
    return 'tp' + str(tp) + '_del' + str(delay)

# Function that imports node information into a dataframe
#   - testName - name of the test
#   - numCLI - total number of clients in the test
#   - nodeSplit - number of nodes running certain applications in the test
#       [numVID, numFDO, numSSH, numVIP]
#   - nodeType - type of the node to import (String), curr. used
#       hostVID, hostFDO, hostSSH, hostVIP, links, serverSSH
#   - nodeNum - number of the node to import, omitted if -1
def importDF(testName, tp, delay):
    # File that will be read
    fullScenarioExportName = makeFullScenarioName(testName)
    # fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_hostVID0_vec.csv'
    #fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_hostFDO0_vec.csv'
    # fileToRead = '../' + str(testName) + '/' + fullScenarioExportName + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_vec.csv'
    fileToRead = '../' + str(testName) + '/heatMapTest_VoIP_corrected_1_VID0_FDO0_SSH0_VIP1'  + '/' + fullScenarioExportName + '_' + makeNodeIdentifier(tp, delay) + '_hostVIP0_vec.csv'
    print("Importing: " + fileToRead)
    # Read the CSV
    return pandas.read_csv(fileToRead)

def filterDFType(df, filterType):
    return df.filter(like=filterType)

def getFilteredDFtypeAndTS(df, filterType):
    filteredDF = filterDFType(df, filterType)
    if len(filteredDF.columns):
        colNoTS = df.columns.get_loc(df.filter(filteredDF).columns[0])
        newDF = df.iloc[:,[colNoTS,colNoTS+1]].dropna()
        newDF.rename(columns={str(newDF.columns[0]) : "TS", str(newDF.columns[1]) : filterType + " Val"})
        return newDF.rename(columns={str(newDF.columns[0]) : "TS", str(newDF.columns[1]) : filterType + " Val"})
    else:
        return pandas.DataFrame(columns=['ts', 'mos Val'])

def extractMosVal(testName, tp, delay):
    df = importDF(testName, tp, delay)
    mosDF = getFilteredDFtypeAndTS(df, 'mos')
    # print(mosDF)
    mosList = mosDF['mos Val'].tolist()
    if len(mosList) > 0:
        print(mosList[0])
        return mosList[0]
    else:
        return 1.0

def extracte2ed(testName, tp, delay):
    df = importDF(testName, tp, delay)
    mosDF = getFilteredDFtypeAndTS(df, 'endToEndDelay')
    print(mosDF['endToEndDelay Val'])
    return mosDF['endToEndDelay Val']

# extractMosVal('heatMapTest_VoIPnewSettings', 540, 0)
# extracte2ed('singleAppDelayTest_VoIP_1cli', 10000, 50)

def prepareMosValsForHeatmap(testName, tps, delays):
    xAxis = []
    yAxis = []
    mosMap = []
    for x in delays:
        print(x)
        if x not in xAxis:
            xAxis.append(x)
        for y in tps:
            if y not in yAxis:
                yAxis.append(y)
                mosMap.append([])
            mosMap[yAxis.index(y)].append(extractMosVal(testName, y, x))
    if not os.path.exists('../exports/heatMap/'):
        os.makedirs('../exports/heatMap/')
    with open('../exports/heatMap/'+makeFullScenarioName(testName)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(xAxis)
        fw.writerow(yAxis)
        fw.writerow(mosMap)

# prepareMosValsForHeatmap('heatMapTest_SSH', [5,10,150,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620])
# prepareMosValsForHeatmap('heatMapTest_VoIP', [555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620,640,660,680,700,720,740,760,780,800,820,840,860,880,900,920,940,960,980])
# prepareMosValsForHeatmap('heatMapTest_VoIPnewSettings', [540,542,544,546,548,550,552,554,556,558,560,562,564,566,568,570,572,574,576,578,580,582,584,586,588,590,592,594,596,598,600], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620,640,660,680,700,720,740,760,780,800])
# prepareMosValsForHeatmap('heatMapTest_Video', [250,290,330,370,410,450,490,530,570,610,650,690,730,770,810,850,890,930,970,1010,1050,1090,1130,1170,1210,1250,1290,1330,1370,1410,1450,1490,1530], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_VideoV2', [50,150,250,350,450,550,650,750,850,950,1050,1150,1250,1350,1450,1550,1650,1750,1850,1950,2050,2150,2250,2350,2450,2550,2650,2750,2850,2950,3050,3150,3250], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoV2', [50,150,250,350,450,550,650,750,850,950,1050,1150,1250,1350,1450,1550,1650,1750,1850,1950,2050,2150,2250,2350,2450,2550,2650,2750,2850,2950,3050,3150,3250], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_NewLiveVideoClient', [50,150,250,350,450,550,650,750,850,950,1050,1150,1250,1350,1450,1550,1650,1750,1850,1950,2050,2150,2250,2350,2450,2550,2650,2750,2850,2950,3050,3150,3250], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_NewLiveVideoClient', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_VideoV2', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideo', [250,290,330,370,410,450,490,530,570,610,650,690,730,770,810,850,890,930,970,1010,1050,1090,1130,1170,1210,1250,1290,1330,1370,1410,1450,1490,1530], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_FileDownload', [250,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3250,3500,3750,4000,4250,4500,4750,5000,5250,5500,5750,6000,6250,6500,6750,7000,7250,7500,7750,8000], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])
# prepareMosValsForHeatmap('heatMapTest_FileDownload2-5MB', [250,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3250,3500,3750,4000,4250,4500,4750,5000,5250,5500,5750,6000,6250,6500,6750,7000,7250,7500,7750,8000], [0,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600])

# prepareMosValsForHeatmap('heatMapTest_VideoFine', [i*20 for i in range(1,51)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoFine', [i*20 for i in range(1,51)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_FileDownloadFine', [i*20 for i in range(1,51)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_VideoLong', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_VideoFineLong', [i*20 for i in range(1,51)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_LiveVideoFineShort', [i*20 for i in range(1,51)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoFineLong', [i*20 for i in range(1,51)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_LiveVideoShort', [50+i*300 for i in range(33)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_LiveVideoLong', [50+i*300 for i in range(33)], [i*20 for i in range(31)])

# prepareMosValsForHeatmap('heatMapTest_VoIP_corrected', [x for x in range(5,56)], [x*20 for x in range(0,50)])

# prepareMosValsForHeatmap('heatMapTest_LiveVideoFineLongV2', [100+x*20 for x in range(226)], [i*20 for i in range(31)])
# prepareMosValsForHeatmap('heatMapTest_VideoFineLongV2', [100+x*20 for x in range(226)], [i*20 for i in range(31)])
#prepareMosValsForHeatmap('heatMapTest_FileDownloadFineV3', [100+x*20 for x in range(226)], [i*20 for i in range(31)])

prepareMosValsForHeatmap('heatMapTest_VoIP_corrected', [x for x in range(50,560,10)], [x*2 for x in range(0,50)])
