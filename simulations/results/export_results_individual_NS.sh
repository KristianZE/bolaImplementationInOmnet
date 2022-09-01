#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -n numRuns -s sourceFolder -o resultsFolder -t resultsSubfolder -d experimentDescriptor"
   echo -e "\t-f Number of the first run to export"
   echo -e "\t-l Number of the first run to exports"
   echo -e "\t-r Number of slices in the experiment"
   echo -e "\t-s Folder which contains the source .vec and .sca files"
   echo -e "\t-o Destination folder"
   echo -e "\t-t Destination subfolder"
   echo -e "\t-d Descriptor of the experiment"
   exit 1 # Exit script after printing help
}

while getopts "f:l:r:s:o:t:d:" opt
do
   case "$opt" in
      f ) firstRun="$OPTARG" ;;
      l ) lastRun="$OPTARG" ;;
      r ) numSlices="$OPTARG" ;;
      s ) sourceFolder="$OPTARG" ;;
      o ) resultsFolder="$OPTARG" ;;
      t ) resultsSubfolder="$OPTARG" ;;
      d ) experimentDescriptor="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$firstRun" ] || [ -z "$lastRun" ] || [ -z "$sourceFolder" ] || [ -z "$resultsFolder" ] || [ -z "$resultsSubfolder" ] || [ -z "$experimentDescriptor" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

if [ -d "${sourceFolder}" ] 
then
    echo "Source directory ${sourceFolder} exists. Continuing..." 
else
    echo "Error: Source directory ${sourceFolder} does not exist. Quitting..."
    exit 2
fi

if [ -d "${resultsFolder}" ] 
then
    echo "Results directory ${resultsFolder} exists. Continuing..." 
else
    echo "Results directory ${resultsFolder} does not exist. Creating the directory..."
    mkdir ${resultsFolder}
    if [ -d "${resultsFolder}" ] 
    then
        echo "Results directory ${resultsFolder} successfully created. Continuing..." 
    else
        echo "Error: Results directory ${resultsFolder} Couldn't be created. Quitting..."
        exit 3
    fi
fi

firstResult=0

for run_num in $(eval echo "{$firstRun..$lastRun}")
do
    nVID=$(perl -nle'print $& while m{(?<=nVID )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nLVD=$(perl -nle'print $& while m{(?<=nLVD )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nFDO=$(perl -nle'print $& while m{(?<=nFDO )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nSSH=$(perl -nle'print $& while m{(?<=nSSH )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nVIP=$(perl -nle'print $& while m{(?<=nVIP )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    ncVIP=$(perl -nle'print $& while m{(?<=ncVIP )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)


    lastVID=$(($nVID - 1))
    lastLVD=$(($nLVD - 1))
    lastFDO=$(($nFDO - 1))
    lastSSH=$(($nSSH - 1))
    lastVIP=$(($nVIP - 1))
    lastcVIP=$(($ncVIP - 1))
  
    lastSlice=$(($numSlices - 1))

    totalNum=$(($nVID + $nFDO + $nSSH + $nVIP + $nLVD + $ncVIP))

    echo "Total number of clients in run: $totalNum. This includes:"
    echo -e "\t- $nVID video clients"
    echo -e "\t- $nLVD live video clients"
    echo -e "\t- $nFDO file download clients"
    echo -e "\t- $nSSH SSH clients"
    echo -e "\t- $nVIP VoIP clients"
    echo -e "\t- $ncVIP cVoIP clients"




    subfolderName="${resultsSubfolder}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}"
    echo "Subfolder name: $subfolderName"
    if [ -d "${resultsFolder}/${subfolderName}" ] 
    then
        echo "Vectors directory ${resultsFolder}/${subfolderName} exists. Continuing..." 
    else
        echo "Results directory ${resultsFolder}/${subfolderName} does not exist. Creating the directory..."
        mkdir ${resultsFolder}/${subfolderName}
        if [ -d "${resultsFolder}/${subfolderName}" ] 
        then
            echo "Results directory ${resultsFolder}/${subfolderName} successfully created. Continuing..." 
        else
            echo "Error: Results directory ${resultsFolder}/${subfolderName} Couldn't be created. Quitting..."
            exit 4
        fi
    fi
    
    if [ -d "${resultsFolder}/${subfolderName}/vectors" ] 
    then
        echo "Vectors directory ${resultsFolder}/${subfolderName}/vectors exists. Continuing..." 
    else
        echo "Results directory ${resultsFolder}/${subfolderName}/vectors does not exist. Creating the directory..."
        mkdir ${resultsFolder}/${subfolderName}/vectors
        if [ -d "${resultsFolder}/${subfolderName}/vectors" ] 
        then
            echo "Results directory ${resultsFolder}/${subfolderName}/vectors successfully created. Continuing..." 
        else
            echo "Error: Results directory ${resultsFolder}/${subfolderName}/vectors Couldn't be created. Quitting..."
            exit 4
        fi
    fi

    if [ -d "${resultsFolder}/${subfolderName}/scalars" ] 
    then
        echo "Vectors directory ${resultsFolder}/${subfolderName}/scalars exists. Continuing..." 
    else
        echo "Results directory ${resultsFolder}/${subfolderName}/scalars does not exist. Creating the directory..."
        mkdir ${resultsFolder}/${subfolderName}/scalars
        if [ -d "${resultsFolder}/${subfolderName}/scalars" ] 
        then
            echo "Results directory ${resultsFolder}/${subfolderName}/scalars successfully created. Continuing..." 
        else
            echo "Error: Results directory ${resultsFolder}/${subfolderName}/scalars Couldn't be created. Quitting..."
            exit 4
        fi
    fi
    
    echo "Exporting run $run_num which has $totalNum clients..."
    for sliNum in $(eval echo "{$firstResult..$lastSlice}")
    do
        echo -e "\tExporting for resource link $sliNum:\t\t\c"
        opp_scavetool export -f "module=~"*router0.ppp[$sliNum]*" AND name=~"*xPk*" "  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_resAllocLink${sliNum}_vec.csv ${sourceFolder}/*-${run_num}.vec
        
    done
    # echo -e "\tExporting dequeueIndex for router0:\t\t\c"
    # opp_scavetool export -f "module(*router0*) AND name(*dequeueIndex*)"  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_router0_dI_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting dequeueIndex for router1:\t\t\c"
    # opp_scavetool export -f "module(*router1*) AND name(*dequeueIndex*)"  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_router1_dI_vec.csv ${sourceFolder}/*-${run_num}.vec
    # opp_scavetool export -f "(module(*router0.ppp[0]*) AND name(*xPk*)) OR (module(*router0.ppp[1]*) AND name(*xPk*)) OR (module(*router0.ppp[2]*) AND name(*xPk*)) OR (module(*router0.ppp[3]*) AND name(*xPk*))"  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_links_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting for server serverSSH:\t\t\c"
    # opp_scavetool export -f "(module(*serverSSH*) AND name(*RTO*)) OR (module(*serverSSH*) AND name(*advertised*))" -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_serverSSH_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting for server serverVID:\t\t\c"
    # opp_scavetool export -f "(module(*serverVID*tcp*))" -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_serverVID_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting for server serverLVD:\t\t\c"
    # opp_scavetool export -f "(module(*serverLVD*tcp*))" -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_serverLVD_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting for server serverFDO:\t\t\c"
    # opp_scavetool export -f "(module(*serverFDO*tcp*))" -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_serverFDO_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting for router0:\t\t\c"
    # opp_scavetool export -f "module(*router0*) AND name(*queueLength*)"  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_router0_qL_vec.csv ${sourceFolder}/*-${run_num}.vec
    # echo -e "\tExporting for router1:\t\t\c"
    # opp_scavetool export -f "module(*router1.ppp[0]*) AND name(*queueLength*)"  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_router1_qL_vec.csv ${sourceFolder}/*-${run_num}.vec
    
    for cli_num in $(eval echo "{$firstResult..$lastVID}")
    do
        echo -e "\tExporting for video client $cli_num:\t\t\c"
        opp_scavetool export -f "module=~"*hostVID[$cli_num]*"" -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_hostVID${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
    done
    for cli_num in $(eval echo "{$firstResult..$lastLVD}")
    do
        echo -e "\tExporting for live video client $cli_num:\t\t\c"
        opp_scavetool export -f "module=~"*hostLVD[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_hostLVD${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
    done
    for cli_num in $(eval echo "{$firstResult..$lastFDO}")
    do
        echo -e "\tExporting for file download client $cli_num:\t\c"
        opp_scavetool export -f "module=~"*hostFDO[$cli_num]*"" -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_hostFDO${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
    done
    for cli_num in $(eval echo "{$firstResult..$lastSSH}")
    do
        echo -e "\tExporting for SSH client $cli_num:\t\t\c"
        opp_scavetool export -f "module=~"*hostSSH[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_hostSSH${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
    done
    for cli_num in $(eval echo "{$firstResult..$lastVIP}")
    do
        echo -e "\tExporting for VoIP client $cli_num:\t\t\c"
        opp_scavetool export -f "module=~"*hostVIP[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_hostVIP${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
    done
    for cli_num in $(eval echo "{$firstResult..$lastcVIP}")
    do
        echo -e "\tExporting for cVIP client $cli_num:\t\t\c"
        opp_scavetool export -f "module=~"*hostcVIP[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/vectors/${experimentDescriptor}_${totalNum}_VID${nVID}_LVD${nLVD}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}_cVIP${ncVIP}_hostcVIP${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
    done
   



done

echo -e "Exports complete :)"