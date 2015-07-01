# -*- coding: utf-8 -*-

from django import forms
# from django.forms import ModelForm
from django.contrib.auth.models import User
# from crims.job.models import Bounty
from crims.userprofile.models import UserProfile


class NewBountyForm(forms.Form):
    def __init__(self, data, user, *args, **kwargs):
        super(NewBountyForm, self).__init__(data=data, *args, **kwargs)
        self.user = user

    name = forms.CharField(max_length=100)
    credits = forms.CharField(max_length=4)

    def clean_name(self):
        if self.cleaned_data['name'] == str(self.user):
            raise forms.ValidationError(u'Really want to pay for your own head? I don\'t think so.')

        try:
            user = User.objects.get(username__iexact=self.cleaned_data['name'])
        except User.DoesNotExist:
            raise forms.ValidationError(u'Unknown user.')

        return self.cleaned_data['name']

    def clean_credits(self):
        try:
            if int(self.cleaned_data['credits']) <= 0:
                raise forms.ValidationError(u'No one will do it for free, smartass.')
        except ValueError:
            raise forms.ValidationError(u'Yeah, why don\'t you offer old shoe for this job?')

        profile = UserProfile.objects.get_by_id(self.user.id)
        if not profile.has_enough('credit', self.cleaned_data['credits']):
            # TODO: add-more-credits link
            raise forms.ValidationError(u'Not enough credits. You have %s credits. ADD_MORE' % user.credit)

        return self.cleaned_data['credits']
