# Introdução ao SPIRE

Roteiro construido para auxiliar na compreensão do funcionamento do SPIRE.

## Pré-requisitos

* Certifique-se que tem o Go instalado:

```bash
   wget https://go.dev/dl/go1.22.2.linux-amd64.tar.gz
   sudo rm -rf /usr/local/go && tar -C /usr/local -xzf go1.22.2.linux-amd64.tar.gz
   echo "export PATH=$PATH:/usr/local/go/bin" >> $HOME/.profile
```
```bash
  go version 
```

**A instalação descrita para o Go foi para Linux, caso seu sistema operação for outro visite: https://go.dev/doc/install**

* Clonar o repositório:
  
```bash
   git clone https://github.com/GabrielCLL/introduction2spire.git
```

* Entrar no diretório do projeto e clonar o spire:

```bash
   git clone https://github.com/spiffe/spire.git
```

# Demonstração

Para tornar o processo de demonstração mais didático, se decidiu montar dois cenários que consigam representar os conceitos sobre identidade e de confiança.

## Aplicação em teste:

### Aplicação 1:

A aplicação é um simples servidor Flask, disponível no diretório: [servidor](./app/servidor.py), cuja função é exibir uma frase: "Hello World" caso for acessado.

Entretanto ele foi realizado com o contexto SSL (_Secure Sockets Layer_), habilitando que ela use o HTTPS no lugar de HTTP. Para tanto, deve-se criar um certificado e uma chave e configurá-las no Flask.

Esse cenário refere-se a servir uma identidade a um carga de trabalho.

#### Criando o Root CA:

O SPIRE já vem um dummy como uma CA, e funcionaria perfeitamente neste nosso caso, porém, é interessante saber como se pode trocar o root que o SPIRE.

```bash
  sudo openssl req \
       -subj "/C=BR/ST=PB/L=CG/O=SD Ltd/CN=sd root ca" \
       -newkey rsa:2048 -nodes -keyout ./spire/conf/root.key \
       -x509 -days 30 -out ./spire/conf/root.crt
```


* Adicionando o root CA criado na cadeia de confiança da máquina:

```bash
  sudo sudo cp ./spire/conf/root.crt /usr/local/share/ca-certificates
  sudo update-ca-certificates
```

**Lembre-se de alterar as permissões do arquivo root.key, ele precisará ser lido quando for inicializado o servidor"

```bash
  sudo chmod 644 ./spire/conf/root.key
```

#### Modificar os arquivos de configuração para receber este certificado:

Como mudamos a ca utilizada, devemos sinalizá-la nos arquivos de configuração.

* [Servidor](./spire/conf/server/server.conf):

    ```bash
        UpstreamAuthority "disk" {
                plugin_data {
                    key_file_path = "./conf/root.key"
                    cert_file_path = "./conf/root.crt"
                }
            }
    ```

* [Agente](./spire/conf/agent/agent.conf):

    ```bash
        trust_bundle_path = "./conf/root.crt"
    ```

#### Inicializando o SPIRE

##### Gere todos os binários do SPIRE:

O primeiro passo é gerar os binários, eles que vão fazer a mágica acontecer.

|Obs: para ele o spire poder utilizar os recursos da máquina precisaremos ter um api.socket do Unix.

```bash
    cd spire && make build 
```

##### Inciando o Servidor SPIRE:

```bash
   ./bin/spire-server run -config conf/server/server.conf &
```

```bash
   ./bin/spire-server healthcheck
```
* Criar o token de atestação para o Agente SPIRE:
  
```bash
   ./bin/spire-server token generate -spiffeID spiffe://example.org/myagent
```

##### Iniciando o Agente SPIRE:
  
```bash
   ./bin/spire-agent run -config conf/agent/agent.conf -joinToken <token_string> &
```

```bash
   ./bin/spire-agent healthcheck
```

