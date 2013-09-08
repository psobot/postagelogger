postagelogger
=============

by Peter Sobot, September 7, 2013. Licensed under MIT.
Python logging handler that sends emails via [PostageApp](http://postageapp.com/).

##Usage

    import logging
    import postagelogger
    
    log = logging.getLogger(__name__)
    log.addHandler(postagelogger.PostageAppHandler(
      "my_postageapp_api_key", 'from@example.com', 'me@example.com'
    ))
    log.critical('Oh noes, a terrible error!')
    
    # Check your email!
