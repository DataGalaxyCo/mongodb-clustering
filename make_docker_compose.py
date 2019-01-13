import os
import sys
import time
from config import set_auth
from config import help_msg
from config import mongo_user
from config import mongo_pass
from config import compose_yml
from config import num_of_shard
from config import shard_keys_map
from config import sample_shard_key
from config import sample_db_enable


def install():

    cmd = "openssl rand -base64 512 > darvazeh"
    os.popen(cmd)
    cmd = "chmod 400 darvazeh"
    os.popen(cmd)
    print "Making `keyfile` has been finished... done"

    cmd = "docker build -t mongokey ."
    print "Making custom mongodb image has been finished... done"
    os.popen(cmd)

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
    print "Make docker Compose file... done"

    cmd = "docker-compose up -d"
    os.popen(cmd)
    print "Please wait 20 sec..."
    time.sleep(20)
    print "Docker-compose up... done"

    # Make configsrv replica set
    cmd = r"""
    docker exec -it cfg1 bash -c "echo 'rs.initiate({_id: \"config-replica\",configsvr: true, members: [{ _id : 0, host : \"cfg1\" },{ _id : 1, host : \"cfg2\" }, { _id : 2, host : \"cfg3\" }]})' | mongo"
    """
    os.popen(cmd)
    print "Please wait 20 sec..."
    time.sleep(20)
    print "Making cfg replica set has been finished... done"

    sample = r""
    priority = 100
    for i in range(num_of_shard):
        i += 1
        y = i - 1
        if i >= 8:
            sample += r"""{ _id : %s, host : \"shard%s:27018\", votes: 0 },""" % (y, i)
        else:
            priority -= 10
            sample += r"""{ _id : %s, host : \"shard%s:27018\" ,priority: %d},""" % (y, i, priority)
    cmd = r"""
    docker exec -it shard1 bash -c "echo 'rs.initiate({_id : \"shard-replica\", members: [%s]})' | mongo --port 27018"
    """ % (sample)

    inti_shard = os.popen(cmd)
    print "Please wait 20 sec..."
    time.sleep(20)

    for i in range(num_of_shard):
        i += 1
        cmd = r"""
        docker exec -it router bash -c "echo 'sh.addShard(\"shard-replica/shard{}:27018\")' | mongo "
        """.format(i)
        os.popen(cmd)
    print "Shard initializing has been finished... done"

    extra()
    authentication()

    print "Final step has been finished."



def authentication():
    auth_text = set_auth % (mongo_user, mongo_pass, mongo_user, mongo_pass)
    f = open('auth.js', 'w')
    f.write(auth_text)
    f.close()
    cmd = "sudo cp auth.js mongo_cluster/data1/"
    os.popen(cmd)
    cmd = "sudo cp auth.js mongo_cluster/router/"
    os.popen(cmd)
    cmd = "docker exec -it shard1 bash -c 'mongo --port 27018 < /data/db/auth.js;rm /data/db/auth.js'"
    os.popen(cmd)
    cmd = "docker exec -it router bash -c 'mongo router < /data/db/auth.js; rm /data/db/auth.js'"
    os.popen(cmd)
    os.popen('sudo rm -rf darvazeh')
    os.popen('sudo rm -rf auth.js')


def remove():
    cmd = "docker stop $(docker container ls -aq); docker rm $(docker container ls -aq); sudo rm -rf mongo_cluster/"
    os.popen(cmd)
    print "Remove... done"


def extra():
    cmd_shard_keys = "use admin\n"
    for db, _map in shard_keys_map:
        cmd_shard_keys += sample_db_enable % (db) + '\n'
        for coll, _key in _map:
            cmd_shard_keys += sample_shard_key % (db, coll, _key) + '\n'

    f = open('extra.js', 'w')
    f.write(cmd_shard_keys)
    f.close()
    cmd = "sudo cp extra.js mongo_cluster/router/"
    os.popen(cmd)
    cmd = "docker exec -it router bash -c 'mongo < /data/db/extra.js; rm /data/db/extra.js'"
    os.popen(cmd)
    os.popen('sudo rm -rf extra.js')
    print "Finish adding shard_keys processes... done"


try:
    op = sys.argv[1]
    try:
        extra = sys.argv[2]
    except Exception:
        extra = 'all'
    if op == 'install':
        print 'Start installing...'
        install()
    elif op == 'remove':
        print 'Start removing...'
        remove()
    elif op == 'logs':
        cmd = "docker-compose logs --tail={} -t -f".format(extra)
        os.system(cmd)
    elif op == 'run':
        print 'Start running...'
        cmd = "docker-compose up -d"
        os.popen(cmd)
    elif op == 'stop':
        cmd = "docker-compose stop"
        os.popen(cmd)
    elif (op == 'help') or (op == '--help'):
        print help_msg
    else:
        print help_msg
except Exception as e:
    if sys.argv == ['make_docker_compose.py']:
        print help_msg
    else:
        print "Error: ", e
