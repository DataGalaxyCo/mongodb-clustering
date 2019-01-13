# Mongodb-Clustering
Install mongodb clustering by docker and docker-compose.

* Before everything install docker and docker-compose:
Please login docker:
```
docker login
```
Then pull this image:
```
docker pull mongo
```

You can change some of general options such as number of shard member and authentication(username & password) in the`config.py` file:
```
# number of shards
num_of_shard = 3

# Mongodb credential
mongo_user = 'admin'
mongo_pass = 'pass'
```

#### Enable sharding on database and setting shard keys:
Please fill shard_keys variable in the `config.py` file such as below:
```
shard_keys_map = {
    'database': [('coll1', 'key'), ('coll2', 'key')]
}
```

#### Installation and Running
```
python make_docker_compose.py install
```

#### Help
```
python make_docker_compose.py help
```
