
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from subprocess import Popen, PIPE
from mininet.cli import CLI





if '__main__' == __name__:
  setLogLevel('info')


  net = Mininet(link=TCLink)
  key = "net.mptcp.mptcp_enabled"
  value = 1
  p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE, stderr=PIPE)
  stdout, stderr = p.communicate()
  print ("stdout=",stdout,"stderr=", stderr)
  laptop1 = net.addHost('laptop1')
  laptop2 = net.addHost('laptop2')
  linkopt={'bw':5}
  net.addLink(laptop2,laptop1,cls=TCLink, **linkopt)
  net.addLink(laptop2,laptop1,cls=TCLink, **linkopt)

  net.start()
  dumpNodeConnections(net.hosts)
  print(net.hosts)
  print("Testing Network Connectivity")
  net.pingAll()
  print("Testing bandwidth")
  net.iperf((laptop2,laptop1))
  CLI(net)
  net.stop()
