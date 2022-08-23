import xml.etree.ElementTree as ET
import numpy as np

# import delayEstimation as delEst
import qoeEstimation as qoeEst

import shutil
import math

def getBandForQoECli(host, desQoE):
    qoeEstimator = qoeEst.ClientQoeEstimator(host)
    qoe = np.array([qoeEstimator.estQoEb(x) for x in qoeEstimator.yAxis])
    # print(qoe)
    if host == 'hostLVD':
        desQoE += 0.1
    idx = np.abs(qoe - desQoE).argmin()
    while qoe[idx] < desQoE:
        idx += 1
    # print('\t-> Target:', desQoE, '; Selected:', qoe[idx], '; Bitrate:', qoeEstimator.yAxis[idx])
    return qoeEstimator.yAxis[idx]

# for app in ['hostVID', 'hostLVD', 'hostFDO', 'hostVIP', 'hostSSH']:
#     print(app)
#     for tQ in [3.0, 3.5, 4.0]:
#         getBandForQoECli(app, tQ)


# default: ceilMultiplier = 1.25; guaranteeMultiplier = 1.0
def simpleAdmission(availBand, desiredQoE, cliTypes, maxNumCliType, ceilMultiplier, guaranteeMultiplier):
    usedBand = 0
    numHostsPerType = {}
    reqBitratesPerType = {}
    for host in cliTypes:
        reqBitratesPerType[host] = getBandForQoECli(host, desiredQoE)
        print('For a QoE of', desiredQoE, host, 'needs', reqBitratesPerType[host])
        numHostsPerType[host] = 0
    ceilBitrates = {}
    assuredBitrates = {}
    for host in cliTypes:
        ceilBitrates[host] = reqBitratesPerType[host] * ceilMultiplier
        assuredBitrates[host] = reqBitratesPerType[host] * guaranteeMultiplier
    numSameRes = 0
    oldBand = 0
    while usedBand < availBand:
        for host in cliTypes:
            tryAdd = usedBand + assuredBitrates[host]
            if tryAdd <= availBand and numHostsPerType[host] < maxNumCliType:
                usedBand = tryAdd
                numHostsPerType[host] += 1
        if oldBand == usedBand:
            numSameRes += 1
        else:
            numSameRes = 0
        oldBand = usedBand
        if numSameRes > 10:
            break
    
    print('Hosts admitted for desired QoE of', desiredQoE, 'and link bitrate of', availBand, 'Kbps is :', numHostsPerType)
    print('This allocation will use', usedBand, 'Kbps out of available', availBand, 'Kbps')

    return numHostsPerType, assuredBitrates, ceilBitrates

# print(simpleAdmission(100000, 3, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50))
# simpleAdmission(200000, 3.5, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50)
# simpleAdmission(200000, 4, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50)

# print(simpleAdmission(100000, 2.5, ['hostVIP', 'hostSSH', 'hostVID', 'hostLVD', 'hostFDO'], 50, 2.0, 1.0))

# getBandForQoECli('hostFDO', 3)

def prepareHTBClassXML(configElem, classType, className, clParent, clRate, clCeil, clBurst, clCburst, clLevel, clQuantum, clMbuffer, clPrio, clQueueNum):
    classElem = ET.SubElement(configElem, 'class')
    classElem.set('id', classType+className)

    parentId = ET.SubElement(classElem, 'parentId')
    parentId.text = clParent

    rate = ET.SubElement(classElem, 'rate')
    rate.set('type', 'int')
    rate.text = clRate

    ceil = ET.SubElement(classElem, 'ceil')
    ceil.set('type', 'int')
    ceil.text = clCeil

    burst = ET.SubElement(classElem, 'burst')
    burst.set('type', 'int')
    burst.text = clBurst

    cburst = ET.SubElement(classElem, 'cburst')
    cburst.set('type', 'int')
    cburst.text = clCburst

    level = ET.SubElement(classElem, 'level')
    level.set('type', 'int')
    level.text = clLevel

    quantum = ET.SubElement(classElem, 'quantum')
    quantum.set('type', 'int')
    quantum.text = clQuantum

    mbuffer = ET.SubElement(classElem, 'mbuffer')
    mbuffer.set('type', 'int')
    mbuffer.text = clMbuffer

    if classType == 'leaf':
        prio = ET.SubElement(classElem, 'priority')
        prio.text = clPrio

        queueNum = ET.SubElement(classElem, 'queueNum')
        queueNum.set('type', 'int')
        queueNum.text = clQueueNum

