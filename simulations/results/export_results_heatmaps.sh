#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -n numRuns -s sourceFolder -o resultsFolder -t resultsSubfolder -d experimentDescriptor"
   echo -e "\t-n Number of runs from which to export scalars and vecorts into .csv files"
   echo -e "\t-r Number of slices in the experiment"
   echo -e "\t-s Folder which contains the source .vec and .sca files"
   echo -e "\t-o Destination folder"
   echo -e "\t-t Destination subfolder"
   echo -e "\t-d Descriptor of the experiment"
   exit 1 # Exit script after printing help
}

while getopts "n:r:s:o:t:d:" opt
do
   case "$opt" in
      n ) numRuns="$OPTARG" ;;
      r ) numSlices="$OPTARG" ;;
      s ) sourceFolder="$OPTARG" ;;
      o ) resultsFolder="$OPTARG" ;;
      t ) resultsSubfolder="$OPTARG" ;;
      d ) experimentDescriptor="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$numRuns" ] || [ -z "$sourceFolder" ] || [ -z "$resultsFolder" ] || [ -z "$resultsSubfolder" ] || [ -z "$experimentDescriptor" ]
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
lastResult=$(($numRuns - 1))

for run_num in $(eval echo "{$firstResult..$lastResult}")
do
    nVID=$(perl -nle'print $& while m{(?<=nVID )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nFDO=$(perl -nle'print $& while m{(?<=nFDO )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nSSH=$(perl -nle'print $& while m{(?<=nSSH )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    nVIP=$(perl -nle'print $& while m{(?<=nVIP )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)

    tp=$(perl -nle'print $& while m{(?<=TP )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)
    delay=$(perl -nle'print $& while m{(?<=del )[0-9]+}g' ${sourceFolder}/*-${run_num}.vci)

    lastVID=$(($nVID - 1))
    lastFDO=$(($nFDO - 1))
    lastSSH=$(($nSSH - 1))
    lastVIP=$(($nVIP - 1))
    lastSlice=$(($numSlices - 1))

    totalNum=$(($nVID + $nFDO + $nSSH + $nVIP))

    echo "Total number of clients in run: $totalNum. This includes:"
    echo -e "\t- $nVID video or live video clients"
    echo -e "\t- $nFDO file download clients"
    echo -e "\t- $nSSH SSH clients"
    echo -e "\t- $nVIP VoIP clients"

    subfolderName="${resultsSubfolder}_${totalNum}_VID${nVID}_FDO${nFDO}_SSH${nSSH}_VIP${nVIP}"
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
    
    echo "Exporting run $run_num which has $totalNum clients..."
    echo -e "\tExporting for router0:\t\t\c"
    opp_scavetool export -f "module=~"*router0.ppp[0]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_router0_vec.csv ${sourceFolder}/*-${run_num}.vec
    echo -e "\tExporting for router1:\t\t\c"
    opp_scavetool export -f "module=~"*router1.ppp[0]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_router1_vec.csv ${sourceFolder}/*-${run_num}.vec
    if (( lastVID >= firstResult ))
    then
        for cli_num in $(eval echo "{$firstResult..$lastVID}")
        do
            echo -e "\tExporting for video client $cli_num:\t\t\c"
            opp_scavetool export -f "module=~"*hostVID[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_hostVID${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
        done
        echo -e "\tExporting for video server:\t\t\c"
        opp_scavetool export -f "module=~"*serverVID*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_serverVID_vec.csv ${sourceFolder}/*-${run_num}.vec
    fi
    if (( lastFDO >= firstResult ))
    then
        for cli_num in $(eval echo "{$firstResult..$lastFDO}")
        do
            echo -e "\tExporting for file download client $cli_num:\t\c"
            opp_scavetool export -f "module=~"*hostFDO[$cli_num]*" " -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_hostFDO${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
        done
        echo -e "\tExporting for file download server:\t\t\c"
        opp_scavetool export -f "module=~"*serverFDO*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_serverFDO_vec.csv ${sourceFolder}/*-${run_num}.vec
    fi
    if (( lastSSH >= firstResult ))
    then
        for cli_num in $(eval echo "{$firstResult..$lastSSH}")
        do
            echo -e "\tExporting for SSH client $cli_num:\t\t\c"
            opp_scavetool export -f "module=~"*hostSSH[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_hostSSH${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
        done
        echo -e "\tExporting for SSH server:\t\t\c"
        opp_scavetool export -f "module=~"*serverSSH*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_serverSSH_vec.csv ${sourceFolder}/*-${run_num}.vec
    fi
    if (( lastVIP >= firstResult ))
    then
        for cli_num in $(eval echo "{$firstResult..$lastVIP}")
        do
            echo -e "\tExporting for VoIP client $cli_num:\t\t\c"
            opp_scavetool export -f "module=~"*hostVIP[$cli_num]*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_hostVIP${cli_num}_vec.csv ${sourceFolder}/*-${run_num}.vec
        done
        echo -e "\tExporting for VoIP server:\t\t\c"
        opp_scavetool export -f "module=~"*serverVIP*""  -F CSV-S -o ${resultsFolder}/${subfolderName}/${experimentDescriptor}_tp${tp}_del${delay}_serverVIP_vec.csv ${sourceFolder}/*-${run_num}.vec
    fi

done

echo -e "Exports complete :)"