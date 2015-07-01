from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

import datetime
import cPickle as pickle
from crims.userprofile.models import UserProfile


class PaymentManager(models.Manager):
    pass


class Payment(models.Model):
    user_id = models.IntegerField()
    site = models.CharField(max_length=10)
    provider = models.CharField(max_length=20)
    details = models.CharField(max_length=255)
    credits = models.PositiveIntegerField()
    total_credits = models.PositiveIntegerField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PaymentManager()

    class Meta:
        db_table = 'payment'
        verbose_name = 'Payment'

    def __unicode__(self):
        return 'UID:%s CREDITS:%s @ %s' % (str(self.user_id), str(self.credits), str(self.created_at))


class PaymentCountryManager(models.Manager):
    pass


class PaymentCountry(models.Model):
    country_id = models.IntegerField()
    # general
    is_srpoints = models.BooleanField(default=True)
    is_paypal = models.BooleanField(default=True)

    is_peanut = models.BooleanField(default=False)
    is_platnosci = models.BooleanField(default=False)

    # sms
    is_webtopay = models.BooleanField(default=False)
    is_furtumo = models.BooleanField(default=False)
    is_paymo = models.BooleanField(default=False)

    objects = PaymentCountryManager()

    class Meta:
        db_table = 'payment_country'
        verbose_name = 'Payment Country'
        verbose_name_plural = 'Payment Countries'

    def __unicode__(self):
        return 'Payments for country: %s' % self.country_id


class PaymentCodeManager(models.Manager):
    def check_code(self, code):
        try:
            return self.get(code=code)
        except PaymentCode.DoesNotExist:
            return None

    def gen_new_code(self, value=0):
        import hashlib

        sha = hashlib.sha1()
        sha.update(str(datetime.datetime.now()))
        sha_code = sha.hexdigest()

        start = 0
        while True:
            try:
                code = sha_code[start:start + 6]

                self.get(code=code)
                start += 1
                continue
            except PaymentCode.DoesNotExist:
                pc = PaymentCode()
                pc.code = code
                pc.value = value
                pc.save()

                return code


class PaymentCode(models.Model):
    code = models.CharField(max_length=6)
    value = models.CharField(max_length=100)

    used_by = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    codes = PaymentCodeManager()

    class Meta:
        db_table = 'payment_code'
        verbose_name = 'Payment Code'

    def __unicode__(self):
        return '%s @ %s' % (str(self.code), str(self.created_at))


class PaymentPromoCodeManager(models.Manager):
    def check_code(self, code):
        try:
            return self.get(code=code)
        except PaymentCode.DoesNotExist:
            return None


class PaymentPromoCode(models.Model):
    code = models.CharField(max_length=20)
    value = models.IntegerField()

    used_by = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(default=datetime.datetime.now())

    objects = PaymentPromoCodeManager()

    class Meta:
        db_table = 'payment_promo_code'
        verbose_name = 'Payment Promo Code'

    def __unicode__(self):
        return '%s @ %s' % (str(self.code), str(self.created_at))


class UserFBSpamManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_fb_spam_%s' % user.id
        elif user_id is not None:
            key = 'user_fb_spam_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)
            else:
                logging.warning('facebook_spam not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except UserFBSpam.DoesNotExist:
            fb = UserFBSpam()
            fb.user = user
            fb.save()
            item = fb

        cache.set(key, pickle.dumps(item))
        return item


class UserFBSpam(models.Model):
    user = models.ForeignKey(User)
    next_queue_at = models.DateTimeField(default=datetime.datetime.now())

    sent = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserFBSpamManager()

    class Meta:
        db_table = 'facebook_spam'
        verbose_name = 'Facebook Spam'

    def __unicode__(self):
        return '%s\' facebook spam' % self.user

    def save(self):
        super(UserFBSpam, self).save()  # Call the "real" save() method
        key = 'user_fb_spam_%s' % self.user.id
        cache.set(key, pickle.dumps(self))


class UserFBSpamLog(models.Model):
    user_id = models.IntegerField()
    type = models.CharField(max_length=25)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'facebook_spam_log'
        verbose_name = 'Facebook Spam Log'

    def __unicode__(self):
        return '%s: %s > %s' % (self.user_id, self.type, self.message)


class UserFBSpamQueue(models.Model):
    user_id = models.IntegerField()
    type = models.CharField(max_length=25)
    message = models.CharField(max_length=255)
    details = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expire_at = models.DateTimeField(default=datetime.datetime.now() + datetime.timedelta(days=3))

    class Meta:
        db_table = 'facebook_spam_queue'
        verbose_name = 'Facebook Spam Queue'

    def __unicode__(self):
        return '%s: %s > %s' % (self.user_id, self.type, self.message)


class NewsManager(models.Manager):
    def get_latest(self, lang='en', limit=3):
        key = 'news_%s' % lang

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.filter(lang=lang).order_by('-created_at')[:limit]
        except News.DoesNotExist:
            return None

        cache.set(key, pickle.dumps(item))
        return item


class News(models.Model):
    source = models.CharField(max_length=20)
    lang = models.CharField(max_length=2)

    title = models.CharField(max_length=100)
    content_short = models.CharField(max_length=255)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    objects = NewsManager()

    class Meta:
        db_table = 'news'
        verbose_name = 'News'

    def save(self):
        super(News, self).save()  # Call the "real" save() method
        cache.delete('news_%s' % self.lang)

    def __unicode__(self):
        return '%s @ %s' % (str(self.title), str(self.created_at))


class UserStreamManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        return self.filter(user=user)

    def get_latest(self, user=None, user_id=None):
        return self.get_by_user(user, user_id).order_by('-created_at')[:10]


class UserStream(models.Model):
    user = models.ForeignKey(User)

    source = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserStreamManager()

    class Meta:
        db_table = 'user_stream'
        verbose_name = 'User Stream'

    def save(self):
        super(UserStream, self).save()  # Call the "real" save() method
        cache.delete('user_stream_%s' % self.user.id)

    def __unicode__(self):
        return '%s: %s @ %s' % (str(self.user), str(self.title), str(self.created_at))

    def __getattr__(self, name):
        if name == 'title':
            return pickle.loads(self.title)
        elif name == 'content':
            return pickle.loads(self.content)
        else:
            return self.__getattribute__(name)


class UserActionManager(models.Manager):
    def get_latest_positive(self, user, limit=10):
        return self.filter(user=user, is_positive=True).order_by('-created_at')[:limit]

    def get_latest_negative(self, user, limit=10):
        return self.filter(user=user, is_positive=False).order_by('-created_at')[:limit]

    def get_latest(self, user, limit=10):
        return self.filter(user=user).order_by('-created_at')[:limit]


class UserAction(models.Model):
    user = models.ForeignKey(User, related_name='Base User')
    against = models.ForeignKey(User, related_name='Against User')

    is_positive = models.BooleanField(default=False)
    source = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserActionManager()

    class Meta:
        db_table = 'user_action'
        verbose_name = 'User Action'

    def save(self):
        super(UserStream, self).save()  # Call the "real" save() method
        cache.delete('user_stream_%s' % self.user.id)

    def __unicode__(self):
        return 'action of %s againts %s' % (self.user, self.against)


class UserRelationManager(models.Manager):
    def get_score(self, user, related):
        key = 'user_relation_%s_%s' % (user.id, related.id)

        try:
            return self.get(user=user, related=related).score
        except UserRelation.DoesNotExist:
            return settings.DEFAULT_RELATION_SCORE


class UserRelation(models.Model):
    user = models.ForeignKey(User, related_name='Related User')
    related = models.ForeignKey(User, related_name='Related to User')
    score = models.PositiveSmallIntegerField(default=settings.DEFAULT_RELATION_SCORE)  # 0-100

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserRelationManager()

    class Meta:
        db_table = 'user_relation'
        verbose_name = 'User Relation'

    def save(self):
        # security
        if self.score < 0: self.score = 0
        if self.score > 100: self.score = 100

        super(UserRelation, self).save()  # Call the "real" save() method
        cache.delete('user_relation_%s_%s' % (self.user.id, self.related.id))

    def __unicode__(self):
        return 'relation of %s with %s: %d' % (self.user, self.related, self.score)
