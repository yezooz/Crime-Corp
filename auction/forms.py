# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django import forms


class SellForm(forms.Form):
    DURATION = (
        (1, "1 %s" % _('day'),),
        (2, "2 %s" % _('days'),),
        (3, "3 %s" % _('days'),),
        (4, "4 %s" % _('days'),),
        (5, "5 %s" % _('days'),),
        (6, "6 %s" % _('days'),),
        (7, "7 %s" % _('days'),),
    )

    # extra_title = forms.CharField(required=False, max_length=20)
    start_price = forms.IntegerField(min_value=1, max_value=99999999, widget=forms.TextInput(attrs={'size': '7'}))
    duration = forms.ChoiceField(choices=DURATION)
