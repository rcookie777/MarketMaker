# ftx-quant-msu

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Installation
Probably not the best name for an the environment but we can change this later.

### Using Conda
```
$ conda env create -n ftx python=3.7
$ conda activate ftx
$ conda install matplotlib scipy pandas seaborn
$ pip install python-binance==1.0.15 notebook ccxt tqdm websockets==9.1 pyyaml
```

### Using Virtual environment (Less storage required)
We can use a virtual environment as well, which may use less space than conda but does not do much in the way of resolving dependency conflicts.
```
$ pip install virtualenv
$ python3 -m pip install --upgrade pip
$ cd ~/
$ mkdir venv
```

I had to run the following for whatever reason, my system python is 3.8 it seems. You may not need to, but if the next command fails at building the ftx virtualenv, then run this.

```
$ sudo apt install python3.8-venv
```
Create the environment.
```
$ python3 -m venv venv/ftx
```
For maximum space saving, you can try the following. It's possible it won't work as well since it's relying on the systems already installed packages, but might be worth a try.

```
$ python3 -m venv --system-site-packages venv/ftx
```

Activate the environment

```
$ source venv/ftx/bin/activate
```
If you run `$ which pip3` now, you will see that pip is coming from the environment, not the system python version, which is good.

Now install the packages.
```
$ pip install numpy \
matplotlib \
scipy \
pandas \
seaborn \
python-binance==1.0.15 \
notebook \
ccxt \
tqdm \
websockets==9.1 \
pyyaml \
gevent==21.12.0 \
websockets==9.1 \
websocket-client==1.4.1
```




## Usage
Running in interactive mode will allow you te see the messages printed out from the _on_message method in MarketMaker()

`$ python -i -m strategies.market_maker`

Not ideal way to use it going forward, but works to demonstrate. Since it spawns a thread, you'll need to kill the process from another terminal.

```
$ ps -aux | grep market_maker
$ kill pid_of_market_maker_process
```
