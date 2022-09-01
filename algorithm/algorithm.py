import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0,currentdir) 

import delayEstimation as delEst
import qoeEstimation as qoeEst

import random
import statistics
import csv

import copy

import itertools

CRED = '\033[91m'
CGREEN  = '\33[32m'
CYELLOW = '\33[33m'
CBLUE   = '\33[34m'
CGREENBG = '\33[42m'
CBLUEBG   = '\33[44m'
CEND = '\033[0m'

def esimateBandMosDel(numHostsSlice, qoeEstimators, sliceAssignment, bandAssignment, rbSize, printFlag):
    if printFlag == True: print("\tBand assignment: " + str(bandAssignment) + '; Num all bands = ' + str(sum([bandAssignment[x] for x in bandAssignment])))
    maxSSHCliBand = 20.0
    currMeanBandPerHostSlice = {}
    currEstDelayPerHostSlice = {}
    currEstMosPerHostSlice = {}
    minMos = ('', '', 6)
    maxMos = ('', '', 0)
    allMosVals = []
    for sli in numHostsSlice:
        currMeanBandPerHostSlice[sli] = {}
        currEstDelayPerHostSlice[sli] = {}
        currEstMosPerHostSlice[sli] = {}
        for host in sliceAssignment[sli]:
            if 'hostSSH' in sliceAssignment[sli] and len(sliceAssignment[sli]) > 1:
                if bandAssignment[sli] * rbSize / numHostsSlice[sli] > maxSSHCliBand:
                    if host == 'hostSSH':
                        currMeanBandPerHostSlice[sli][host] = maxSSHCliBand
                    else:
                        currMeanBandPerHostSlice[sli][host] = (bandAssignment[sli] * rbSize - sliceAssignment[sli]['hostSSH']*maxSSHCliBand) / (numHostsSlice[sli] - sliceAssignment[sli]['hostSSH'])
                else:
                    currMeanBandPerHostSlice[sli][host] = bandAssignment[sli] * rbSize / numHostsSlice[sli]
            else:
                currMeanBandPerHostSlice[sli][host] = bandAssignment[sli] * rbSize / numHostsSlice[sli]
            currEstDelayPerHostSlice[sli][host] = delEst.estDelay(host, currMeanBandPerHostSlice[sli][host])
            currEstMosPerHostSlice[sli][host] = qoeEstimators[host].estQoEbd(currMeanBandPerHostSlice[sli][host], currEstDelayPerHostSlice[sli][host])
            allMosVals.extend([currEstMosPerHostSlice[sli][host] for _ in range(sliceAssignment[sli][host])])
            if minMos[2] > currEstMosPerHostSlice[sli][host]:
                minMos = (sli, host, currEstMosPerHostSlice[sli][host])
            if maxMos[2] < currEstMosPerHostSlice[sli][host]:
                maxMos = (sli, host, currEstMosPerHostSlice[sli][host])

    if printFlag == True: print('\tMin MOS:\t' + str(minMos))
    if printFlag == True: print('\tMax MOS:\t' + str(maxMos))
    avgMos = statistics.mean(allMosVals)
    if printFlag == True: print('\tMean MOS:\t' +str(avgMos))
    mosFairness = 1 - (2*statistics.stdev(allMosVals))/(5.0-1.0)
    if printFlag == True: print('\tQoE Fairness:\t' +str(mosFairness))
    if printFlag == True: print("\tMean cli band:\t" + str(currMeanBandPerHostSlice))
    if printFlag == True: print("\tEst cli del:\t" + str(currEstDelayPerHostSlice))
    if printFlag == True: print("\tEst cli mos:\t" + str(currEstMosPerHostSlice))
    
    return currMeanBandPerHostSlice, currEstDelayPerHostSlice, currEstMosPerHostSlice, minMos, maxMos, avgMos, mosFairness

def normaliseMosForObjFunc(inputValue):
    return (inputValue - 1.0)/(5.0-1.0)

