import os
import sys
import time


compose_yml = """
version: '3.3'
services:
{}
    mongocfg1:
        container_name: mongocfg1
        image: mongo
        command: mongod --configsvr --replSet mongorsconf --dbpath /data/db --port 27017
        environment:
            TERM: xterm
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/config1:/data/db
    mongocfg2:
        container_name: mongocfg2
        image: mongo
        command: mongod --configsvr --replSet mongorsconf --dbpath /data/db --port 27017
        environment:
            TERM: xterm
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/config2:/data/db
    mongocfg3:
        container_name: mongocfg3
        image: mongo
        command: mongod --configsvr --replSet mongorsconf --dbpath /data/db --port 27017
        environment:
            TERM: xterm
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/config3:/data/db
    mongos1:
        container_name: mongos1
        image: mongo
        depends_on:
            - mongocfg1
            - mongocfg2
            - mongocfg3
{}
        command: mongos --configdb mongorsconf/mongocfg1:27017,mongocfg2:27017,mongocfg3:27017 --port 27017 --bind_ip_all
        ports:
            - 27017:27017
        expose:
            - '27017'
        volumes:
            - /etc/localtime:/etc/localtime:ro

"""


def install():
    num_of_shard = 13
    shards = ""
    mongos = ""
    init = 27018
    for i in range(num_of_shard):
        i += 1
        sample = """
    shard{}:
        container_name: shard{}
        image: mongo
        command: mongod --shardsvr --replSet shard-replica --dbpath /data/db --port 27018
        ports:
            - {}:27018
        expose:
            - '27018'
        environment:
            TERM: xterm
        volumes:
            - /etc/localtime:/etc/localtime:ro
            - ./mongo_cluster/data{}:/data/db
        """
        shards += sample.format(i, i, init, i) + '\n'
        init += 1
        mongos += '            - shard{}\n'.format(i)

    # Make docker Compose file
    f = open('docker-compose.yml', 'w')
    f.write(compose_yml.format(shards, mongos))
    f.close()
    print "Make docker Compose file... \t\t\t done"


    print "Running docker compose up"
    cmd = "docker-compose up -d"
    upd = os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Please wait 20 sec..."
    time.sleep(20)
    print "Docker-compose up... \t\t\t done"

    print "Make configsrv replica set"
    # Make configsrv replica set
    cmd = r"""
    docker exec -it mongocfg1 bash -c "echo 'rs.initiate({_id: \"mongorsconf\",configsvr: true, members: [{ _id : 0, host : \"mongocfg1\" },{ _id : 1, host : \"mongocfg2\" }, { _id : 2, host : \"mongocfg3\" }]})' | mongo"
    """
    cfg = os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Please wait 20 sec..."
    time.sleep(20)
    print "Making cfg replica set... \t\t\t done"

    print "Init shard"
    # Make configsrv replica set
    sample = r""
    for i in range(num_of_shard):
        i += 1
        y = i - 1
        if i >= 8:
            sample += r"""{ _id : %s, host : \"shard%s:27018\", priority: 0, votes: 0 },""" % (y, i)
        else:
            sample += r"""{ _id : %s, host : \"shard%s:27018\" },""" % (y, i)
    cmd = r"""
    docker exec -it shard1 bash -c "echo 'rs.initiate({_id : \"shard-replica\", members: [%s]})' | mongo --port 27018"
    """ % (sample)

    inti_shard = os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Please wait 20 sec..."
    time.sleep(20)

    print "init shard... \t\t\t done"
    print "Final step: It may takes serveral minutes... ."
    for i in range(num_of_shard):
        i += 1
        cmd = r"""
        docker exec -it mongos1 bash -c "echo 'sh.addShard(\"shard-replica/shard{}:27018\")' | mongo "
        """.format(i)
        cmd = os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Final step has been finished."


def remove():
    cmd = "docker stop $(docker container ls -aq); docker rm $(docker container ls -aq); sudo rm -rf mongo_cluster/"
    cmd = os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Remove... \t\t\t done"


try:
    op = sys.argv[1]
    try:
        extra = sys.argv[2]
    except:
        extra = 'all'
    if op == 'install':
        install()
    elif op == 'remove':
        remove()
    elif op == 'logs':
        cmd = "docker-compose logs --tail={} -t -f".format(extra)
        os.system(cmd)
    else:
        print "Please pass `install` or `remove` arg"
except Exception as e:
    print "You should pass just one argument", e
