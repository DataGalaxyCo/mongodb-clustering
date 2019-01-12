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

#### Installation and running
```
python make_docker_compose.py install
python make_docker_compose.py run
```

