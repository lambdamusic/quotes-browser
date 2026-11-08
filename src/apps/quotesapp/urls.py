from django.conf.urls import url
from django.views.generic import RedirectView

from . import views


app_name = 'quotesapp'
urlpatterns = [
    url(r'^about/', views.about, name='about'),
    url(r'^tags/$', views.tags_all, name='tags'),

    ## ALL SOURCES
    url(r'^quotes/$', views.sources, name='sources'),
    ## RANDOM QUOTE (picked in the browser)
    url(r'^random/$', views.random_quote, name='random'),
    ##
    
    ## SOURCE PAGE
    url(r'^quotes/(?P<source_slug>[\w-]+)/$', views.source_detail, name='source'), 
    
    ## QUOTE DETAIL
    url(r'^quotes/(?P<source_slug>[\w-]+)/(?P<quoteindex>[\w-]+)/$', views.quote_detail, name='quotes'), 

    ## QUOTE PAGE ORIGINAL
    # url(r'^quotes/(?P<slug>[\w-]+)', views.quote_detail, name='quotes'), # 2024-03-14: had to remove suffix '/$'    

    url(r'^$', views.tags_all, name='home'),
]
