# import cPickle as pickle
from django.db import models
# from crims.userprofile.models import UserProfile

class GangManager(models.Manager):
    def get_by_name(self, name):
        return self.get(name__iexact=name)


class Gang(models.Model):
    name = models.CharField(max_length=15)
    member = models.TextField()
    invite_key = models.CharField(max_length=8)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GangManager()

    class Meta:
        db_table = 'gang'

    def __unicode__(self):
        return "Gang %s" % self.name

    def __getattr__(self, name):
        if name == 'members':
            return self.members.split(',')

    def add_member(self, name):
        members = self.members
        members.append(name)
        self.member = ','.join(members)
        self.save()

    def rem_member(self, name):
        members = self.members
        del members[members.index(name)]
        self.member = ','.join(members)
        self.save()
