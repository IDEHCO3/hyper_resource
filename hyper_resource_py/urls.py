from django.conf.urls import include, url
import sys

basic_path = 'ibge/bcim/'
host_name = sys.argv[-1]
protocol = 'http'
urlpatterns = [
    url(r'^'+ 'ibge/bcim/', include('bcim.urls', namespace='bcim_v1')),
    url(r'^controle_adesao-list/',include('controle_adesao.urls',namespace='controle_adesao')),
    url(r'^controle-list/',include('controle.urls',namespace='controle_v1')),


]
urlpatterns += [

    url(r'^api-auth/', include('rest_framework.urls',namespace='rest_framework')),

]


