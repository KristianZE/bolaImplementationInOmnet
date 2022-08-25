#!/bin/bash

helpFunction()
{
   echo ""
   echo "Will run a single run from a single config and ini file."
   echo "Usage: $0 -i iniFile -c config -t numThreads"
   echo -e "\t-i Omnet++ INI file containing the congfig to run"
   echo -e "\t-c Config for the scenario you want to run"
   echo -e "\t-s Number of slices in the scenario you want to run"
   exit 1 # Exit script after printing help
}

while getopts "i:c:s:" opt
do
   case "$opt" in
      i ) iniFile="$OPTARG" ;;
      c ) config="$OPTARG" ;;
      s ) slices="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$iniFile" ] || [ -z "$config" ] || [ -z "$slices" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

###### Run a single simulation config. Note: The config should only have one run here!!! ######
###### You may need to relink the paths depending on your machine!!!!! ######

#../src/ml_qoe ${iniFile} -u Cmdenv -c ${config} -m -n .:../src:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/src:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/examples:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/tutorials:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/showcases -l /Users/marijagajic/omnetpp-6.0pre15/samples/inet/src/INET
#../src/rndm ${iniFile} -u Cmdenv -c ${config} -m -n .:../src:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/src:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/examples:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/tutorials:/Users/marijagajic/omnetpp-6.0pre15/samples/inet/showcases -l /Users/marijagajic/omnetpp-6.0pre15/samples/inet/src/INET 
../src/improved5gNS ${iniFile} -m -u Cmdenv -c ${config} -n .:../src:../../inet/examples:../../inet/showcases:../../inet/src:../../inet/tests/validation:../../inet/tests/networks:../../inet/tutorials:../../inet-gpl/src:../../inet-gpl/examples --image-path=../../inet/images -l ../../inet/src/INET -l ../../inet-gpl/src/INETGPL 


# ###### Export results from OMNet++ to csv ######
cd results
./export_results_individual_NS.sh -f 0 -l 0 -r ${slices} -s ${config} -o ../../analysis/${config} -t ${config} -d ${config}
# ### Export some queue scalars as well ###
# # ./export_results_individual_NS_onlyR1Queues.sh -f 0 -l 0 -r ${slices} -s ${config} -o ../../../analysis/${config} -t ${config} -d ${config}

#  ###### Extract necessary information from the csv's ######
cd ../../analysis/${config}
name=$(ls)
cd ../code
python3.9 parseResNe.py ${config} ${slices} ${name} # Extract required information from the scavetool csv's
# # Fix possibly broken MOS scores of VoD, Live and SSH (Which are calculated using python scripts during simulation. These scripts may randomly fail...)
cd sshMOScalcFiles/code
python3.9 recalcQoE.py ${config} ${name} # First take care of SSH
cd ../../videoMOScalcFiles/code 
python3.9 recalcQoE.py ${config} ${name} # Now take care of both video clients
cd ../..
python3.9 remakeMOSexports.py ${config} ${name} # Remake the mos results to include recalculated values
#python3.9 parseResInvestigation.py ${config} ${slices} ${name}

# # #rm -rf ../../5gNS/simulations/results/${config}/

# # ###### Plot basic plots ######
python3.9 plotResNE.py ${config} ${slices} ${name} # Plot everything
# # #python3.9 plotResPaper.py ${config} ${slices} ${name} # Plot everything
# # #python3.9 plotResInvestigation.py ${config} ${slices} ${name} # Plot everything

echo "Simulation, exports and initial plots are complete for ${config}";
