from bluesky.callbacks.zmq import Publisher

Publisher(glbl['inbound_proxy_address'], RE=xrun)
