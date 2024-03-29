#!/usr/bin/env python3

import socket
import uuid

from .base import DaqController

from mnvruncontrol.backend.PostOffice.Routing import PostOffice
from mnvruncontrol.backend.PostOffice.Envelope import Message, Subscription


class MinervaController(DaqController):
    def __init__(self, config: dict):
        super().__init__(config)

        self.ident = uuid.uuid4()
        self.ip = socket.gethostbyname(socket.gethostname())

        port = config['minerva'].get('listen_port', 9998)
        self.postoffice = PostOffice(listen_port=port)

        server = (config['minerva'].get('remote_addr', 'localhost'),
                  config['minerva'].get('remote_port', 1090))

        for subject in ['mgr_directive', 'control_request']:
            sub = Subscription(subject=subject,
                               action=Subscription.FORWARD,
                               delivery_address=server)
            self.postoffice.AddSubscription(sub)

    def send(self, message: Message):
        return self.postoffice.SendAndWaitForResponse(message)

    def status(self):
        msg = Message(subject='mgr_directive',
                      directive='status_report',
                      client_id=self.ident)
        return self.send(msg)

    def update_control(self, control: bool):
        request = 'get' if control else 'release'
        msg = Message(subject='control_request',
                      request=request,
                      requester_id=self.ident,
                      requester_name='Bart',
                      requester_ip=self.ip,
                      requester_location='MINOS',
                      requester_phone='630-999-9999')
        return self.send(msg)

    def get_control(self):
        return self.update_control(True)

    def release_control(self):
        return self.update_control(False)

    def start_run(self):
        self.get_control()
        status = self.status()
        msg = Message(subject='mgr_directive',
                      directive='start',
                      client_id=self.ident,
                      configuration=status[0].status['configuration'])
        response = self.send(msg)
        self.release_control()
        return response

    def stop_run(self):
        self.get_control()
        msg = Message(subject='mgr_directive',
                      directive='stop',
                      client_id=self.ident)
        response = self.send(msg)
        self.release_control()
        return response
