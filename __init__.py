import json
import time
import atexit
import socket
import logging
import urllib2
import threading


class PostageAppHandler(logging.Handler):
    """
    A handler class which sends an email via PostageApp for each logging event.
    If timeout is specified, log messages will be batched together and
    sent every $n$ seconds in one email.
    """
    def __init__(self, api_key, fromaddr, recipients, timeout=None):
        """
        Initialize the handler.

        Initialize the instance with the from and to addresses and subject
        line of the email.
        """
        logging.Handler.__init__(self)

        self.api_key = api_key
        self.fromaddr = fromaddr
        if isinstance(recipients, basestring):
            recipients = [recipients]
        self.recipients = recipients

        self.records = []

        self.delay = timeout if timeout is None else float(timeout)
        if self.delay is not None:
            self.exit = False
            self.finished = False
            atexit.register(self.stop)

            self.thread = threading.Thread(target=self.run)
            self.thread.setDaemon(True)
            self.thread.start()

    def getSubject(self, record):
        """
        Determine the subject for the email.

        If you want to specify a subject line which is record-dependent,
        override this method.
        """
        return "%s event on %s" % (record.levelname, socket.gethostname())

    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        self.records.append(
            (self.getSubject(record), self.format(record), record.levelname)
        )
        if self.delay is None:
            self.send()

    def run(self):
        try:
            while not self.exit:
                self.send()
                if not self.exit:
                    time.sleep(self.delay)
        finally:
            self.finish()

    def send(self):
        if not self.records:
            return

        obj = {
            'api_key': self.api_key,
            'arguments': {
                'recipients': self.recipients,
                'headers': {
                    'from': self.fromaddr,
                },
                'content': {
                },
            }
        }

        if len(self.records) == 1:
            record = self.records.pop()
            (obj['arguments']['headers']['subject'],
             obj['arguments']['content']['text/plain'], _) = record
        else:
            if len(set([x[2] for x in self.records])) == 1:
                obj['arguments']['headers']['subject'] = (
                    "%d %s events on %s" % (
                        len(self.records),
                        self.records[0][2],
                        socket.gethostname(),
                    )
                    )
            else:
                obj['arguments']['headers']['subject'] = "%d events on %s" % (
                    len(self.records),
                    socket.gethostname(),
                )
            obj['arguments']['content']['text/plain'] = (
                ("\n" + ('-' * 80) + "\n").join(
                    [x[1] for x in self.records]
                )
            )
            self.records = []

        try:
            req = urllib2.Request(
                'http://api.postageapp.com/v.1.0/send_message.json',
                json.dumps(obj),
                {
                    'User-Agent': 'postageapp-logger',
                    'Content-Type': 'application/json'
                }
            )
            response = urllib2.urlopen(req)
            json_response = json.loads(response.read())
            if json_response['response']['status'] != 'ok':
                raise RuntimeError(
                    'Server returned %s' % json_response['response']['status']
                )
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def stop(self):
        self.exit = True
        self.finish()

    def finish(self):
        if not self.finished:
            self.send()
        else:
            raise RuntimeError("finish() already called on this logger!")
