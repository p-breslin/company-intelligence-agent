import weaviate

"""
Weaviate docker set up:

docker run -d --name weaviate \ 
    -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \ 
    -e PERSISTENCE_DATA_PATH="/var/lib/weaviate" \ 
    -e QUERY_DEFAULTS_LIMIT=25 \ 
    -p 8080:8080 \ 
    -p 50051:50051 \ 
    semitechnologies/weaviate:latest

"""
client = weaviate.connect_to_local(port=8080)
print(client.is_ready())
client.close()
