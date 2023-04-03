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
import inet.node.inet.Router;
import inet.node.inet.StandardHost;


//
// TODO documentation
//
network Network
{
    @display("bgb=608,525");
    submodules:
        router0: Router {
            @display("p=216,262");
        }
        router1: Router {
            @display("p=373,262");
        }
        server: StandardHost {
            @display("p=516.304,261.326");
        }
        client: StandardHost {
            @display("p=74,262");
        }
    connections:
        client.pppg[0] <--> router0.pppg[0];
        router1.pppg[0] <--> server.pppg[0];
        router0.pppg[0] <--> router1.pppg[0];
}

