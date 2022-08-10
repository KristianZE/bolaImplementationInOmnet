import scipy.interpolate
import numpy
import sys

# Predict the MOS value for SSH
def predictSSHmos(rtt):
    # Construct a function that can be used to predict the MOS value using extrapolation
    # The values used for it are taken from Casas, P., Seufert, M., Egger, S., & Schatz, R. (2013, May). Quality of experience in remote virtual desktop services. In 2013 IFIP/IEEE International Symposium on Integrated Network Management (IM 2013) (pp. 1352-1357). IEEE.
    # They are present in Figure 5a of this paper. Values taken from the Figure:
    #   X values: 0, 50, 150, 200, 350, 500 in miliseconds
    #   Y values: 4.3, 4.25, 3.7, 3.65, 2.95, 2.6
    x = [0,50,150,200,350,500]
    y = [4.3, 4.25, 3.7, 3.65, 2.95, 2.6]
    interpFunction = scipy.interpolate.interp1d(x, y, kind='linear', fill_value='extrapolate', assume_sorted=True)
    predictedMOS = interpFunction(rtt)
    if predictedMOS > 5:
        predictedMOS = 5
    if predictedMOS < 1:
        predictedMOS = 1
    return predictedMOS

if __name__ == "__main__":
    inputRTT = sys.argv[1]
    outFile = sys.argv[2]
    pMOS = predictSSHmos(inputRTT)
    with open(outFile, 'w') as outfile:
        outfile.write(str(pMOS))