# Beta is not used currently
def objectiveFunction(alpha, beta, minMosTuple, avgMos, mosFairness, printFlag):
    calcValue = alpha*mosFairness + (1-alpha)*normaliseMosForObjFunc(avgMos)
    if printFlag == True: print('\tObjective function: ' + str(alpha) + ' * ' + str(mosFairness) + ' + ' + str(1 - alpha) + ' * ' + str(normaliseMosForObjFunc(avgMos)) + ' = ' + CBLUEBG + str(calcValue) + CEND)
    return calcValue

# ex sliceAssignment = {'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}
# ex initialBandAssignment = {'sliceDel' : 20, 'sliceBand' : 80} in recource blocks
# rbSize is resource block size in kbps
def algorithm(sliceAssignment, initialBandAssignment, rbSize, alpha, beta, numAlgRounds, sameLimit, printFlag):
    numHostsSlice = {}
    qoeEstimators = {}
    for sli in sliceAssignment:
        sumHosts = 0
        for host in sliceAssignment[sli]:
            sumHosts += sliceAssignment[sli][host]
            qoeEstimators[host] = qoeEst.ClientQoeEstimator(host)
        numHostsSlice[sli] = sumHosts
    bandAssignment = initialBandAssignment

    roundBandAssignment = {}
    roundMeanBandPerHostSlice = {}
    roundEstDelayPerHostSlice = {}
    roundEstMosPerHostSlice = {}
    roundMinMos = {}
    roundMaxMos = {}
    roundAvgMos = {}
    roundMosFairness = {}
    roundObjectiveFunction = {}


    for algRound in range(0, numAlgRounds):
        print(CRED + '-- Round ' + str(algRound) + ' --' + CEND, end='')
        if algRound == 0:
            print('')
            currMeanBandPerHostSlice, currEstDelayPerHostSlice, currEstMosPerHostSlice, minMos, maxMos, avgMos, mosFairness = esimateBandMosDel(numHostsSlice, qoeEstimators, sliceAssignment, bandAssignment, rbSize, printFlag)
            roundMeanBandPerHostSlice[algRound] = currMeanBandPerHostSlice.copy()
            roundEstDelayPerHostSlice[algRound] = currEstDelayPerHostSlice.copy()
            roundEstMosPerHostSlice[algRound] = currEstMosPerHostSlice.copy()
            roundMinMos[algRound] = minMos
            roundMaxMos[algRound] = maxMos
            roundAvgMos[algRound] = avgMos
            roundBandAssignment[algRound] = bandAssignment.copy()
            roundObjectiveFunction[algRound] = objectiveFunction(alpha, beta, minMos, avgMos, mosFairness, printFlag)
            continue
        
        if printFlag: print(CYELLOW + '\nLast configuration:' + CEND)
        _, _, _, minMos, _, avgMos, mosFairness = esimateBandMosDel(numHostsSlice, qoeEstimators, sliceAssignment, roundBandAssignment[algRound-1], rbSize, printFlag)
        objectiveFunction(alpha, beta, minMos, avgMos, mosFairness, printFlag)

        # Get reversed order list of last allocations and check how far back the resource allocation has not changed
        revLastResults = [roundBandAssignment[x] for x in list(roundBandAssignment)][::-1]
        
        # The number of round nothing has changed is the 'allocation' jump we will try in this algorithm round. So we start with 1 and if there was no change in previous two rounds we go to 2 and so on...
        numSame = 1
        for i in range(1, len(revLastResults)):
            numSame = i
            if revLastResults[i] != revLastResults[i-1]:
                break
        if numSame > 1: print('\tLast ' + str(numSame) + ' rounds resulted in the same resource assignment')
        else: print('')
        
        
        if printFlag: print('Offset: ' + str(numSame))
        sliceList = list(bandAssignment)
        
        maxObjectiveFunction = roundObjectiveFunction[algRound - 1]
        bestAssignment = roundBandAssignment[algRound - 1]
        for sliceIncrease in sliceList:
            for sliceDecrease in sliceList:
                if sliceIncrease == sliceDecrease:
                    continue
                testBandAssignment = roundBandAssignment[algRound-1].copy()
                if testBandAssignment[sliceDecrease] > numSame:
                    testBandAssignment[sliceDecrease] -= numSame
                else:
                    continue
                testBandAssignment[sliceIncrease] += numSame
                _, _, _, testMinMos, _, testAvgMos, testMosFairness = esimateBandMosDel(numHostsSlice, qoeEstimators, sliceAssignment, testBandAssignment, rbSize, False)
                objectiveFunctionVal = objectiveFunction(alpha, beta, testMinMos, testAvgMos, testMosFairness, False)
                # print(objectiveFunctionVal)
                if objectiveFunctionVal > maxObjectiveFunction:
                    print(CGREEN + '\tWe have found a better configuration in this round! Cause: ' + str(objectiveFunctionVal) + ' > ' + str(maxObjectiveFunction) + CEND)
                    print(CGREEN + '\tMean utility: ' + str(testAvgMos) + '; Min utility : ' + str(testMinMos) + '; Fairness: ' + str(testMosFairness) + ';' + CEND)
                    maxObjectiveFunction = objectiveFunctionVal
                    bestAssignment = testBandAssignment
                    print(CGREEN + '\tResource allocation: ' + str(bestAssignment) + CEND)
        
        # print(bestAssignment)
        if printFlag: print(CGREEN + 'New configuration:' + CEND)
        newMeanBandPerHostSlice, newEstDelayPerHostSlice, newEstMosPerHostSlice, newMinMos, newMaxMos, newAvgMos, newMosFairness = esimateBandMosDel(numHostsSlice, qoeEstimators, sliceAssignment, bestAssignment, rbSize, printFlag)
        newObjectiveFunction = objectiveFunction(alpha, beta, newMinMos, newAvgMos, newMosFairness, printFlag)

        roundMeanBandPerHostSlice[algRound] = newMeanBandPerHostSlice.copy()
        roundEstDelayPerHostSlice[algRound] = newEstDelayPerHostSlice.copy()
        roundEstMosPerHostSlice[algRound] = newEstMosPerHostSlice.copy()
        roundMinMos[algRound] = newMinMos
        roundMaxMos[algRound] = newMaxMos
        roundAvgMos[algRound] = newAvgMos
        roundMosFairness[algRound] = newMosFairness
        roundBandAssignment[algRound] = bestAssignment.copy()
        roundObjectiveFunction[algRound] = newObjectiveFunction

        if numSame >= sameLimit:
            print(CGREENBG+"Last "+str(sameLimit)+" rounds resulted in the same resource assignment! Algorithm is done!"+CEND)
            break
    print('Number of rounds required to find the last assignment: ' + str(algRound) + '(numAlgRounds) - ' + str(numSame) + '(numLastSameAssignment) = ' + str(algRound - numSame))
    print('Final, recommended, assignment:')
    esimateBandMosDel(numHostsSlice, qoeEstimators, sliceAssignment, bestAssignment, rbSize, True)
    objectiveFunction(alpha, beta, newMinMos, newAvgMos, newMosFairness, True)
    print('')

    return roundBandAssignment[algRound], roundObjectiveFunction[algRound], roundMinMos[algRound], roundMaxMos[algRound], roundAvgMos[algRound], roundMosFairness[algRound], roundMeanBandPerHostSlice[algRound], roundEstDelayPerHostSlice[algRound], roundEstMosPerHostSlice[algRound]

