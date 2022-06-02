#include <cerrno>
#include <sstream>
#include <vector>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <iostream>
#include <string>
#include <string.h>
#include <sys/wait.h>

using namespace std;

//funkcja obsługująca błędy
void problem(string message){
    const char * err = message.c_str(); 
    if (errno != 0) perror(err);
    else cout << message << endl;
    exit(1);
}   

//funckja zapisująca adres serwera do struktury
sockaddr_in create_server_address(int port){
    struct sockaddr_in saddr;
    saddr.sin_family = PF_INET;
    saddr.sin_port = htons(port);
    saddr.sin_addr.s_addr = INADDR_ANY;
    return saddr;
}

//funkcja zwracająca deskryptor stworzonego socketu 
int create_socket(){
    int sfd = socket(PF_INET, SOCK_STREAM, 0);
    int on = 1;
    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, (char*)&on, sizeof(on));
    return sfd;
}

//funkcja zabijająca proces zombie
void zombie_killer(int signo){
    wait(NULL);
}

//funkcja odbierająca od wektory do obliczeń
string receive_from_client(int cfd){
    string received;
    received.clear();
    received.resize(100);

    int len_received = 0,  sum_received = 0;
    while ((len_received = read(cfd, (char*)(received.data() + sum_received), 100)) > 0){
        sum_received += len_received;
        if ((received[sum_received - 1] == ' ' and received[sum_received - 2] == ' ') 
        or received[sum_received - 1] == '\0' or received[sum_received - 2] == '\0') break;
        received.resize(100 + sum_received);
    }   
    if (len_received < 0) problem("Błąd funkcji read (od klienta)! ");
    return received;
}

//funkcja mnożąca wektory i zwracająca wynik w postaci
string calculate(string received){
    string result_str;
    stringstream received_s(received);
    vector<int> received_int;

    while (received_s){
        int number;
        received_s >> number;
        received_int.push_back(number);
    }

    int len = received_int.size() / 2;
    int result = 0;

    for (int i = 0; i < len; i++){
        result += received_int[i] * received_int[i+len];
    }

    result_str = to_string(result);
    return result_str;
}

//Odsyłanie wyniku do głównego serwera
void send_to_client(int fd, string result){
    result.resize(100);
    int message_len = 100;
    uint sum_sent = 0, len_sent = 0;
    while (sum_sent < 100){   
        len_sent = write(fd, result.c_str() + sum_sent, message_len);
        if (len_sent < 0){
            problem("Błąd wysyłania do klienta (write)!");
        }else{
            sum_sent += len_sent;
        }
    }
}

int main(int argc, char *argv[]) {
    if(argc != 2){
        problem("Zła ilość argumentów\n./Plik [port]");
    }
    int s, sfd, cfd, pid;
    signal(SIGCHLD, zombie_killer);

    sfd = create_socket();
    sockaddr_in saddr = create_server_address(atoi(argv[1]));
    struct sockaddr_in caddr;
    s = sizeof(caddr);

    if (bind(sfd, (struct sockaddr*)&saddr, sizeof(saddr)) < 0){
        problem("Błąd funkcji bind!");
    }

    if (listen(sfd, 15) < 0){
        problem("Błąd funkcji listen!");
    }

    while(1) {
        cfd = accept(sfd, (struct sockaddr*)&caddr, (socklen_t*)&s);
        if (cfd < 0) problem("Błąd funkcji accept! ");

        cout << "Nowe połączenie: " << inet_ntoa((struct in_addr)caddr.sin_addr) << endl;
        pid = fork();
        if (pid == 0){ 
            close(sfd);
            string received, result;

            while(1){
                received = receive_from_client(cfd);
                if (received[0] == 'n') break;
                result = calculate(received);
                send_to_client(cfd, result);
            }
            close(cfd);
            exit(0);
        }
        close(cfd);
    }
    close(sfd);
    exit(0);
}