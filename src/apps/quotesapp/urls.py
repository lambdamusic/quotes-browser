from django.conf.urls import url
from django.views.generic import RedirectView

from . import views, views_seo


app_name = 'quotesapp'
urlpatterns = [
    url(r'^about/', views.about, name='about'),
    url(r'^tags/$', views.tags_all, name='tags'),
    ## TAG PAGE (was /tags/?tag=x until 2026-11; that URL now redirects here)
    ## .+ so tags with a slash work too (RDF/XML)
    url(r'^tags/(?P<tag>.+)/$', views.tag_detail, name='tag'),

    ## FOR SEARCH ENGINES, AND GITHUB PAGES' NOT-FOUND PAGE (fetched explicitly by site-dump)
    url(r'^robots\.txt$', views_seo.robots_txt, name='robots'),
    url(r'^sitemap\.xml$', views_seo.sitemap_xml, name='sitemap'),
    url(r'^404\.html$', views.not_found, name='not_found'),

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
