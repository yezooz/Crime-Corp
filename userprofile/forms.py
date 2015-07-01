# -*- coding: utf-8 -*-
import re

from django.utils.translation import ugettext as _
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class ChangeEmailForm(forms.Form):
    user = None

    old_email = forms.EmailField()
    new_email_1 = forms.EmailField()
    new_email_2 = forms.EmailField()


class SetEmailForm(forms.Form):
    user = None

    new_email_1 = forms.EmailField()
    new_email_2 = forms.EmailField()


class ChangePassForm(forms.Form):
    user = None

    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_old_password(self):
        if self.user is None:
            raise forms.ValidationError(_('Unknown error'))

        if 'old_password' in self.cleaned_data and self.user.check_password(self.cleaned_data['old_password']):
            return self.cleaned_data['old_password']
        else:
            raise forms.ValidationError(_('Password is not correct'))

    def clean_new_password2(self):
        if 'new_password1' in self.cleaned_data and 'new_password2' in self.cleaned_data and self.cleaned_data[
            'new_password1'] == self.cleaned_data['new_password2']:
            return self.cleaned_data['new_password2']
        raise forms.ValidationError(_('You must type the same password each time'))


class SetPassForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_new_password2(self):
        if 'new_password1' in self.cleaned_data and 'new_password2' in self.cleaned_data and self.cleaned_data[
            'new_password1'] == self.cleaned_data['new_password2']:
            return self.cleaned_data['new_password2']
        raise forms.ValidationError(_('You must type the same password each time'))


class SetUsernameForm(forms.Form):
    username = forms.CharField(max_length=30, widget=forms.TextInput)

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        username_re = re.compile(r'^[A-Za-z]{1,}\w*$')

        if 'username' in self.cleaned_data:
            if not username_re.search(self.cleaned_data['username']):
                raise forms.ValidationError(
                    _('Usernames can only contain letters, numbers and underscores and cannot begin with number.'))
            if len(self.cleaned_data['username']) < 4:
                raise forms.ValidationError(_('Username can\'t be shorter than 4 characters.'))
            if len(self.cleaned_data['username']) > 20:
                raise forms.ValidationError(_('Username can\'t be longer than 20 characters.'))
            try:
                user = User.objects.get(username__exact=self.cleaned_data['username'])
            except User.DoesNotExist:
                return self.cleaned_data['username']
            raise forms.ValidationError(_('This username is already taken. Please choose another.'))


class ImForm(forms.Form):
    ims = (('msn', 'MSN'), ('gtalk', 'GTalk'), ('jabber', 'Jabber'), ('aim', 'AIM'), ('gg', 'Gadu-Gadu'))

    im1 = forms.CharField(required=False)
    im1_type = forms.ChoiceField(choices=ims)
    im2 = forms.CharField(required=False)
    im2_type = forms.ChoiceField(choices=ims)
    im3 = forms.CharField(required=False)
    im3_type = forms.ChoiceField(choices=ims)
    twitter = forms.CharField(required=False)
    mobile = forms.CharField(required=False)