# {leafName:[assuredRate, ceilRate, priority, queueNum]}
def genHTBconfig(configName, linkSpeed, leafClassesConfigs):

    configElem = ET.Element('config')
    prepareHTBClassXML(configElem, 'root', '', 'NULL', str(linkSpeed), str(linkSpeed), '1600', '1600', '1', '1600', '60', '', '')
    for leaf in leafClassesConfigs:
        prepareHTBClassXML(configElem, 'leaf', leaf, 'root', str(leafClassesConfigs[leaf][0]), str(leafClassesConfigs[leaf][1]), '1600', '1600', '0', '1600', '60', str(leafClassesConfigs[leaf][2]), str(leafClassesConfigs[leaf][3]))
    # prepareHTBClassXML(configElem, 'leaf', 'Two', 'root', '2000', '5000', '1600', '1600', '0', '1600', '60', '0', '1')

    # create a new XML file with the results
    mydata = ET.tostring(configElem)
    myfile = open('../5gNS/simulations/configs/htbTree/'+configName+"HTB.xml", "wb")
    myfile.write(mydata)
    # shutil.copy2(configName+"HTB.xml", '../5gNS/simulations/configs/htbTree')

# {leafName:[assuredRate, ceilRate, priority, queueNum, parentId, level]}
# {innerName:[assuredRate, ceilRate, parentId, level]}
def genHTBconfigWithInner(configName, linkSpeed, leafClassesConfigs, innerClassesConfigs, numLevels):

    configElem = ET.Element('config')
    prepareHTBClassXML(configElem, 'root', '', 'NULL', str(linkSpeed), str(linkSpeed), '2000', '2000', str(numLevels), '1500', '60', '', '')
    # prepareHTBClassXML(configElem, 'root', '', 'NULL', str(linkSpeed), str(linkSpeed), '1600', '1600', str(numLevels), '1600', '60', '', '')
    
    for inner in innerClassesConfigs:
        # print(inner)
        prepareHTBClassXML(configElem, 'inner', inner, str(innerClassesConfigs[inner][2]), str(innerClassesConfigs[inner][0]), str(innerClassesConfigs[inner][1]), '2000', '2000', str(innerClassesConfigs[inner][3]), '1500', '60', '', '')
        # prepareHTBClassXML(configElem, 'inner', inner, str(innerClassesConfigs[inner][2]), str(innerClassesConfigs[inner][0]), str(innerClassesConfigs[inner][1]), '1600', '1600', str(innerClassesConfigs[inner][3]), '1600', '60', '', '')
    
    for leaf in leafClassesConfigs:
        prepareHTBClassXML(configElem, 'leaf', leaf, str(leafClassesConfigs[leaf][4]), str(leafClassesConfigs[leaf][0]), str(leafClassesConfigs[leaf][1]), '2000', '2000', str(leafClassesConfigs[leaf][5]), '1500', '60', str(leafClassesConfigs[leaf][2]), str(leafClassesConfigs[leaf][3]))
        # prepareHTBClassXML(configElem, 'leaf', leaf, str(leafClassesConfigs[leaf][4]), str(leafClassesConfigs[leaf][0]), str(leafClassesConfigs[leaf][1]), '1600', '1600', str(leafClassesConfigs[leaf][5]), '1600', '60', str(leafClassesConfigs[leaf][2]), str(leafClassesConfigs[leaf][3]))
    
    
    # prepareHTBClassXML(configElem, 'leaf', 'Two', 'root', '2000', '5000', '1600', '1600', '0', '1600', '60', '0', '1')

    # create a new XML file with the results
    mydata = ET.tostring(configElem)
    myfile = open('../5gNS/simulations/configs/htbTree/'+configName+"HTB.xml", "wb")
    myfile.write(mydata)
    # shutil.copy2(configName+"HTB.xml", '../5gNS/simulations/configs/htbTree')

# genHTBconfig('stasTest10a', 10000, {'One':[4000, 7000, 0, 0], 'Two':[2000, 5000, 0, 1]})

