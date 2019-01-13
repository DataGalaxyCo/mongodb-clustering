# number of shards
num_of_shard = 3

# Mongodb credential
# Note: Please change user and password from default values
mongo_user = 'admin'
mongo_pass = '1234'


compose_yml = """
version: '3.3'
services:
{}
    cfg1:
        container_name: cfg1
        image: mongokey
        restart: always
        command: mongod --keyFile darvazeh --configsvr --replSet config-replica --dbpath /data/db --port 27017
        environment:
            TERM: xterm
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/config1:/data/db
    cfg2:
        container_name: cfg2
        image: mongokey
        restart: always
        command: mongod --keyFile darvazeh --configsvr --replSet config-replica --dbpath /data/db --port 27017
        environment:
            TERM: xterm
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/config2:/data/db
    cfg3:
        container_name: cfg3
        image: mongokey
        restart: always
        command: mongod --keyFile darvazeh --configsvr --replSet config-replica --dbpath /data/db --port 27017
        environment:
            TERM: xterm
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/config3:/data/db
    router:
        container_name: router
        image: mongokey
        restart: always
        depends_on:
            - cfg1
            - cfg2
            - cfg3
{}
        command: mongos --keyFile darvazeh --configdb config-replica/cfg1:27017,cfg2:27017,cfg3:27017 --port 27017 --bind_ip_all
        ports:
            - 27017:27017
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/router:/data/db

"""


set_auth = """
use admin
db.createUser(
  {
    user: "%s",
    pwd: "%s",
    roles: [ { role: "root", db: "admin" } ]
  }
);
db.auth('%s', '%s')
"""


help_msg = """
Please pass these options:

1- install \t\t\t For install and making and running sharded cluster.
2- remove \t\t\t For removeing everything.
3- run \t\t\t\t For running sharded cluster
4- stop \t\t\t For stopping shard service
5- logs \t\t\t For showing logs of all shards and cfg and members
"""


shard_keys_map = {
    'DATABASE': [('COLLECTION_1', '_id'), ('COLLECTION_2', '_id')]
}
