#include <cerrno>
#include <math.h>
#include <ostream>
#include <sstream>
#include <algorithm>
#include <vector>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <iostream>
#include <string>
#include <cstring>
#include <sys/wait.h>
#include <sys/mman.h>

using namespace std;

// Struktura do przetrzymywania informacji o otrzymanych macierzach
struct matrix_information{
    vector<string> matrix1;
    vector<string> matrix2;
    int size;
    int fields;
};

//funkcja obsługująca błędy
void problem(string message){
    const char * err = message.c_str(); 
    if (errno != 0) perror(err);
    else cout << message << endl;
    exit(-1);
}   

//funkcja tworząca pamięć współdzieloną przez procesy
int* create_shared_memory(size_t size) {
  int protection = PROT_READ | PROT_WRITE;
  int visibility = MAP_SHARED | MAP_ANONYMOUS;
  return (int*) mmap(NULL, size, protection, visibility, -1, 0);
}

//funkcja zamieniająca vector liczb na ciąg znaków
string vector_to_string(int size, vector<int> vec){
    stringstream ss;

    for (int i = 0; i < size; i++){
        ss << vec[i];
        ss << ' ';
    } 
    return ss.str();
}

//funkcja zamieniająca macierz liczb na ciąg znaków
vector<string> matrix_to_string(int size, vector<vector<int>> matrix){
    vector<string> result;
    for (int i = 0; i < size; i++){
        string part = vector_to_string(size, matrix[i]);
        result.push_back(part);
    }
    return result;
}

//funkcja zamieniająca macierz liczb na ciąg znaków
string array_to_string(int size, int* array){
    stringstream ss;
    string str;
    for (int i = 0; i < size; i++){
        ss << array[i];
        ss << ' ';
    } 
    str = ss.str();

    return str;
}

