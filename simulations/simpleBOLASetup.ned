//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

package improved5gns.simulations;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import inet.visualizer.common.IntegratedVisualizer;
import inet.visualizer.common.InterfaceTableVisualizer;
import ned.DatarateChannel;
import inet.node.internetcloud.InternetCloud;
//
// TODO documentation
//
network simpleBOLASetup
{
    parameters:
        @display("bgb=710,417");
        int nVID = default(1); // Number of video clients
    types:
        channel C extends DatarateChannel
        {
        }
    submodules:
        configurator: Ipv4NetworkConfigurator {
            @display("p=10,10;is=s");
        }
        hostVID[nVID]: StandardHost;
        router0: Router {
            @display("p=233,203");
        }
        router1: Router {
            @display("p=438,203");
        }
        visualizer: IntegratedVisualizer {
            @display("p=18,71");
        }
        serverVID: StandardHost {
            @display("p=560,53");
        }
    connections:
        router0.pppg++ <--> conn1: C { datarate = 10Gbps; delay = 100ns; } <--> router1.pppg++;

        for i=0..nVID-1 {
            hostVID[i].pppg++ <--> C {  datarate = 10Gbps; delay = 100ns; } <--> router0.pppg++;
        }
        serverVID.pppg++ <--> C {  datarate = 10Gbps; delay = 100ns; } <--> router1.pppg++;
}