def makeIPhostNum(ipPrefix, hostNum):
    ipString = ipPrefix + '.'
    ipString += str(hostNum // 64) + '.'
    ipString += str(4*hostNum % 256)
    return ipString

def genBaselineRoutingConfig(configName, hostTypes, hostNums, hostIPprefixes, serverTypes, serverIPprefixes):
    configElem = ET.Element('config')
    for host,nums in zip(hostTypes, hostNums):
        for num in range(nums):
            interfaceElem = ET.SubElement(configElem, 'interface')
            interfaceElem.set('hosts', host+'['+str(num)+']')
            interfaceElem.set('names', 'ppp0')
            interfaceElem.set('address', makeIPhostNum(hostIPprefixes[host],num))
            interfaceElem.set('netmask', '255.255.255.252')
        interfaceElem = ET.SubElement(configElem, 'interface')
        interfaceElem.set('hosts', 'router0')
        interfaceElem.set('towards', host+'[*]')
        interfaceElem.set('address', hostIPprefixes[host]+'.x.x')
        interfaceElem.set('netmask', '255.255.255.252')
    
    for server in serverTypes:
        interfaceElem = ET.SubElement(configElem, 'interface')
        interfaceElem.set('hosts', server)
        interfaceElem.set('names', 'ppp0')
        interfaceElem.set('address', serverIPprefixes[server]+'.0.0')
        interfaceElem.set('netmask', '255.255.255.252')
    

    interfaceElem = ET.SubElement(configElem, 'interface')
    interfaceElem.set('hosts', '**')
    interfaceElem.set('address', '10.x.x.x')
    interfaceElem.set('netmask', '255.x.x.x')
    


    # create a new XML file with the results
    mydata = ET.tostring(configElem)
    myfile = open('../5gNS/simulations/configs/baseQoS/'+configName+"Routing.xml", "wb")
    myfile.write(mydata)
    # shutil.copy2(configName+"Routing.xml", '../5gNS/simulations/configs/baseQoS')


# genBaselineRoutingConfig('stasTest10a', ['hostFDO'], [2], {'hostFDO':'10.3'}, ['serverFDO'],  {'serverFDO':'10.6'})

def genBaselineIniConfig(confName, base, numHostsPerType, hostIPprefixes, availBand, ceilMultiplier, guaranteeMultiplier):
    sumHosts = 0

    #packFilters = '\"'
    packDataFiltersR0 = '['
    packDataFiltersR1 = '['

    for host in numHostsPerType:
        numHostsType = numHostsPerType[host]
        sumHosts += numHostsType
        for num in range(numHostsType):
            #packFilters += '*;'
            packDataFiltersR0 += 'expr(ipv4.srcAddress.str() =~ \"' + makeIPhostNum(hostIPprefixes[host],num) + '\"),'
            packDataFiltersR1 += 'expr(ipv4.destAddress.str() =~ \"' + makeIPhostNum(hostIPprefixes[host],num) + '\"),'


    #packFilters = packFilters[:-1]
    packDataFiltersR0 = packDataFiltersR0[:-1]
    packDataFiltersR1 = packDataFiltersR1[:-1]

    #packFilters += ']'
    packDataFiltersR0 += ']'
    packDataFiltersR1 += ']'
    

    configString = '[Config ' + confName + ']\n'
    configString += 'description = \"Configuration for ' + confName + '. All five applications. QoS employed. Guarantee Multiplier: ' + str(guaranteeMultiplier) + '; Ceil multiplier: ' + str(ceilMultiplier) +'\"\n\n'
    configString += 'extends = ' + base + '\n\n'
    configString += '*.configurator.config = xmldoc(\"configs/baseQoS/' + confName + 'Routing.xml\")\n\n'
    if 'hostVID' in numHostsPerType:
        configString += '*.nVID = ' + str(numHostsPerType['hostVID']) + ' # Number of video clients\n'
    else: 
        configString += '*.nVID = 0 # Number of video clients\n'
    if 'hostLVD' in numHostsPerType:
        configString += '*.nLVD = ' + str(numHostsPerType['hostLVD']) + ' # Number of live video client\n'
    else: 
        configString += '*.nLVD = 0 # Number of live video client\n'
    if 'hostFDO' in numHostsPerType:
        configString += '*.nFDO = ' + str(numHostsPerType['hostFDO']) + ' # Number of file download clients\n'
    else: 
        configString += '*.nFDO = 0 # Number of file download clients\n'
    if 'hostSSH' in numHostsPerType:
        configString += '*.nSSH = ' + str(numHostsPerType['hostSSH']) + ' # Number of SSH clients\n'
    else: 
        configString += '*.nSSH = 0 # Number of SSH clients\n'
    if 'hostVIP' in numHostsPerType:
        configString += '*.nVIP = ' + str(numHostsPerType['hostVIP']) + ' # Number of VoIP clients\n\n'
    else: 
        configString += '*.nVIP = 0 # Number of VoIP clients\n\n'
    if 'hostcVP' in numHostsPerType:
        configString += '*.ncVP = ' + str(numHostsPerType['hostVIP']) + ' # Number of VoIP clients\n\n'
    else: 
        configString += '*.ncVP = 0 # Number of critical VoIP clients\n\n'
    configString += '*.router*.ppp[0].queue.typename = \"HtbQueue\"\n'
    configString += '*.router*.ppp[0].queue.numQueues = ' + str(sumHosts) + '\n'
    configString += '*.router*.ppp[0].queue.queue[*].typename = \"DropTailQueue\"\n'
    configString += '*.router*.ppp[0].queue.packetCapacity = -1\n'
    configString += '*.router*.ppp[0].queue.htbHysterisis = false\n'
    configString += '*.router*.ppp[0].queue.scheduler.adjustHTBTreeValuesForCorectness = false\n'
    configString += '*.router*.ppp[0].queue.scheduler.checkHTBTreeValuesForCorectness = false\n'
    configString += '*.router*.ppp[0].queue.htbTreeConfig = xmldoc(\"configs/htbTree/' + confName + 'HTB.xml\")\n'
    configString += '*.router*.ppp[0].queue.classifier.defaultGateIndex = 0\n'
    configString += '*.router0.ppp[0].queue.classifier.packetFilters = ' + packDataFiltersR0 + '\n'
    configString += '*.router1.ppp[0].queue.classifier.packetFilters = ' + packDataFiltersR1 + '\n\n'

    configString += '**.connFIX0.datarate = ' + str(math.ceil(availBand)) + 'Mbps\n'
    configString += '**.connFIX0.delay = 40ms\n\n\n'

    f = open(confName+".txt", "w")
    f.write(configString)
    f.close()

    f2 = open('../5gNS/simulations/parameterStudyConfiguration.ini', 'a')
    f2.write(configString)
    f2.close()
    # print(configString)


def genAllSliConfigsHTBRun(configName, baseName, availBand, desiredQoE, types, hostToSlice, sliceNames, maxNumCliType, baseNumCli, ceilMultiplier, guaranteeMultiplier, differentiatePrios):
    cliTypes = ['host'+x for x in types]
    serverTypes = ['server'+x for x in types]
    numHostsPerType, reqBitratesPerType, ceilBitrates = simpleAdmission(availBand*1000, desiredQoE, ['host'+x for x in types], maxNumCliType, ceilMultiplier, guaranteeMultiplier)
    
    hostIPprefixes = {}
    serverIPprefixes = {}
    leafClassesConfigs = {}
    innerClassConfigs = {}
    queueInt = 0
    # {leafName:[assuredRate, ceilRate, priority, queueNum, parentId, level]}
    # {innerName:[assuredRate, ceilRate, parentId, level]}
    numLev = 2
    for sliNum in range(len(hostToSlice)):
        sumGuaranteesBandSli = 0
        parentName = 'inner'+sliceNames[sliNum]
        if sliceNames[sliNum] == 'connFIX0':
            parentName = 'root'
            numLev = 1
        for hType in hostToSlice[sliNum]:
            host = 'host'+hType
            priority = 0
            if differentiatePrios == True and host != 'hostVIP' and host != 'hostSSH':
                priority = 1
            for num in range(numHostsPerType[host]):
                leafClassesConfigs[host+str(num)] = [reqBitratesPerType[host], ceilBitrates[host], priority, queueInt, parentName, 0]
                queueInt += 1
            defaultBitrateHost = getBandForQoECli(host, desiredQoE)
            # print(defaultBitrateHost)
            sumGuaranteesBandSli += baseNumCli * defaultBitrateHost
            if sumGuaranteesBandSli < reqBitratesPerType[host] * numHostsPerType[host]:
                raise ValueError('Slice GBR does not match!!')
            print(maxNumCliType, numHostsPerType[host], reqBitratesPerType[host], guaranteeMultiplier, sumGuaranteesBandSli, reqBitratesPerType[host] * numHostsPerType[host])
        if sliceNames[sliNum] != 'connFIX0':
            # For inner class: assured, guaranteed, parent, level
            innerClassConfigs[sliceNames[sliNum]] = [sumGuaranteesBandSli, sumGuaranteesBandSli, 'root', 1]
        # print(list(leafClassesConfigs.keys())[0],':',leafClassesConfigs[list(leafClassesConfigs.keys())[0]])
        # print(list(innerClassConfigs.keys())[0],':',innerClassConfigs[list(innerClassConfigs.keys())[0]])
        

    prefIPno = 0
    for host in cliTypes:
        hostIPprefixes[host] = '10.'+str(prefIPno)
        prefIPno += 1
    prefIPno = 0
    for server in serverTypes:
        serverIPprefixes[server] = '10.'+str(prefIPno+10)
        prefIPno += 1

    genHTBconfigWithInner(configName, availBand*1000, leafClassesConfigs, innerClassConfigs, numLev)
    hostNums = [numHostsPerType[x] for x in numHostsPerType]
    genBaselineRoutingConfig(configName, cliTypes, hostNums, hostIPprefixes, serverTypes, serverIPprefixes)
    genBaselineIniConfig(configName, baseName, numHostsPerType, hostIPprefixes, availBand, ceilMultiplier, guaranteeMultiplier)

    f2 = open('../5gNS/simulations/'+configName.split('-')[0]+'.txt', 'a+')
    f2.write('./runAndExportSimConfig.sh -i parameterStudyConfiguration.ini -c ' + configName + ' -s 1\n')
    f2.close()

####################################################################
# # Settings for parameter study for the VoIP client
# targetQoE = [3.5]
# assuredMulti = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]
# # assuredMulti = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
# rates = [100]
# defaultNumClients = 100
# ceils = [1.0, 1.25, 1.5, 1.75, 2.0]
# # ceils = [1.0, 1.5, 2.0]
# dPrio = [False]
# client = 'VIP'
# studyName = 'parameterStudyVoIPV2'

####################################################################
# # Settings for parameter study for the SSH client
# targetQoE = [3.5]
# assuredMulti = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]
# # assuredMulti = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
# rates = [100]
# defaultNumClients = 100
# ceils = [1.0, 1.25, 1.5, 1.75, 2.0]
# # ceils = [1.0, 1.5, 2.0]
# dPrio = [False]
# client = 'SSH'
# studyName = 'parameterStudySecureShellV2'

####################################################################
# # Settings for parameter study for the VoD client
# targetQoE = [3.5]
# assuredMulti = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]
# # assuredMulti = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
# rates = [100]
# defaultNumClients = 100
# ceils = [1.0, 1.25, 1.5, 1.75, 2.0]
# # ceils = [1.0, 1.5, 2.0]
# dPrio = [False]
# client = 'VID'
# studyName = 'parameterStudyVoDV2'

####################################################################
# # Settings for parameter study for the Live client
# targetQoE = [3.5]
# assuredMulti = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]
# # assuredMulti = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
# rates = [100]
# defaultNumClients = 100
# ceils = [1.0, 1.25, 1.5, 1.75, 2.0]
# # ceils = [1.0, 1.5, 2.0]
# dPrio = [False]
# client = 'LVD'
# studyName = 'parameterStudyLiveV2'

####################################################################
# # Settings for parameter study for the File Download client
# targetQoE = [3.5]
# assuredMulti = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]
# rates = [100]
# defaultNumClients = 100
# # ceils = [1.0, 1.25, 1.5, 1.75, 2.0]
# ceils = [1.0, 1.5, 2.0, 1.25, 1.75]
# dPrio = [False]
# client = 'FDO'
# studyName = 'parameterStudyFileDownloadV2'

counter = 0
for rate in rates:
    for qoE in targetQoE:
        for ceil in ceils:
            rate = getBandForQoECli('host'+client, qoE)*defaultNumClients/1000
            # for mult1 in assuredMulti:
            #     maxCli = int(defaultNumClients/mult1)
            #     for mult in [x for x in assuredMulti if x < mult1]:
            #         # print(int(defaultNumClients/mult1))
            #         for dp in dPrio:
            #             print(maxCli, mult, ceil)
            #             # genAllSliConfigsHTBRun(studyName+'-maxCli'+str(maxCli)+'_R'+str(int(rate))+'_Q'+str(int(qoE*10))+'_M'+str(int(mult*100))+'_C'+str(int(ceil*100))+'_P'+str(dp), 'liteCbaselineTestTokenQoS_base', rate, qoE, [client], [[client]], ['connFIX0'], maxCli, defaultNumClients, ceil, mult, dp)
            #             counter += 1
            for mult in assuredMulti:
                maxCli = int(defaultNumClients/mult)
                for dp in dPrio:
                    print(maxCli, mult, ceil)
                    # counter+=1
                    genAllSliConfigsHTBRun(studyName+'-maxCli'+str(maxCli)+'_R'+str(int(rate))+'_Q'+str(int(qoE*10))+'_M'+str(int(mult*100))+'_C'+str(int(ceil*100))+'_P'+str(dp), 'liteCbaselineTestTokenQoS_base', rate, qoE, [client], [[client]], ['connFIX0'], maxCli, defaultNumClients, ceil, mult, dp)
                    counter += 1
print(counter)