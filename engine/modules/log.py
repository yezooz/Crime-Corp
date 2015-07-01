# -*- coding: utf-8 -*-
import logging.handlers

import datetime
import logging


class Log(object):
    def __init__(self, engine):
        self.engine = engine
        self.stat = None

    def message(self, message, is_error=False):
        self.engine.user.user.message_set.create(message="""%s""" % message)

    def add_log(self, log_type='', log_type_id=0, log='', ip=''):
        from django.db import connection

        try:
            sql = """
				INSERT INTO
					crims_archive.user_log
				VALUES (
					'%s', '%s', '%s', '%s', '%s', '%s'
				)
			""" % (str(self.engine.user.user.id), log_type, log_type_id, log, datetime.datetime.now(), str(ip))

            cursor = connection.cursor()
            cursor.execute(sql)
        except:
            logging.warning('Error inserting log to archive')

    def add_stat(self, key, value=1):
        if not self.stat:
            self.stat = UserDayStat.objects.get_by_user(user=self.engine.user.user)
        self.stat.add_stat(key, value)


class SMTPHandlerWithAuth(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            # import smtplib
            try:
                from email.Utils import formatdate
            except:
                formatdate = self.date_time
            # port = self.mailport
            # if not port:
            # 	port = smtplib.SMTP_PORT
            # smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                self.fromaddr,
                ",".join(self.toaddrs),
                self.getSubject(record),
                formatdate(), msg)

            # smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            # smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            # smtp.quit()

            from django.core.mail import send_mail

            send_mail(self.getSubject(record), msg, 'Crime Corp <robot@madfb.com>', self.toaddrs, fail_silently=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
