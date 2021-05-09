# Safe_UDP
Computer Networks Assignment (BITS Hyderabad: 2nd Sem 2020-2021). 
A reliable implementation over UDP

Application: Uploading service, transfer of files from client to server.


## Running the application

Run the application in two terminals
Start the server side first

``` python filetransfer_server.py ```

``` python filetransfer_client.py ```

Client will prompt you to enter the name of the file to transfer, enter that
by default it will be "tosend.txt"

After the successful run of the program, you will see the file named "received.txt" with your data


## Working

The application files : filtransfer_client, filetransfer_server call the instances of the custom made protocol SUDP (SafeUDP), reliable data transfer implementation over UDP, using the Selective Repeat paradigm

The SUDPServer and SUDPClient communicate with each other using threads, that are mutually blocked to ensure smooth data transmission, any dropped or corrupted packets are informed of, using the timer or socket channel and retransmitted.

For reference: [RUDP RFC](https://tools.ietf.org/html/rfc908)

## Testing 

To install Mininet

```  pip install mininet ```

To test with desired bandwidth settings 

```  sudo python config.py ```

<br />
Mininet will run and setup 2 hosts, laptop1 and laptop2 

To run Client from laptop1


```  mininet> laptop1 python client.py ```

To run Server from laptop2

```  mininet> laptop2 python server.py ```

&nbsp;
&nbsp;
&nbsp;

To get details about network interfaces of laptop1


```  mininet> laptop1 ifconfig```
<br />
<br />

To change connection settings , go to Line 27 of config.py and change 

For Example  
15 Mbps bandwidth and 2 ms delay on each link

```    linkopt = dict(bw=15, delay='2ms', loss=0)```


## Made by

* [Radhesh Sarma](https://github.com/Radhesh-Sarma)
* [Simran Sahni](https://github.com/Simran-Sahni)
* [Karthik Kotikalapudi](https://github.com/karthik0708)
* [Chatrik Singh Mangat](https://github.com/ChatrikMangat)
* [Ashi Sinha](https://github.com/ashiabcd)