def alphaBetaTester(sliceAssignment, initialBandAssignment, rbSize, numAlgRounds, testName):
    testedAlpha = []
    testedBeta = []
    assignments = []
    objFuncVals = []
    minMosVals = []
    maxMosVals = []
    avgMosVals = []
    mosFairnessVals = []
    for alpha in [0.05*x for x in range(21)]:
        for beta in [0.05*x for x in range(21)]:
            if alpha + beta <= 1:
                assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, _, _, _ = algorithm(sliceAssignment, initialBandAssignment, rbSize, alpha, beta, numAlgRounds, 50, False)
                testedAlpha.append(alpha)
                testedBeta.append(beta)
                assignments.append(assign)
                objFuncVals.append(objFuncVal)
                minMosVals.append(minMos)
                maxMosVals.append(maxMos)
                avgMosVals.append(avgMos)
                mosFairnessVals.append(mosFairness)
                print(alpha, beta, assign, objFuncVal, minMos, maxMos, avgMos, mosFairness)
    
    for i in range(len(testedAlpha)):
        print(testedAlpha[i], testedBeta[i], assignments[i], objFuncVals[i])
    
    with open(testName+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(testedAlpha)
        fw.writerow(testedBeta)
        fw.writerow(assignments)
        fw.writerow(objFuncVals)
        fw.writerow(minMosVals)
        fw.writerow(maxMosVals)
        fw.writerow(avgMosVals)
        fw.writerow(mosFairnessVals)

def alphaTester(sliceAssignment, initialBandAssignment, rbSize, numAlgRounds, testName):
    testedAlpha = []
    testedBeta = []
    assignments = []
    objFuncVals = []
    minMosVals = []
    maxMosVals = []
    avgMosVals = []
    mosFairnessVals = []
    meanBandSliceVals = []
    estimDelaySliceVals = []
    estMosSliceVals = []
    for alpha in [0.05*x for x in range(21)]:
        if alpha + 0.0 <= 1:
            assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, meanBandSlice, estimDelaySlice, estMosSlice = algorithm(sliceAssignment, initialBandAssignment, rbSize, alpha, 0.0, numAlgRounds, 50, False)
            testedAlpha.append(alpha)
            testedBeta.append(0.0)
            assignments.append(assign)
            objFuncVals.append(objFuncVal)
            minMosVals.append(minMos)
            maxMosVals.append(maxMos)
            avgMosVals.append(avgMos)
            mosFairnessVals.append(mosFairness)
            meanBandSliceVals.append(meanBandSlice)
            estimDelaySliceVals.append(estimDelaySlice)
            estMosSliceVals.append(estMosSlice)
            print(alpha, 0.0, assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, meanBandSlice, estimDelaySlice, estMosSlice)
    
    for i in range(len(testedAlpha)):
        print(testedAlpha[i], testedBeta[i], assignments[i], objFuncVals[i])
    
    with open(testName+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(testedAlpha)
        fw.writerow(testedBeta)
        fw.writerow(assignments)
        fw.writerow(objFuncVals)
        fw.writerow(minMosVals)
        fw.writerow(maxMosVals)
        fw.writerow(avgMosVals)
        fw.writerow(mosFairnessVals)
        fw.writerow(meanBandSliceVals)
        fw.writerow(estimDelaySliceVals)
        fw.writerow(estMosSliceVals)


def rbSizeTester(sliceAssignment, initialBandAssignmentPercentage, rbSizes, linkMaxSpeed, numAlgRounds, alpha, beta, testName):
    assignments = []
    objFuncVals = []
    minMosVals = []
    maxMosVals = []
    avgMosVals = []
    mosFairnessVals = []
    for rbSize in rbSizes:
        numRBs = linkMaxSpeed / rbSize
        print(numRBs)
        initialBandAssignment = {}
        for sli in list(initialBandAssignmentPercentage):
            initialBandAssignment[sli] = initialBandAssignmentPercentage[sli]*numRBs
        print(initialBandAssignment)
        print(numRBs/len(list(initialBandAssignment)))
        assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, _, _, _ = algorithm(sliceAssignment, initialBandAssignment, rbSize, alpha, beta, numAlgRounds, max(100,numRBs/len(list(initialBandAssignment))), False)
        assignments.append(assign)
        objFuncVals.append(objFuncVal)
        minMosVals.append(minMos)
        maxMosVals.append(maxMos)
        avgMosVals.append(avgMos)
        mosFairnessVals.append(mosFairness)
        print(alpha, beta, assign, objFuncVal, minMos, maxMos, avgMos, mosFairness)
    
    for i in range(len(rbSizes)):
        print(rbSizes[i], assignments[i], objFuncVals[i])
    
    with open(testName+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(rbSizes)
        fw.writerow(assignments)
        fw.writerow(objFuncVals)
        fw.writerow(minMosVals)
        fw.writerow(maxMosVals)
        fw.writerow(avgMosVals)
        fw.writerow(mosFairnessVals)

def variousCliNumTester(exempSlicesNums, rbSize, linkBand, numAlgRounds, alphas, testName):
    cliNums = []
    initNumRBsSlice = linkBand / (rbSize*len(exempSlicesNums))
    initialAllocation = {}
    for x in exempSlicesNums:
        initialAllocation[x] = initNumRBsSlice
        # initialAllocation[x] = 1
        for y in exempSlicesNums[x]:
            cliNums.append(exempSlicesNums[x][y])
    # initialAllocation[x] = linkBand / rbSize
    print(initialAllocation)
    # print(len(list(itertools.permutations(cliNums, len(cliNums)))))
    for alpha in alphas:
        clientConfig = []
        assignments = []
        objFuncVals = []
        minMosVals = []
        maxMosVals = []
        avgMosVals = []
        mosFairnessVals = []
        meanBandSliceVals = []
        estimDelaySliceVals = []
        estMosSliceVals = []
        for subset in itertools.permutations(cliNums, len(cliNums)):
            itera = 0
            tempSliceAssignment = copy.deepcopy(exempSlicesNums)
            for x in exempSlicesNums:
                for y in exempSlicesNums[x]:
                    tempSliceAssignment[x][y] = subset[itera]
                    itera += 1
            assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, meanBandSlice, estimDelaySlice, estMosSlice = algorithm(tempSliceAssignment.copy(), initialAllocation.copy(), rbSize, alpha, 0.0, numAlgRounds, 100, False)
            # print(tempSliceAssignment)
            clientConfig.append(tempSliceAssignment.copy())
            # print(clientConfig)
            assignments.append(assign.copy())
            objFuncVals.append(objFuncVal)
            minMosVals.append(minMos)
            maxMosVals.append(maxMos)
            avgMosVals.append(avgMos)
            mosFairnessVals.append(mosFairness)
            meanBandSliceVals.append(meanBandSlice.copy())
            estimDelaySliceVals.append(estimDelaySlice.copy())
            estMosSliceVals.append(estMosSlice.copy())
            
        with open(testName+'alpha'+str(alpha)+'.csv', mode='w') as writeFile:
            fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            fw.writerow(clientConfig)
            fw.writerow(assignments)
            fw.writerow(objFuncVals)
            fw.writerow(minMosVals)
            fw.writerow(maxMosVals)
            fw.writerow(avgMosVals)
            fw.writerow(mosFairnessVals)
            fw.writerow(meanBandSliceVals)
            fw.writerow(estimDelaySliceVals)
            fw.writerow(estMosSliceVals)

def fetchAlgResults(configName, alphas, basicSliConfig, basicSliBand, rbSize, linkBand, numAlgRounds, testName):
    chosenAlphaList = []
    cliConfig = []
    file_to_read = '../analysis/code/ultimateConfigs/' + configName + 'alphas' + str(alphas) + '.csv'
    with open(file_to_read, mode='r') as readFile:
        csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                chosenAlphaList.extend(row)
            elif line_count == 1:
                cliConfig.extend([eval(x) for x in row])
            line_count += 1
    
    clientConfig = []
    assignments = []
    objFuncVals = []
    minMosVals = []
    maxMosVals = []
    avgMosVals = []
    mosFairnessVals = []
    meanBandSliceVals = []
    estimDelaySliceVals = []
    estMosSliceVals = []
    for i in range(len(chosenAlphaList)):
        sliceAssignment = copy.deepcopy(basicSliConfig)
        for sli in sliceAssignment:
            for cli in sliceAssignment[sli]:
                sliceAssignment[sli][cli] = cliConfig[i][cli]
        initialBandAssignment = copy.deepcopy(basicSliBand)
        # print(sliceAssignment)
        # print(initialBandAssignment)
        assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, meanBandSlice, estimDelaySlice, estMosSlice = algorithm(sliceAssignment, initialBandAssignment, rbSize, chosenAlphaList[i], 0.0, numAlgRounds, 100, False)
        # print(tempSliceAssignment)
        clientConfig.append(sliceAssignment.copy())
        # print(clientConfig)
        assignments.append(assign.copy())
        objFuncVals.append(objFuncVal)
        minMosVals.append(minMos)
        maxMosVals.append(maxMos)
        avgMosVals.append(avgMos)
        mosFairnessVals.append(mosFairness)
        meanBandSliceVals.append(meanBandSlice.copy())
        estimDelaySliceVals.append(estimDelaySlice.copy())
        estMosSliceVals.append(estMosSlice.copy())
        
    with open(testName+'alphas'+str(alphas)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(chosenAlphaList)
        fw.writerow(clientConfig)
        fw.writerow(assignments)
        fw.writerow(objFuncVals)
        fw.writerow(minMosVals)
        fw.writerow(maxMosVals)
        fw.writerow(avgMosVals)
        fw.writerow(mosFairnessVals)
        fw.writerow(meanBandSliceVals)
        fw.writerow(estimDelaySliceVals)
        fw.writerow(estMosSliceVals)

def fetchAlgResultsManTests(testName, alphas, basicSliConfig, basicSliBand, rbSize, linkBand, numAlgRounds):
    # chosenAlphaList = []
    # cliConfig = []
    # file_to_read = '../analysis/exports/compExports/' + testName + '.csv'
    # with open(file_to_read, mode='r') as readFile:
    #     csv_reader = csv.reader(readFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    #     line_count = 0
    #     for row in csv_reader:
    #         if line_count == 0:
    #             chosenAlphaList.extend(row)
    #         elif line_count == 1:
    #             cliConfig.extend([eval(x) for x in row])
    #         line_count += 1
    
    clientConfig = []
    assignments = []
    objFuncVals = []
    minMosVals = []
    maxMosVals = []
    avgMosVals = []
    mosFairnessVals = []
    meanBandSliceVals = []
    estimDelaySliceVals = []
    estMosSliceVals = []
    for i in range(len(alphas)):
        sliceAssignment = copy.deepcopy(basicSliConfig)
        # for sli in sliceAssignment:
        #     for cli in sliceAssignment[sli]:
        #         sliceAssignment[sli][cli] = cliConfig[i][cli]
        initialBandAssignment = copy.deepcopy(basicSliBand)
        # print(sliceAssignment)
        # print(initialBandAssignment)
        assign, objFuncVal, minMos, maxMos, avgMos, mosFairness, meanBandSlice, estimDelaySlice, estMosSlice = algorithm(sliceAssignment, initialBandAssignment, rbSize, alphas[i], 0.0, numAlgRounds, 100, False)
        # print(tempSliceAssignment)
        clientConfig.append(sliceAssignment.copy())
        # print(clientConfig)
        assignments.append(assign.copy())
        objFuncVals.append(objFuncVal)
        minMosVals.append(minMos)
        maxMosVals.append(maxMos)
        avgMosVals.append(avgMos)
        mosFairnessVals.append(mosFairness)
        meanBandSliceVals.append(meanBandSlice.copy())
        estimDelaySliceVals.append(estimDelaySlice.copy())
        estMosSliceVals.append(estMosSlice.copy())
        
    with open('selectedConfigsRes/'+testName+'_alphas'+str(alphas)+'.csv', mode='w') as writeFile:
        fw = csv.writer(writeFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        fw.writerow(alphas)
        fw.writerow(clientConfig)
        fw.writerow(assignments)
        fw.writerow(objFuncVals)
        fw.writerow(minMosVals)
        fw.writerow(maxMosVals)
        fw.writerow(avgMosVals)
        fw.writerow(mosFairnessVals)
        fw.writerow(meanBandSliceVals)
        fw.writerow(estimDelaySliceVals)
        fw.writerow(estMosSliceVals)


# fetchAlgResultsManTests('baselineTestNS_5sli_AlgoTest', [0.0, 0.5, 1.0], {'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}}, {'sliceSSH' : 20, 'sliceVIP' : 20, 'sliceVID' : 20, 'sliceLVD' : 20, 'sliceFDO' : 20}, 1000, 100000, 1000)

# fetchAlgResultsManTests('baselineTestNS_2sli_LVD-BWS_AlgoTest', [0.0, 0.5, 1.0], {'sliceDES' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBWS' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'sliceDES' : 50, 'sliceBWS' : 50}, 1000, 100000, 1000)

# fetchAlgResultsManTests(testName, alpha, basicSliConfig, basicSliBand, rbSize, linkBand, numAlgRounds)
# fetchAlgResults('cliNums[5-20-50-75-100]', [0.0, 0.5, 1.0], {'sliceDES' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBWS' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'sliceDES' : 50, 'sliceBWS' : 50}, 1000, 100000, 1000, '2sliLVD_BWSTestVariousCliNums[5-20-50-75-100]Fairness1')


if __name__ == "__main__":
    print('MAIN')
    # 5 slices algorithm

    # algorithm({'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}}, {'sliceSSH' : 20, 'sliceVIP' : 20, 'sliceVID' : 20, 'sliceLVD' : 20, 'sliceFDO' : 20}, 1000, 0.0, 0, 1000, 100, False)
    # algorithm({'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}}, {'sliceSSH' : 20, 'sliceVIP' : 20, 'sliceVID' : 20, 'sliceLVD' : 20, 'sliceFDO' : 20}, 1000, 0.5, 0, 1000, 100, False)
    # algorithm({'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}}, {'sliceSSH' : 20, 'sliceVIP' : 20, 'sliceVID' : 20, 'sliceLVD' : 20, 'sliceFDO' : 20}, 1000, 1.0, 0, 1000, 100, False)

    # 2 sli lvd in band
    
    # algorithm({'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'sliceDel' : 50, 'sliceBand' : 50}, 1000, 0.0, 0.0, 1000, 100, False)
    # algorithm({'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'sliceDel' : 50, 'sliceBand' : 50}, 1000, 0.5, 0.0, 1000, 100, False)
    # algorithm({'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'sliceDel' : 50, 'sliceBand' : 50}, 1000, 1.0, 0.0, 1000, 100, False)

    # alphaTester({'Delay' : {'hostSSH' : 50, 'hostLVD' : 50, 'hostVIP' : 50}, 'Bandwidth' : {'hostVID' : 50, 'hostFDO' : 50}}, {'Delay' : 50, 'Bandwidth' : 50}, 1000, 1000, '2sliLVD_DESAlphaTest2')
    # alphaTester({'Delay' : {'hostSSH' : 50, 'hostVIP' : 50}, 'Bandwidth' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'Delay' : 50, 'Bandwidth' : 50}, 1000, 1000, '2sliLVD_BWSAlphaTest2')
    # alphaTester({'Delay' : {'hostSSH' : 50, 'hostVIP' : 50}, 'Bandwidth' : {'hostVID' : 50, 'hostFDO' : 50}}, {'Delay' : 50, 'Bandwidth' : 50}, 1000, 1000, '2sli4AppsAlphaTest2')

    # alphaBetaTester({'slice1' : {'hostSSH' : 50}, 'slice2' : {'hostVIP' : 50}, 'slice3' : {'hostVID' : 50}, 'slice5' : {'hostFDO' : 50}}, {'slice1' : 20, 'slice2' : 20, 'slice3' : 20, 'slice5' : 20}, 1000, 1000, '4sliAlphaBetaTest1')
    # alphaBetaTester({'slice1' : {'hostSSH' : 50}, 'slice2' : {'hostVIP' : 20}, 'slice3' : {'hostVID' : 40}, 'slice4' : {'hostLVD' : 10}, 'slice5' : {'hostFDO' : 20}}, {'slice1' : 20, 'slice2' : 20, 'slice3' : 20, 'slice4' : 20, 'slice5' : 20}, 1000, 1000, '5sliAlphaBetaTest5')
    # alphaTester({'slice1' : {'hostSSH' : 50}, 'slice2' : {'hostVIP' : 20}, 'slice3' : {'hostVID' : 40}, 'slice4' : {'hostLVD' : 10}, 'slice5' : {'hostFDO' : 20}}, {'slice1' : 20, 'slice2' : 20, 'slice3' : 20, 'slice4' : 20, 'slice5' : 20}, 1000, 1000, '5sliAlphaBetaTest5')

    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTest50eachMinMos1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 10}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewFileMinMos1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 10}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewLiveMinMos1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 10}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewVoDMinMos1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 10}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewVoIPMinMos1')
    # alphaTester({'SSH' : {'hostSSH' : 10}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewSSHMinMos1')

    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTest50eachFairness1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 10}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewFileFairness1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 10}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewLiveFairness1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 10}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewVoDFairness1')
    # alphaTester({'SSH' : {'hostSSH' : 50}, 'VoIP' : {'hostVIP' : 10}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewVoIPFairness1')
    # alphaTester({'SSH' : {'hostSSH' : 10}, 'VoIP' : {'hostVIP' : 50}, 'VoD' : {'hostVID' : 50}, 'Live' : {'hostLVD' : 50}, 'File' : {'hostFDO' : 50}}, {'SSH' : 20, 'VoIP' : 20, 'VoD' : 20, 'Live' : 20, 'File' : 20}, 1000, 1000, '5sliAlphaTestFewSSHFairness1')

    # variousCliNumTester({'sliceSSH' : {'hostSSH' : 5}, 'sliceVIP' : {'hostVIP' : 20}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 75}, 'sliceFDO' : {'hostFDO' : 100}}, 1000, 100000, 1000, [0.0, 0.5, 1.0], '5sliTestVariousCliNums[5-20-50-75-100]Fairness1')

    # rbSizeTester({'sliceSSH' : {'hostSSH' : 50}, 'sliceVIP' : {'hostVIP' : 50}, 'sliceVID' : {'hostVID' : 50}, 'sliceLVD' : {'hostLVD' : 50}, 'sliceFDO' : {'hostFDO' : 50}}, {'sliceSSH' : 0.2, 'sliceVIP' : 0.2, 'sliceVID' : 0.2, 'sliceLVD' : 0.2, 'sliceFDO' : 0.2}, [10, 20, 50, 100, 200, 250, 400, 500, 1000], 100000, 10000, 0.33, 0.33, '5sliRbSizeTest1')
    # rbSizeTester({'sliceDel' : {'hostSSH' : 50, 'hostLVD' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostFDO' : 50}}, {'sliceDel' : 0.50, 'sliceBand' : 0.50}, [10, 20, 50, 100, 200, 250, 500, 1000], 100000, 10000, 0.33, 0.33, '2sliLVD_DESRbSizeTest1')
    # rbSizeTester({'sliceDel' : {'hostSSH' : 50, 'hostVIP' : 50}, 'sliceBand' : {'hostVID' : 50, 'hostLVD' : 50, 'hostFDO' : 50}}, {'sliceDel' : 0.50, 'sliceBand' : 0.50}, [10, 20, 50, 100, 200, 250, 500, 1000], 100000, 10000, 0.33, 0.33, '2sliLVD_BWSRbSizeTest1')