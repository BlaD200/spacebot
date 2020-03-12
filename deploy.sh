docker build -t spacebot .
docker tag spacebot eu.gcr.io/vibrant-vector-260112/spacebot
gcloud auth print-access-token | sudo  docker login -u oauth2accesstoken --password-stdin https://eu.gcr.io
docker push eu.gcr.io/vibrant-vector-260112/spacebot