//funkcja zabijająca proces zombie
void zombie_killer(int signo){
    wait(NULL);
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

//funkcja zapisująca z podanych argumentów adresy serwerów podrzędnych
vector<sockaddr_in> get_sub_servers_addresses(int num_servers, char *adresses[]){
    vector<sockaddr_in> servers;

    for (int i = 0; i < num_servers; i++){
        struct hostent* h=gethostbyname(adresses[i*2 + 2]);
        inet_ntoa(*((struct in_addr *)h->h_addr_list[0]));
        struct sockaddr_in addr;
        int port = atoi(adresses[i*2 + 3]);

        addr.sin_family=PF_INET;
        addr.sin_port=htons(port);
        addr.sin_addr.s_addr=inet_addr(adresses[i*2 + 2]);
        servers.push_back(addr);
    } 
    return servers;
}

//funkcja odbierająca od klienta macierze
matrix_information receive_from_client(int cfd){
    matrix_information matrixes;
    string received;
    received.resize(100);

    int len_received = 0,  sum_received = 0;
    while ((len_received = read(cfd, (char*)(received.data() + sum_received), 100)) > 0){
        sum_received += len_received;
        if ((received[sum_received - 1] == ' ' and received[sum_received - 2] == ' ') 
        or received[sum_received - 1] == '\0' or received[sum_received - 2] == '\0') break;
        received.resize(100 + sum_received);
    }
    if (len_received < 0) problem("Błąd funkcji read (od klienta)! ");
    
    stringstream received_s(received);
    received_s >> matrixes.size; //pierwszy przesłany element jest wielkością macierzy
    matrixes.fields = pow(matrixes.size, 2);

    vector<vector<int>> m1(matrixes.size, vector<int>(matrixes.size));
    vector<vector<int>> m2(matrixes.size, vector<int>(matrixes.size));
    //zapisanie macierzy w wektorach 
    for (int i = 0; i < matrixes.size; i++){
        for (int j = 0; j < matrixes.size; j++){
            received_s >> m1[i][j];
        }
    }
    //druga macierz ma zamienione wiersze z kolumnami by łatwiej było wysyłać dane do obliczeń
    for (int i = 0; i < matrixes.size; i++){
        for (int j = 0; j < matrixes.size; j++){
            received_s >> m2[j][i];
        }
    }
    //zamiana macierzy na tablice ciagów znaków
    matrixes.matrix1 = matrix_to_string(matrixes.size, m1);
    matrixes.matrix2 = matrix_to_string(matrixes.size, m2);
    return matrixes;
}

//funkcja wysyłająca wynik do klienta
void send_to_client(int fd, string to_send_str){
    int message_len = 100;
    int empty = 100 - to_send_str.size()%100;
    int offset = to_send_str.size() - 1;
    to_send_str.resize((to_send_str.size()/ 100 + 1) * 100 );
    for (int i = 0; i < empty; i++){
        to_send_str[offset + i] = ' ';
    }
    const char* to_send = to_send_str.c_str();
    uint sum_sent = 0, len_sent = 0;
    while (sum_sent < to_send_str.size()){   
        len_sent = write(fd, to_send + sum_sent, message_len);
        if (len_sent < 0){
            problem("Błąd wysyłania do klienta (write)!");
        }else{
            sum_sent += len_sent;
        }
    }
}

//funkcja wysyłająca wiersz i kolumnę do serwera podrzędnego oraz odbierająca wynik
int count_on_server(matrix_information matrixes, int fd, int field){
    string to_send_str = matrixes.matrix1[field/matrixes.size] + matrixes.matrix2[field%matrixes.size] + '\0';
    char buf[100];
    to_send_str.resize((to_send_str.size()/100 + 1) * 100);
    const char* to_send = to_send_str.c_str();

    int message_len = 100;
    uint sum_sent = 0, len_sent = 0;
    while (sum_sent < to_send_str.size()){   
        len_sent = write(fd, to_send + sum_sent, message_len);
        if (len_sent < 0){
            problem("Błąd wysyłania do serwera (write)!");
        }else{
            sum_sent += len_sent;
        }
    }

    int sum_received = 0, len_received;
    while(sum_received < 100){
        len_received = read(fd, buf + sum_received, 100);
        if (len_received < 0){
            problem("Błąd odbierania z serwera (read)! ");
        }
        sum_received += len_received;
    }
    
    return atoi(buf);
}

int main(int argc, char *argv[]) {
    if (argc < 4 or argc % 2 == 1){
        problem("Podano złą liczbę argumentów!\n./Plik [port serwera] [adres] [port] [adres] [port] ...\n");
    }
    int cfd, sfd, pid, s, num_servers;
    signal(SIGCHLD, zombie_killer);    
    sfd = create_socket();
    sockaddr_in saddr = create_server_address(atoi(argv[1]));
    struct sockaddr_in caddr;
    s = sizeof(caddr);

    num_servers = (argc - 2) / 2;
    vector<sockaddr_in> servers = get_sub_servers_addresses(num_servers, argv);

    if (bind(sfd, (struct sockaddr*)&saddr, sizeof(saddr)) < 0){
        problem("Błąd funkcji bind! ");
    }

    if (listen(sfd, 15) < 0){
        problem("Błąd funkcji listen! ");
    }

    while(1) {
        cfd = accept(sfd, (struct sockaddr*)&caddr, (socklen_t*)&s);
        if (cfd < 0) problem("Błąd funkcji accept! ");
        cout << "Nowe połączenie! " << inet_ntoa((struct in_addr)caddr.sin_addr) << endl;

        pid = fork();
        if (pid < 0) {
            problem("Błąd tworzenia procesu potomnego (fork)! ");
        }
        else if (pid == 0){ 
            close(sfd);
            matrix_information received = receive_from_client(cfd);

            int* result = create_shared_memory(sizeof(int)* received.fields);
   
            int parts = received.fields / num_servers;
            for (int i = 0; i < num_servers; i++){
                pid = fork();
                if (pid == 0){
                    close(cfd);
                    int sub_sfd = create_socket();

                    if (connect(sub_sfd,(struct sockaddr*)&servers[i], sizeof(servers[i])) < 0) problem("Błąd funkcji connect");
                    int end_field = (i + 1) * parts;
                    if (i == num_servers - 1) end_field = received.fields;

                    for (int j = i * parts; j < end_field; j++){
                        result[j] = count_on_server(received, sub_sfd, j);
                    }
                    if (write(sub_sfd, "n", 2) < 0){
                        problem("Błąd wysyłania do serwera (write)! ");
                    }
                    exit(0);
                }
            }

            int status;
            do {
                status = wait(NULL);
                if(status == -1 && errno != ECHILD) {
                    problem("Błąd funkcji wait! ");
                }
            } while (status > 0);

            string to_send = array_to_string(received.fields, result);

            send_to_client(cfd, to_send);

            close(cfd);
            exit(0);
        }
        else close(cfd);
    } 
    close(sfd);
    exit(0);
}
