#! /bin/bash
cd ~/
git clone https://github.com/aguinet/usbtop.git
cd usbtop
sudo apt update 
sudo apt install libboost-dev libpcap-dev libboost-thread-dev libboost-system-dev cmake
mkdir _build && cd _build
cmake -DCMAKE_BUILD_TYPE=Release .. 
make 
sudo make install 