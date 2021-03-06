from urllib import parse as urlparse
from urllib.parse import urlencode
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
import re


class ImmoSource(models.Model):
    name = models.CharField(max_length=100)
    host_regex = models.CharField(
        max_length=100,
        help_text=(
            'The regex of the host who will be used to deduct '
            'the `ImmoSource` from the `Search.url`.'
        )
    )
    order_query_string = models.CharField(
        max_length=50,
        help_text=(
            'The query string to add to the `Search.url` '
            'to sort ascendingly the results by date.'
        )
    )

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return '{} (by {})'.format(self.name, self.user)


class Search(models.Model):
    url = models.URLField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    immo_source = models.ForeignKey(ImmoSource, on_delete=models.PROTECT)

    def order_url(self, immo_source=None):
        immo_source = immo_source or self.immo_source
        params = immo_source.order_query_string.split('=')
        url_parts = list(urlparse.urlparse(self.url))
        query_strings = dict(urlparse.parse_qsl(url_parts[4]))
        query_strings[params[0]] = params[1]
        url_parts[4] = urlencode(query_strings)
        self.url = urlparse.urlunparse(url_parts)

    def clean(self):
        immo_sources = ImmoSource.objects.all()
        for immo_src in immo_sources:
            match = re.match(immo_src.host_regex, self.url)
            if match:
                self.immo_source = immo_src
                self.order_url()
                return
        raise ValidationError(_('This website is not supported.'))

    def __str__(self):
        return '{}: {}'.format(self.immo_source, self.url)


class Feature(models.Model):
    label = models.CharField(max_length=100)
    key = models.SlugField(unique=True)

    def __str__(self):
        return self.label


class SearchResult(models.Model):
    search = models.ForeignKey(Search, on_delete=models.PROTECT)
    url = models.URLField(max_length=255)
    original_id = models.CharField(max_length=40)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=5000)
    price = models.FloatField()
    charges_included = models.BooleanField(default=True)
    publication_date = models.DateTimeField()
    real_estate_type = models.CharField(max_length=100, blank=True, null=True)
    rooms = models.IntegerField()
    furnished = models.NullBooleanField(blank=True, null=True)
    surface = models.FloatField()
    images = ArrayField(models.URLField(max_length=255), blank=True, null=True)
    zipcode = models.CharField(max_length=10)
    city = models.CharField(max_length=80)
    ges = models.CharField(max_length=1, blank=True, null=True)
    energy_rate = models.CharField(max_length=1, blank=True, null=True)
    alive = models.BooleanField(default=True)
    accepted = models.NullBooleanField(default=None)
    features = models.ManyToManyField(Feature, through='SearchResultFeature')

    class Meta:
        unique_together = ('search', 'original_id')

    def __str__(self):
        return self.title


class SearchResultFeature(models.Model):
    search_result = models.ForeignKey(SearchResult, on_delete=models.PROTECT)
    feature = models.ForeignKey(Feature, on_delete=models.PROTECT)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ('search_result', 'feature')

    def __str__(self):
        return '{}.{} = {}'.format(
            self.search_result, self.feature, self.value)
