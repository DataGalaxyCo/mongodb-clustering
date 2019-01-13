import os
import sys
import time
from config import num_of_shard
from config import mongo_user
from config import mongo_pass


compose_yml = """
version: '3.3'
services:
{}
    cfg1:
        container_name: cfg1
        image: mongokey
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


def install():
    print "Make keyfile ... "
    cmd = "openssl rand -base64 512 > darvazeh"
    os.popen(cmd).read()
    cmd = "chmod 400 darvazeh"
    os.popen(cmd).read()
    print "Making `keyfile` has been finished."
    print "Making custom image from mongodb image."
    cmd = "docker build -t mongokey ."
    print "Making custom image \t\t\t done"
    os.popen(cmd).read()
    shards = ""
    mongos = ""
    init = 27018
    for i in range(num_of_shard):
        i += 1
        sample = """
    shard{}:
        container_name: shard{}
        image: mongokey
        command: mongod --keyFile darvazeh --shardsvr --replSet shard-replica --dbpath /data/db --port 27018
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
    print "Make docker Compose file... \t\t done"

    print "Running docker compose up"
    cmd = "docker-compose up -d"
    os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Please wait 20 sec..."
    time.sleep(20)
    print "Docker-compose up... \t\t\t done"

    print "Make configsrv replica set"
    # Make configsrv replica set
    cmd = r"""
    docker exec -it cfg1 bash -c "echo 'rs.initiate({_id: \"config-replica\",configsvr: true, members: [{ _id : 0, host : \"cfg1\" },{ _id : 1, host : \"cfg2\" }, { _id : 2, host : \"cfg3\" }]})' | mongo"
    """
    os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Please wait 20 sec..."
    time.sleep(20)
    print "Making cfg replica set... \t\t\t done"

    print "Start shard initializing"
    # Make configsrv replica set
    sample = r""
    priority = 100
    for i in range(num_of_shard):
        i += 1
        y = i - 1
        if i >= 8:
            sample += r"""{ _id : %s, host : \"shard%s:27018\", votes: 0 },""" % (y, i)
        else:
            priority -= 10
            sample += r"""{ _id : %s, host : \"shard%s:27018\" priority: %s},""" % (y, i, priority)
    cmd = r"""
    docker exec -it shard1 bash -c "echo 'rs.initiate({_id : \"shard-replica\", members: [%s]})' | mongo --port 27018"
    """ % (sample)

    inti_shard = os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Please wait 20 sec..."
    time.sleep(20)

    print "Shard initialize part2: It may takes serveral minutes... ."
    for i in range(num_of_shard):
        i += 1
        cmd = r"""
        docker exec -it router bash -c "echo 'sh.addShard(\"shard-replica/shard{}:27018\")' | mongo "
        """.format(i)
        os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Shard initializing... \t\t\t done"

    auth_text = set_auth % (mongo_user, mongo_pass, mongo_user, mongo_pass)
    f = open('auth.js', 'w')
    f.write(auth_text)
    f.close()
    cmd = "sudo cp auth.js mongo_cluster/data1/"
    os.popen(cmd).read()
    cmd = "docker exec -it shard1 bash -c 'mongo --port 27018 < /data/db/auth.js'"
    os.popen(cmd).read()
    cmd = "docker exec -it shard1 bash -c 'mongo --host router < /data/db/auth.js; rm /data/db/auth.js'"
    os.popen(cmd).read()
    os.popen('sudo rm -rf darvazeh').read()
    os.popen('sudo rm -rf auth.js').read()
    print "Final step has been finished."


def remove():
    cmd = "docker stop $(docker container ls -aq); docker rm $(docker container ls -aq); sudo rm -rf mongo_cluster/"
    os.popen(cmd).read()[:-1].replace('\n', ' ')
    print "Remove... \t\t\t done"


try:
    op = sys.argv[1]
    try:
        extra = sys.argv[2]
    except Exception:
        extra = 'all'
    if op == 'install':
        install()
    elif op == 'remove':
        remove()
    elif op == 'logs':
        cmd = "docker-compose logs --tail={} -t -f".format(extra)
        os.system(cmd)
    elif op == 'run':
        cmd = "docker-compose up -d"
        os.popen(cmd).read()[:-1].replace('\n', ' ')
    elif op == 'stop':
        cmd = "docker-compose stop"
        os.popen(cmd).read()[:-1].replace('\n', ' ')
    else:
        print "Please pass `install` or `remove` arg"
except Exception as e:
    print "You should pass just one argument", e
