from bluesky.callbacks.zmq import Publisher

raw_publisher = Publisher(glbl['inbound_proxy_address'], RE=xrun, prefix=b'raw')
raw_publisher = Publisher(glbl['inbound_proxy_address'], RE=RE, prefix=b'raw')
