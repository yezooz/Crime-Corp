import os

from django.conf import settings

import datetime
import logging


# logs directory setup
if settings.LOCAL:
    logs_dir = '/Users/marekmikuliszyn/Sites/crims/logs/'
else:
    logs_dir = '/home/marek/crims/logs/'

today_cat = datetime.datetime.now().strftime("%Y-%m-%d")
try:
    os.stat(logs_dir + str(today_cat))
except OSError:
    os.mkdir(logs_dir + str(today_cat), 0777)


def create_logger(name=None):
    if name is None:
        logger = logging.getLogger('')
        name = 'crims'
    else:
        logger = logging.getLogger(name)

    hdlr = logging.FileHandler(logs_dir + str(today_cat) + "/%s.log" % (name))
    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',)
    formatter = logging.Formatter('%(asctime)-11s | %(levelname)-6s | %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return logger


def set_email_logger(logger, subject="Log message"):
    import crims.engine.modules.log as log

    rootLogger = create_logger(logger)
    smtpHandler = log.SMTPHandlerWithAuth(('crimecorp.com', 25), 'crimecorp@crimecorp.com', 'crimecorp@crimecorp.com',
                                          subject)
    rootLogger.addHandler(smtpHandler)
    return rootLogger


debug_logger = create_logger('debug')
info_logger = create_logger('info')
warning_logger = create_logger('warning')
error_logger = set_email_logger('error', "Error message from Crime Corp")
critical_logger = set_email_logger('critical', "CRITICAL message from Crime Corp")


def debug(msg):
    debug_logger.debug(msg)


def info(msg):
    info_logger.info(msg)


def warning(msg):
    warning_logger.warning(msg)


def error(msg):
    error_logger.error(msg)


def critical(msg):
    critical_logger.critical(msg)
