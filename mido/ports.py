"""
Useful tools for working with ports

Module content:

    multi_receive -- receive messages from multiple ports
    multi_iter_pending -- iterate through messages from multiple ports
    IOPort -- combined input / output port. Wraps around to normal ports
    MessageBuffer -- pseudo-port that stores messages in a deque
"""

import time
import random
from collections import deque


def multi_receive(ports):
    """Receive messages from multiple ports.

    Generates (message, port) tuples from every port in ports. The
    ports are polled in random order for fairness, and all messages
    from each port are yielded before moving on to the next port.
    """
    ports = list(ports)
    while 1:
        random.shuffle(ports)
        
        for port in ports:
            for _ in range(port.pending()):
                yield (port.receive(), port)

        time.sleep(0.001)


def multi_iter_pending(ports):
    """Iterate through all pending messages in ports.

    ports is an iterable of message ports to check.

    Yields (message, port) tuples until there are no more pending
    messages. This can be used to receive messages from
    a set of ports in a non-blocking manner.
    """
    ports = list(ports)
    random.shuffle(ports)
    for port in ports:
        for _ in range(port.pending()):
            yield (port.receive(), port)


class IOPort(object):
    """Input / output port.

    This is a convenient wrapper around an input port and an output
    port which provides the functionality of both. Every method call
    is forwarded to the appropriate port.
    """

    def __init__(self, input, output):
        self.input = input
        self.output = output
        self.closed = False

        # Todo: what if they have different names?
        self.name = self.input.name

    def send(self, message):
        return self.output.send(message)

    def receive(self):
        return self.input.receive()

    def pending(self):
        return self.input.pending()

    def iter_pending(self):
        """Iterate through pending messages."""
        for message in self.input.iter_pending():
            yield message

    def close(self):
        if not self.closed:
            self.input.close()
            self.output.close()
            self.closed = True

    def __iter__(self):
        for message in self.input:
            yield message

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False

    def __repr__(self):
        if self.closed:
            state = 'closed'
        else:
            state = 'open'

        return "<{} I/O port '{}' ({})>".format(
            state, self.name, self.input.device.interface)
