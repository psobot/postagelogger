import json
import socket
import logging
import urllib2


class PostageAppHandler(logging.Handler):
    """
    A handler class which sends an email via PostageApp for each logging event.
    """
    def __init__(self, api_key, fromaddr, recipients):
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
        url = 'http://api.postageapp.com/v.1.0/send_message.json'
        json_string = json.dumps({
            'api_key': self.api_key,
            'arguments': {
                'recipients': self.recipients,
                'headers': {
                    'from': self.fromaddr,
                    'subject': self.getSubject(record),
                },
                'content': {
                    'text/plain': self.format(record)
                },
            }
        })
        
        try:
            req = urllib2.Request(
                url,
                json_string,
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
