# Matrix-multiplication-server
## Description
Server application that receives 2 matrixes from client, divide them into parts and sends to sub-servers. <br> 
Each sub-server multiplies one column/row and sends result back to the main server. <br>
Main server sends results back to client.
## Instruction for servers
./server_sub [number of port]
<br><br>
./server_main [number of port] [sub-server address] [sub-server port] *for each server*
