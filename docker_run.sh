xhost +local:

# DBUS_SOCKET_PATH=$(echo "$DBUS_SESSION_BUS_ADDRESS" | sed 's/unix:path=//' | sed 's/,.*//')

# docker run -it \
#     --rm \
#     --ipc=host \
#     -e DISPLAY=$DISPLAY \
#     -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
#     -v "$DBUS_SOCKET_PATH":"$DBUS_SOCKET_PATH":ro \
#     --device=/dev/dri:/dev/dri \
#     -v ./creds.json:/home/marketface/creds.json \
#     --user $(id -u):$(id -g) \
#     --entrypoint /bin/bash \
#     -t marketface

docker run -it \
    -e DISPLAY=$DISPLAY \
    -p 8090:8090 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
    -v /run/dbus:/run/dbus:ro \
    -v ./marketface:/home/marketface/marketface:rw \
    -v ./data:/home/marketface/data:rw \
    -v ./creds.json:/home/marketface/creds.json:ro \
    -v ./browser_context.json:/home/marketface/browser_context.json:rw \
    --device=/dev/dri \
    --entrypoint /bin/bash \
    marketface