##### Registrando a carga de trabalho:
  
 Deve-se criar o registro de entrada para uma carga de trabalho. Esse processo é atribuir ao agente, que esteja rodando no mesmo nó que carga, a responsabilidade de atestar essa carga.

 A atestação e garantia que cada carga irá receber o SVID correto, parte do uso dos seletores. 
 
 | Para mais detalhes visite: [Registering worloads](https://spiffe.io/docs/latest/deploying/registering/)

```bash
   ./bin/spire-server entry create -parentID spiffe://example.org/myagent \
    -spiffeID spiffe://example.org/myservice -dns teste.servidor -selector unix:uid:$(id -u)
```

```bash
Entry ID         : 73f1b674-59da-46a8-b70f-59dfc361910c
SPIFFE ID        : spiffe://example.org/myservice
Parent ID        : spiffe://example.org/myagent
Revision         : 0
X509-SVID TTL    : default
JWT-SVID TTL     : default
Selector         : unix:uid:1000
```
#### Resgatando o SVID:

Como não utilizaramos um spire-helper, o processo de gerar as identidades irá ocorrer por meio do comando abaixo.
Esse comando ele chama a API da carga de trabalho solicitando o certificado x509 para a carga de trabalho.

```bash
    bin/spire-agent api fetch x509 -write /tmp/
```

```bash
Received 1 svid after 2.623105ms

SPIFFE ID:              spiffe://example.org/myservice
SVID Valid After:       2024-05-01 22:36:03 +0000 UTC
SVID Valid Until:       2024-05-01 23:36:13 +0000 UTC
Intermediate #1 Valid After:    2024-05-01 22:33:16 +0000 UTC
Intermediate #1 Valid Until:    2024-05-02 22:33:26 +0000 UTC
CA #1 Valid After:      2024-05-01 22:30:00 +0000 UTC
CA #1 Valid Until:      2024-05-31 22:30:00 +0000 UTC

Writing SVID #0 to file /tmp/svid.0.pem.
Writing key #0 to file /tmp/svid.0.key.
Writing bundle #0 to file /tmp/bundle.0.pem.
```

* Caso queira conferir o formato e conteúdo do certificado basta executar:

```bash
    openssl x509 -in /tmp/svid.0.pem -text -noout
```
##### Executando o servidor

De posse da SVID, está na hora de executarmos o servidor.
```bash
    python3 ../app/servidor.py
```

##### Realizando uma chamada para o servidor:

```bash
    curl --cacert ./conf/root.crt https://teste.servidor:5000/
```

```bash
   openssl s_client -connect 127.0.0.1:5000 > ../teste.crt
```

|Obs: Tem que realizar o mapeamento da porta para o dns atribuido na criação do registro de entrada!

```bash
   sudo nano /etc/hosts 
```

```bash
    # This file was automatically generated by WSL. To stop automatic generation of this file, add the following entry to /># [network]
    # generateHosts = false
    127.0.0.1       localhost
    127.0.1.1       Legacy. Legacy
    127.0.0.1       teste.servidor

    # The following lines are desirable for IPv6 capable hosts
    ::1     ip6-localhost ip6-loopback
    fe00::0 ip6-localnet
    ff00::0 ip6-mcastprefix
    ff02::1 ip6-allnodes
    ff02::2 ip6-allrouters
```

### Aplicação 2:

A aplicação 2 trata-se de firmar um tls entre um cliente e um servidor.

Ela se encontra aqui: https://github.com/spiffe/go-spiffe/tree/main/v2/examples/spiffe-tls

O detalhe dessa demonstração é a inclusão das bibliotecas, o que facilita o manejo do SPIFFE, como por exemplo, na solicitações dos SVIDs.

# Removendo os processos:

* Descobrindo o PID do Agente SPIRE

    ```bash
        kill -9 $(ps aux | grep '[s]pire-agent ' | awk '{print $2}')
    ```
   

* Descobrindo o PID do Servidor SPIRE

    ```bash
        kill -9 $(ps aux | grep '[s]pire-server ' | awk '{print $2}')
    ```
    